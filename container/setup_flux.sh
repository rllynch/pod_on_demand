#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# Flux models
########################################################################################

cd $script_dir

# flux-dev
# https://comfyanonymous.github.io/ComfyUI_examples/flux/
download_hf_model text_encoders/        comfyanonymous/flux_text_encoders       t5xxl_fp16.safetensors
download_hf_model text_encoders/        comfyanonymous/flux_text_encoders       clip_l.safetensors
download_hf_model diffusion_models/     black-forest-labs/FLUX.1-dev            flux1-dev.safetensors # 23GB
download_hf_model vae/                  Comfy-Org/Lumina_Image_2.0_Repackaged   split_files/vae/ae.safetensors

# Flux fill (inpainting) model
download_hf_model diffusion_models/     black-forest-labs/FLUX.1-Fill-dev       flux1-fill-dev.safetensors
