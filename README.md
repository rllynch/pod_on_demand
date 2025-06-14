# Overview

This repository contains a set of scripts to:
* Install ComfyUI, related models, and related tools on a Runpod pod
* Provide a reverse proxy to services on the pod, automatically starting the pod when ComfyUI
is accessed and terminating the pod when idle to save costs.

# Initial setup

* [Create a runpod API key](https://www.runpod.io/console/user/settings) on Runpod. This key will
be used by the scripts to manage the Runpod pods.
* [Create a network volume](https://www.runpod.io/console/user/storage/create) on Runpod. Note down
the volume ID from the [Storage page](https://www.runpod.io/console/user/storage). About 200GB is
required for the default configuration.
* [Create a Huggingface read only token](https://huggingface.co/settings/tokens/new?tokenType=read)
to be used by the scripts to download models from Huggingface.
* Local machine
    * Clone this repository to your local machine.
    * In the runpod_control subdirectory
        * Copy secrets.template.yaml to secrets.yaml and fill in the Runpod API key and volume ID.
        * Customize config.yaml as desired.
    * Create and activate a virtual environment then install the required Python packages from requirements.txt.
    * Run the create.py script to create the Runpod pod.
    * Go to the [Runpod Pods](https://www.runpod.io/console/deploy) page and confirm the pod is running.
    * Example:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ./create.py
    ```

* Runpod pod
    * SSH into the container then clone this repository into the container's /workspace/scripts directory.
    * Run the container/setup.sh script to set up the container environment and wait for it to
    complete. This will install ComfyUI, related tools, and models to the persistent network volume.
    * Example:
    ```bash
    git clone https://github.com/rllynch/pod_on_demand.git /workspace/scripts
    cd /workspace/scripts/container
    ./setup.sh
    # You will be prompted to enter your Huggingface read-only token.
    ```

* Local machine
    * Run destroy.py to stop and delete the pod created earlier.
    * Run the proxy.py script to start the local proxy server.
    * Connect to http://localhost:8000 to access the status page
    * Connect to http://localhost:8001 to access ComfyUI. A pod will be started automatically
    and the ComfyUI web interface should appear in a couple minutes.
    * Example:

    ```bash
    ./destroy.py
    ./proxy.py
    # (Connect to http://localhost:8000 or http://localhost:8001)
    ```
