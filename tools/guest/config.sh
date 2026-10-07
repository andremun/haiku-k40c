# Shared settings for the GPU guest tools. Sourced, not run.
# The guests live outside the repository, next to the Haiku test VM.
: "${HAIKU_CROSS:=$HOME/haiku-cross}"
GUEST_DIR="$HAIKU_CROSS/linux-guest"
GUEST_SSH_PORT=2222
# The K40c that may go to a guest: the development card (assumption S1).
# The other K40c keeps the language model (llm-mode.sh one).
GPU_BDF="0000:04:00.0"
GPU_UUID="GPU-305da5a6-e0a3-a36a-963b-4c099fd262f5"
OVMF_CODE=/usr/share/OVMF/OVMF_CODE_4M.fd
OVMF_VARS=/usr/share/OVMF/OVMF_VARS_4M.fd
