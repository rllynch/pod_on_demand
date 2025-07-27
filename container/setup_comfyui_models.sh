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
download_hf_model flux_common      text_encoders/        comfyanonymous/flux_text_encoders       t5xxl_fp16.safetensors
download_hf_model flux_common      text_encoders/        comfyanonymous/flux_text_encoders       clip_l.safetensors
download_hf_model flux_common      diffusion_models/     black-forest-labs/FLUX.1-dev            flux1-dev.safetensors # 23GB
download_hf_model flux_common      vae/                  Comfy-Org/Lumina_Image_2.0_Repackaged   split_files/vae/ae.safetensors

# Flux fill (inpainting) model
download_hf_model flux_inpainting  diffusion_models/     black-forest-labs/FLUX.1-Fill-dev       flux1-fill-dev.safetensors

# Cosmos models
download_hf_model cosmos           text_encoders/        https://huggingface.co/comfyanonymous/cosmos_1.0_text_encoder_and_VAE_ComfyUI/resolve/main/text_encoders/oldt5_xxl_fp8_e4m3fn_scaled.safetensors
download_hf_model cosmos           vae/                  https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
download_hf_model cosmos           diffusion_models/     https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2B_t2i.safetensors

download_hf_model cosmos_2b        diffusion_models/     https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2B_video2world_480p_16fps.safetensors
download_hf_model cosmos_2b        diffusion_models/     https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_2B_video2world_720p_16fps.safetensors
download_hf_model cosmos_14b       diffusion_models/     https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_14B_video2world_480p_16fps.safetensors
download_hf_model cosmos_14b       diffusion_models/     https://huggingface.co/Comfy-Org/Cosmos_Predict2_repackaged/resolve/main/cosmos_predict2_14B_video2world_720p_16fps.safetensors

########################################################################################
# WAN 2.1 models
# https://comfyanonymous.github.io/ComfyUI_examples/wan/
########################################################################################

# Common
download_hf_model wan_common      text_encoders/        Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
download_hf_model wan_common      vae/                  Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/vae/wan_2.1_vae.safetensors

# Text to Video
download_hf_model wan_t2v         diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors # 2.7GB
download_hf_model wan_t2v         diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_t2v_14B_fp16.safetensors # 27GB

# VACE Reference Image to Video
# (output does not contain reference image)
download_hf_model wan_vace         diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_vace_1.3B_fp16.safetensors # 4GB
download_hf_model wan_vace         diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors # 32GB

# Image to Video
download_hf_model wan_i2v         diffusion_models/     Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/diffusion_models/wan2.1_i2v_480p_14B_fp16.safetensors
download_hf_model wan_i2v         clip_vision/          Comfy-Org/Wan_2.1_ComfyUI_repackaged    split_files/clip_vision/clip_vision_h.safetensors
