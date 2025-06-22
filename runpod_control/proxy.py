#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

"""Automatically start and stop RunPod pods based on web activity, reverse proxy traffic to
apps on RunPod pods."""

import os
import pprint
import logging
import contextlib
import asyncio
import subprocess
import argparse
import socket
import json
from datetime import datetime
from time import time
from types import SimpleNamespace
from pathlib import Path

import jinja2
import aiohttp
from aiohttp import web
import aiohttp_jinja2

import runpod

from config import get_config, setup_runpod
from create import create_pod
from resume import resume_pod
from update_ssh_config import get_ssh_ip_port, update_ssh_config
from destroy import terminate_pod

logger = logging.getLogger(__name__)
script_dir = Path(__file__).parent

async def handle_websocket_proxy(ws_client, ws_backend_server, state):
    """
    Forward WebSocket messages between client and backend server.

    Args:
        ws_client: WebSocket connection to the client
        ws_backend_server: WebSocket connection to the backend server
        state: State object to track activity
    """
    async def forward_messages(ws_from, ws_to, direction):
        try:
            async for msg in ws_from:
                state.last_web_activity = time()
                payload = f' ({msg.data})' if msg.type == aiohttp.WSMsgType.TEXT else ''
                logger.debug(f'Forwarding {direction}: {msg.type.name}{payload}')

                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_to.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    await ws_to.send_bytes(msg.data)
                elif msg.type == aiohttp.WSMsgType.PING:
                    await ws_to.ping()
                elif msg.type == aiohttp.WSMsgType.PONG:
                    await ws_to.pong()
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    if not ws_to.closed:
                        await ws_to.close(code=msg.data, message=msg.extra)
                    return  # Exit the loop when close is received
                else:
                    logger.warning(f'Unknown message type: {msg.type}')

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error(f'Error forwarding {direction} messages: {e}')
        finally:
            try:
                if not ws_to.closed:
                    await ws_to.close()
            except asyncio.CancelledError:
                logger.debug('WebSocket cancelled')

    # Create tasks for bidirectional forwarding
    client_to_server = asyncio.create_task(
        forward_messages(ws_client, ws_backend_server, "client->server")
    )
    server_to_client = asyncio.create_task(
        forward_messages(ws_backend_server, ws_client, "server->client")
    )

    # Wait for either direction to complete
    _, pending = await asyncio.wait(
        [client_to_server, server_to_client],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Cancel remaining tasks
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

async def handle_http_proxy(request, client_session, backend_url):
    """
    Forward HTTP requests to the backend server and return the response.

    Args:
        request: The incoming HTTP request
        client_session: aiohttp ClientSession for making backend requests
        backend_url: URL of the backend server to forward requests to

    Returns:
        web.Response: The response from the backend server
    """
    drop_headers = ('Content-Encoding', 'Content-Length', 'Connection', 'Upgrade', 'Transfer-Encoding')

    headers = {k: v for k, v in request.headers.items() if k not in drop_headers}
    data = await request.content.read()

    try:
        async with client_session.request(
            request.method,
            backend_url,
            headers=headers,
            data=data
        ) as backend_response:

            headers = {k: v for k, v in backend_response.headers.items() if k not in drop_headers}
            body = await backend_response.content.read()

            # Create client response with backend's data
            return web.Response(
                status=backend_response.status,
                headers=headers,
                body=body,
            )
    except (ConnectionResetError, ConnectionError, aiohttp.ClientError) as ex:
        logger.error(f'Connection error: {ex}')
        return web.Response(status=502, text='Bad Gateway - Connection error')

async def handle_proxy_request(request):
    """
    Main request handler that routes requests to either WebSocket or HTTP proxy.

    Args:
        request: The incoming request

    Returns:
        web.Response or WebSocketResponse: Appropriate response based on request type
    """
    # ComfyUI checks these after the websocket reconnects
    dont_wake_paths = ('/api/queue', '/api/history')

    conn = request.headers.get('connection', '').lower()
    upgrade = request.headers.get('upgrade', '').lower()

    is_web_socket = 'upgrade' in conn and upgrade == 'websocket' and request.method == 'GET'

    start_pod = not any(request.raw_path.startswith(path) for path in dont_wake_paths)
    if not is_web_socket and start_pod:
        # Don't start the pod for websocket connections - only for regular HTTP requests
        if not request.app['state'].need_pod:
            logger.info(f"{request.app['name']} web activity detected, starting pod")
        request.app['state'].last_web_activity = time()
        request.app['state'].need_pod = True
        logger.debug(f'Web activity: {request.raw_path}')

    if not request.app['global_state'].ssh.ssh_running:
        # Show starting page while pod is starting up
        context = {
            'name': request.app['name'],
        }
        response = aiohttp_jinja2.render_template("starting.html", request,
                                        context=context)
        return response

    # Pod and SSH are up - forward request to backend server
    remote_port = request.app['port_cfg']['remote_port']
    backend_url = f"http://127.0.0.1:{remote_port}{request.raw_path}"

    client_session = request.app['client_session']

    if is_web_socket:
        ws_client = web.WebSocketResponse()
        await ws_client.prepare(request)
        logger.info(f'Client WebSocket connection established to {pprint.pformat(ws_client)}')

        try:
            async with client_session.ws_connect(backend_url, headers={'cookie': request.headers.get('cookie', '')}) as ws_backend_server:
                logger.info('Upstream WebSocket connection established')

                await handle_websocket_proxy(ws_client, ws_backend_server, request.app['state'])

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error(f'Failed to connect to upstream server: {e}')
            await ws_client.close()

        return ws_client

    else:
        return await handle_http_proxy(request, client_session, backend_url)

def is_pod_running(name):
    """
    Check if RunPod pod for this application is currently running.

    Returns:
        bool: True if at least one pod is running, False otherwise
    """
    pod_list = runpod.get_pods()
    pod_list = [pod for pod in pod_list if pod['name'] == name]
    if len(pod_list) == 0:
        return False
    if pod_list[0]['desiredStatus'] != 'RUNNING':
        return False
    return True

async def status_reporter(global_state):
    """
    Periodically report the status of pod and SSH connections.

    Args:
        global_state: Global application state containing pod and SSH status
    """
    last_report_time = 0
    last_pod_running = None
    last_ssh_running = None
    max_report_interval = 60

    while True:
        do_report = False
        state_change = False

        if time() - last_report_time > max_report_interval:
            do_report = True

        if last_pod_running != global_state.pod.pod_running:
            do_report = True
            state_change = True

        if last_ssh_running != global_state.ssh.ssh_running:
            do_report = True
            state_change = True

        if do_report:
            log_func = logger.info if global_state.pod.pod_running or state_change else logger.debug
            last_web_activity = max([proxy.last_web_activity for proxy in global_state.proxies])
            last_web_activity = f'{(time()-last_web_activity)/60:.1f} minutes ago' if last_web_activity else 'never'
            last_cpu_gpu_activity = f'{(time()-global_state.ssh.last_activity)/60:.1f} minutes ago' if global_state.ssh.last_activity else 'never'
            log_func(f"pod_running={global_state.pod.pod_running}, "
                        f"ssh_running={global_state.ssh.ssh_running}, "
                        f"last_web_activity={last_web_activity}, "
                        f"cpu_util={global_state.ssh.cpu_util:.0f}%, "
                        f"gpu_util={global_state.ssh.gpu_util:.0f}%, "
                        f"cpu_mem={global_state.ssh.cpu_mem_gb:.1f}GB, "
                        f"gpu_mem={global_state.ssh.gpu_mem_gb:.1f}GB, "
                        f"last_cpu_gpu_activity={last_cpu_gpu_activity}")

            last_report_time = time()
            last_pod_running = global_state.pod.pod_running
            last_ssh_running = global_state.ssh.ssh_running

        await asyncio.sleep(1)

def create_or_resume_pod(name):
    """
    Resume an existing pod if it exists or create a new pod.
    """
    pod_list = runpod.get_pods()
    pod_list = [pod for pod in pod_list if pod['name'] == name]

    if len(pod_list) == 0:
        create_pod()
    else:
        resume_pod()

async def monitor_pod(pod_state, proxies_state, ssh_state, config):
    """
    Monitor pod status and automatically start/stop pods based on demand.

    Args:
        pod_state: State object tracking pod status
        proxies_state: List of proxy states to check for pod demand
        config: Application configuration
    """
    last_pod_running_check = 0
    startup_wait_time = config['web']['startup_wait_time']
    check_pod_interval = config['web']['check_pod_interval']
    periodic_tasks = config['periodic_tasks']
    for task_name, task in periodic_tasks.items():
        task['last_run'] = 0

    while True:
        try:
            if time() - last_pod_running_check > check_pod_interval:
                pod_state.pod_running = is_pod_running(config['runpod']['pod']['name'])
                last_pod_running_check = time()

            pod_state.need_ssh = pod_state.pod_running

            need_pod = any(proxy.need_pod for proxy in proxies_state) or ssh_state.need_pod
            if need_pod and not pod_state.pod_running:
                logger.info("Pod is not running, starting pod...")
                create_or_resume_pod(config['runpod']['pod']['name'])
                pod_state.pod_running = True
                pod_state.pod_start_time = time()
                # Give it a little time to start
                await asyncio.sleep(startup_wait_time)
                pod_state.need_ssh = True

            if pod_state.pod_running:
                # Check if any periodic tasks need to run
                for task_name, task in periodic_tasks.items():
                    if time() - task['last_run'] >= task['interval']:
                        logger.debug(f'Running periodic task "{task_name}": {task["command"]}')
                        cp = subprocess.run(task['command'],
                                            shell=True, check=False,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if cp.returncode != 0:
                            for line in cp.stdout.decode('utf-8', errors='ignore').splitlines():
                                logger.error(f'{task_name}: {line}')
                            logger.error(f'Periodic task "{task_name}" failed with code {cp.returncode}')
                        else:
                            logger.debug(f'Periodic task "{task_name}" completed successfully')
                        task['last_run'] = time()

            if pod_state.pod_running and not need_pod:
                logger.info("Destroying pod...")
                terminate_pod()
                pod_state.pod_running = False
                pod_state.pod_start_time = 0
                pod_state.need_ssh = False

            await asyncio.sleep(10)

        except Exception as ex: # pylint: disable=broad-exception-caught
            logger.error(f"Error in pod monitoring: {ex}")
            pod_state.pod_running = False
            pod_state.need_ssh = False
            await asyncio.sleep(30)

async def handle_ssh_output(proc, ssh_state, ssh_config):
    """
    Handle the utilization metrics from status_loop.py on the pod.
    """
    last_was_active = None
    while True:
        line = await proc.stdout.readline()
        if not line:
            break  # EOF
        line = line.decode('utf-8', errors='ignore').strip()
        logger.debug(f"SSH output: {line}")
        try:
            data = json.loads(line)
        except json.JSONDecodeError as ex:
            logging.error(f"{ex}: Failed to decode JSON from SSH output: {line}")
            continue

        for key, value in data.items():
            setattr(ssh_state, key, value)

        is_active = ssh_state.cpu_util >= ssh_config['cpu_util_threshold'] or ssh_state.gpu_util >= ssh_config['gpu_util_threshold']
        if is_active != last_was_active:
            logger.info(f"CPU/GPU status changed to: {'active' if is_active else 'idle'}")
            last_was_active = is_active
        if is_active:
            if not ssh_state.need_pod:
                logger.info(f"CPU usage: {ssh_state.cpu_util:.0f}%, GPU usage: {ssh_state.gpu_util:.0f}% - setting need_pod to True")
                ssh_state.need_pod = True
            ssh_state.last_activity = time()

        idle_time = time() - ssh_state.last_activity
        if idle_time > ssh_config['shutdown_timeout'] and ssh_state.need_pod:
            logger.info(f"CPU and GPU have been idle for {idle_time:.0f} seconds, setting need_pod to False")
            ssh_state.need_pod = False

async def monitor_ssh(ssh_state, pod_state, config):
    """
    Monitor and maintain SSH port forwarding connections to pod.

    Args:
        ssh_state: State object tracking SSH connection status
        pod_state: State object tracking pod status
        config: Application configuration containing port forwarding settings
    """
    while True:
        try:
            if pod_state.need_ssh:
                ssh_state.ssh_ip, ssh_state.ssh_port = get_ssh_ip_port()
                if ssh_state.ssh_ip is None or ssh_state.ssh_port is None:
                    logger.error("SSH IP or port not found, retrying...")
                    await asyncio.sleep(30)
                    continue

                logger.debug(f"Seconds since pod start: {time()-pod_state.pod_start_time:.0f}")
                logger.info(f"Establishing SSH connection to pod at {ssh_state.ssh_ip}:{ssh_state.ssh_port}...")
                ssh_state.ssh_running = True

                port_forward_args = []
                for _, port_cfg in config['web']['proxies'].items():
                    remote_port = port_cfg['remote_port']
                    if remote_port:
                        port_forward_args += ['-L', f'{remote_port}:127.0.0.1:{remote_port}']

                cmd = [
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'ServerAliveInterval=60',
                    '-o', 'ServerAliveCountMax=3',
                    '-o', 'ConnectTimeout=10'
                ] + port_forward_args + [
                    '-p', str(ssh_state.ssh_port),
                    f'root@{ssh_state.ssh_ip}',
                    config['ssh']['status_command']
                ]
                logger.info(f"Running command: {' '.join(cmd)}")
                proc = await asyncio.create_subprocess_exec(*cmd, preexec_fn=os.setpgrp,
                                                            stdout=asyncio.subprocess.PIPE,
                                                            stderr=asyncio.subprocess.STDOUT)

                await handle_ssh_output(proc, ssh_state, config['ssh'])
                await proc.wait()
                ssh_state.ssh_running = False
                logger.info("SSH connection closed.")
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(30)
        except Exception as ex: # pylint: disable=broad-exception-caught
            logger.error(f"Error in SSH monitoring: {ex}")
            ssh_state.ssh_running = False
            await asyncio.sleep(30)

async def update_ssh_config_task(ssh_state):
    """
    Task to automatically update SSH configuration when SSH connection status changes.

    Args:
        ssh_state: State object tracking SSH connection status
    """
    last_ssh_running = False
    while True:
        try:
            if not last_ssh_running and ssh_state.ssh_running:
                await update_ssh_config(wait=True, replace=True, prompt_replace=False)
                last_ssh_running = True

            if last_ssh_running and not ssh_state.ssh_running:
                last_ssh_running = False

        except Exception as ex: # pylint: disable=broad-exception-caught
            logger.error(f"Error in SSH config update: {ex}")

        await asyncio.sleep(5)

def immediate_shutdown(global_state):
    """
    Immediately mark all proxies as idle so pod is terminated immediately.
    Args:
        global_state: Global application state containing proxy states
    """
    for proxy_state in global_state.proxies:
        proxy_state.last_web_activity = 0

async def proxy_idle_detection(app: web.Application):
    """
    Monitor proxy activity and mark pods as not needed after idle timeout.

    Args:
        app: The web application instance containing state and configuration
    """
    shutdown_timeout = app['config']['web']['shutdown_timeout']
    while True:
        try:
            if app['state'].need_pod and time() - app['state'].last_web_activity > shutdown_timeout:
                if app['state'].last_web_activity:
                    logger.info(f"No {app['state'].name} web activity for {app['config']['web']['shutdown_timeout']//60} minutes, setting need_pod to False...")
                else:
                    logger.info(f"Immediate shutdown requested, setting need_pod to False for {app['state'].name}...")
                app['state'].need_pod = False

            if app['state'].scheduled_shutdown and time() >= app['state'].scheduled_shutdown:
                logger.info("Scheduled shutdown time reached, shutting down immediately...")
                immediate_shutdown(app['global_state'])
                app['state'].scheduled_shutdown = None

        except Exception as ex: # pylint: disable=broad-exception-caught
            logger.error(f"Error in proxy idle detection: {ex}")

        await asyncio.sleep(10)

async def background_tasks(app: web.Application):
    """
    Context manager to start and clean up background tasks for the application.

    Args:
        app: The web application instance

    Yields:
        None: Control to the application while tasks run
    """
    for name, key in app['state'].app_keys.items():
        coro = {
            'proxy_idle_detection': proxy_idle_detection,
        }[name]
        app[key] = asyncio.create_task(coro(app))

    yield

    for _, key in app['state'].app_keys.items():
        app[key].cancel()

    with contextlib.suppress(asyncio.CancelledError):
        for _, key in app['state'].app_keys.items():
            await app[key]

async def handle_schedule_shutdown(request):
    """API endpoint to schedule shutdown"""
    data = await request.json()
    shutdown_in_minutes = data.get('shutdown_in_minutes', None)
    if shutdown_in_minutes is None or shutdown_in_minutes <= 0:
        return web.json_response({'error': 'Invalid shutdown time'}, status=400)

    proxy_state = request.app['state']
    proxy_state.scheduled_shutdown = time() + (shutdown_in_minutes * 60)

    logger.info(f"Shutdown scheduled in {shutdown_in_minutes} minutes")
    return web.json_response({'status': 'success'})

async def handle_cancel_shutdown(request):
    """API endpoint to cancel scheduled shutdown"""
    proxy_state = request.app['state']
    proxy_state.scheduled_shutdown = None

    logger.info("Scheduled shutdown cancelled")
    return web.json_response({'status': 'success'})

async def handle_immediate_shutdown(request):
    """API endpoint for immediate shutdown"""
    logger.info("Immediate shutdown requested")
    immediate_shutdown(request.app['global_state'])
    return web.json_response({'status': 'success'})

def format_timestamp(timestamp):
    """
    Format a unix timestamp into a human-readable string.
    """
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y %H:%M:%S')
    return None

def format_duration(raw_seconds):
    """
    Format a duration in seconds into HH:MM:SS format.
    """
    hours, remainder = divmod(raw_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

async def handle_status(request):
    """
    Serve the status page with current pod and SSH information.
    """
    global_state = request.app['global_state']

    # Calculate uptime if pod is running
    pod_uptime = None
    if global_state.pod.pod_running:
        pod_uptime = format_duration(time() - global_state.pod.pod_start_time)

    proxies = []
    for proxy_state in global_state.proxies:
        # Calculate time since last activity
        last_web_activity = None
        if proxy_state.last_web_activity:
            minutes_ago = (time() - proxy_state.last_web_activity) / 60
            last_web_activity = f"{minutes_ago:.1f} minutes ago"

        proxies.append({
            'name': proxy_state.name,
            'active': global_state.ssh.ssh_running, # TODO
            'last_activity_time': last_web_activity,
            'local_port': proxy_state.local_port,
            'remote_port': proxy_state.remote_port,
        })

    context = {
        'pod_running': global_state.pod.pod_running,
        'pod_start_time': format_timestamp(global_state.pod.pod_start_time),
        'pod_uptime': pod_uptime,
        'ssh_running': global_state.ssh.ssh_running,
        'ssh_ip': global_state.ssh.ssh_ip,
        'ssh_port': global_state.ssh.ssh_port,
        'scheduled_shutdown_time': format_timestamp(request.app['state'].scheduled_shutdown) if request.app['state'].scheduled_shutdown else None,
        'shutdown_countdown': format_duration(request.app['state'].scheduled_shutdown - time()) if request.app['state'].scheduled_shutdown else None,
        'proxies': proxies,
        'current_time': format_timestamp(time())
    }

    return aiohttp_jinja2.render_template('status.html', request, context)

async def create_app(name, port_cfg, global_state, proxy_state, config):
    """
    Create and configure the aiohttp web application.

    Args:
        port_cfg: Port configuration for this proxy instance
        global_state: Global application state
        proxy_state: State specific to this proxy instance

    Returns:
        web.Application: Configured web application
    """
    app = web.Application()

    app['name'] = name
    app['config'] = config
    app['port_cfg'] = port_cfg
    app['global_state'] = global_state
    app['state'] = proxy_state
    app['client_session'] = aiohttp.ClientSession()

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(script_dir / 'templates'))

    async def cleanup_session(app):
        # Clean up client_session on app shutdown
        await app['client_session'].close()
    app.on_cleanup.append(cleanup_session)

    if app['port_cfg']['remote_port']:
        app.router.add_route('*', '/{path:.*}', handle_proxy_request)
    else:
        app.router.add_get('/', lambda request: web.HTTPFound('/status'))
        app.router.add_get('/status', handle_status)
        app.router.add_post('/api/schedule-shutdown', handle_schedule_shutdown)
        app.router.add_post('/api/cancel-shutdown', handle_cancel_shutdown)
        app.router.add_post('/api/immediate-shutdown', handle_immediate_shutdown)

    for name in ('proxy_idle_detection',):
        app['state'].app_keys[name] = web.AppKey(name, asyncio.Task[None])

    app.cleanup_ctx.append(background_tasks)

    return app

runners = []
async def start_site(name, port_cfg, global_state, proxy_state, config):
    """
    Start a web server site for a specific port configuration.

    Args:
        port_cfg: Port configuration specifying local port to listen on
        global_state: Global application state
        proxy_state: State specific to this proxy instance
    """
    listen_address = port_cfg['local_bind_address']
    listen_port = port_cfg['local_port']
    url_address = socket.gethostname() if listen_address == '0.0.0.0' else listen_address
    app = await create_app(name, port_cfg, global_state, proxy_state, config)
    runner = web.AppRunner(app)
    runners.append(runner)
    await runner.setup()
    site = web.TCPSite(runner, listen_address, listen_port)
    logger.info(f"{name} at http://{url_address}:{listen_port}/")
    await site.start()

def main():
    """
    Main entry point that sets up logging, creates global state, and starts all services.

    Initializes the event loop, creates proxy servers for each configured port,
    and starts monitoring tasks for pods and SSH connections.
    """
    parser = argparse.ArgumentParser(description='Automatic RunPod start/stop and reverse proxy service')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    debug = args.debug
    setup_runpod()
    config = get_config()

    if debug:
        log_level = logging.DEBUG
        http_log_level = logging.DEBUG
    else:
        log_level = logging.INFO
        http_log_level = logging.WARNING
    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)
    logging.getLogger('aiohttp.access').setLevel(http_log_level)

    loop = asyncio.get_event_loop()

    initial_pod_running = is_pod_running(config['runpod']['pod']['name'])

    global_state = SimpleNamespace(
        pod=SimpleNamespace(
            pod_running=initial_pod_running,
            pod_start_time=time() if initial_pod_running else 0,
            need_ssh=initial_pod_running,
        ),

        ssh=SimpleNamespace(
            ssh_running=False,
            cpu_util=0, gpu_util=0, cpu_mem_gb=0, gpu_mem_gb=0,
            last_activity=0, need_pod=False,
            ssh_ip=None, ssh_port=None,
        ),

        proxies=[]
    )

    for port_name, port_cfg in config['web']['proxies'].items():
        # Keep the pod running if it was running at startup
        proxy_state = SimpleNamespace(
            need_pod=initial_pod_running,
            last_web_activity=time() if initial_pod_running else 0,
            scheduled_shutdown=None,
            app_keys={},
            name=port_name, local_port=port_cfg['local_port'],
            remote_port=port_cfg['remote_port'],
        )
        global_state.proxies.append(proxy_state)

        loop.create_task(start_site(name=port_name, port_cfg=port_cfg, global_state=global_state,
                                    proxy_state=proxy_state, config=config))

    loop.create_task(monitor_pod(global_state.pod, global_state.proxies, global_state.ssh, config))
    loop.create_task(monitor_ssh(global_state.ssh, global_state.pod, config))
    loop.create_task(status_reporter(global_state))
    if config['ssh']['update_ssh_config']:
        loop.create_task(update_ssh_config_task(global_state.ssh))

    try:
        loop.run_forever()
    except Exception as ex: # pylint: disable=broad-exception-caught
        logger.error(f"Exception in main(): {ex}")
    finally:
        for runner in runners:
            loop.run_until_complete(runner.cleanup())

if __name__ == '__main__':
    main()
