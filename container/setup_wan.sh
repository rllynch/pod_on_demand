#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2025 Richard L. Lynch <rich@richlynch.com>
# SPDX-License-Identifier: MIT

set -eu
#set -x

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${script_dir}/common.sh"

########################################################################################
# WAN 2.1 models
# https://comfyanonymous.github.io/ComfyUI_examples/wan/
########################################################################################

cd $script_dir

# Common
download_hf_model text_encoders/        Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
download_hf_model vae/                  Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/vae/wan_2.1_vae.safetensors

# Text to Video
download_hf_model diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors # 2.7GB
download_hf_model diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_t2v_14B_fp16.safetensors # 27GB

# VACE Reference Image to Video
# (output does not contain reference image)
download_hf_model diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors # 4GB
download_hf_model diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors # 32GB

# Image to Video
download_hf_model diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors
download_hf_model clip_vision/          Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/clip_vision/clip_vision_h.safetensors
