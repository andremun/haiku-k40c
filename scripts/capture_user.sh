#!/usr/bin/env bash
# PCI and driver captures that need no root. Writes to reference/pci/.
# Read-only: sysfs, /proc and query commands. Formats: reference/pci/README.md.
# Covers every NVIDIA display device that is present, so a change of slot
# needs no edit here. Run scripts/capture_root.sh (sudo) after it.
# Usage: scripts/capture_user.sh
set -euo pipefail
OUT="$(cd "$(dirname "$0")/.." && pwd)/reference/pci"
mkdir -p "${OUT}"
STAMP="# Captured $(date -Iseconds) without root. Root-only fields show as <access denied>/zeros."
gpus=()
for d in /sys/bus/pci/devices/*; do
    [[ $(cat "$d/vendor") == 0x10de && $(cat "$d/class") == 0x03* ]] && gpus+=("$(basename "$d")")
done
[[ ${#gpus[@]} -gt 0 ]] || { echo "No NVIDIA display device found." >&2; exit 1; }
for dev in "${gpus[@]}"; do
    bdf=${dev#0000:}; tag=${bdf//[:.]/_}; s=/sys/bus/pci/devices/${dev}
    lspci -vvv -nn -s "${bdf}" > "${OUT}/lspci-vvv-${tag}.txt" 2>/dev/null
    cat "$s/resource" > "${OUT}/resource-${tag}.txt"
    xxd -l 64 "$s/config" > "${OUT}/config-${tag}.hex"
    for k in numa_node local_cpulist current_link_speed current_link_width \
             max_link_speed max_link_width irq; do
        echo "$k: $(cat "$s/$k")"
    done > "${OUT}/sysfs-${tag}.txt"
    cat "/proc/driver/nvidia/gpus/${dev}/information" > "${OUT}/nvidia-proc-${tag}.txt"
done
{ echo "${STAMP}"; lspci -nn; } > "${OUT}/lspci-nn.txt"
lspci -tv > "${OUT}/lspci-tree.txt"
{ head -1 /proc/interrupts; grep -i nvidia /proc/interrupts; } > "${OUT}/interrupts.txt"
{ uname -a; cat /proc/driver/nvidia/version; lsmod | grep -E '^(nvidia|video)' || true
  grep -rhs nvidia /etc/modprobe.d/ || true; } > "${OUT}/os.txt"
nvidia-smi -q > "${OUT}/nvidia-smi-q.txt"
nvidia-smi -q -d MEMORY,CLOCK > "${OUT}/nvidia-smi-mem-clock.txt"
nvidia-smi topo -m > "${OUT}/nvidia-smi-topo.txt"
echo "Written to ${OUT} for: ${gpus[*]}"
