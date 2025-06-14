# Cache HF models on NFS
export HF_HOME="/workspace/.cache/huggingface"

# Cache pip packages on NFS to avoid having to redownload them each time the container is created
export PIP_CACHE_DIR="/workspace/.cache/pip"

# Persistent storage path
install_root="/workspace"

kohya_ss_parent="/opt"
kohya_ss_dir="${kohya_ss_parent}/kohya_ss"

# Having the venv on NFS makes ComfyUI start up extremely slow
#venv_dir="/workspace/venv"
venv_dir=""

model_size_fn="${install_root}/model_size.txt"

do_apt_upgrade=0

# psmisc for killall
extra_apt_packages="
    vim
    htop
    net-tools
    ncdu
    psmisc
    rsync
    imagemagick
"
