#!/usr/bin/env python3.13

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

import subprocess
from pathlib import Path

def main():
    root = Path('/workspace')
    excluded_globs = [
        '/workspace/.cache/Microsoft/**/*',
        '/workspace/.cache/huggingface/hub/**/*',
        '/workspace/.cache/huggingface/xet/**/*',
        '/workspace/.cache/pip/**/*',
        '/workspace/.cache/rclone/**/*',
        '/workspace/ComfyUI/custom_nodes/comfyui-manager',
        '/workspace/ComfyUI/models/**/*',
        '/workspace/scripts',
        '/workspace/ollama',
        '/workspace/vllm',
        '**/__pycache__',
        '**/nohup.out',
    ]

    backup_paths = []

    for path in root.glob('*'):
        if any(path.full_match(excl) for excl in excluded_globs):
            continue

        if (path/'.git').is_dir():
            # Git repo
            git_output = subprocess.run(['git', 'status', '--ignored', '--porcelain', '-z'],
                                        cwd=path, check=True, stdout=subprocess.PIPE)
            for line in git_output.stdout.decode('utf-8', errors='ignore').split('\0'):
                if len(line) == 0:
                    continue
                xy = line[:2]
                assert line[2] == ' '
                fn = line.rstrip()[3:]
                full_path = path/fn

                if any(full_path.full_match(excl) for excl in excluded_globs):
                    continue

                if full_path.is_dir():
                    for subpath in full_path.glob('**/*'):
                        if not subpath.is_dir():
                            backup_paths.append(subpath)
                else:
                    backup_paths.append(full_path)

            continue

        # Regular dir
        if path.is_dir():
            for subpath in path.glob('**/*'):
                if not subpath.is_dir() and not any(subpath.full_match(excl) for excl in excluded_globs):
                    backup_paths.append(subpath)
        else:
            backup_paths.append(path)

    for path in sorted(backup_paths):
        print(path)

if __name__ == "__main__":
    main()
