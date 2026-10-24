#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Read-only PCI captures that need root. Writes to reference/pci/root/.
# No writes to PCI config space, no BAR access, no driver changes.
# Root writes into a private temporary folder. The user account copies the
# files into the repository (scripts/root-guard.sh).
# Usage: sudo scripts/capture_root.sh
set -euo pipefail
. "$(dirname "$0")/root-guard.sh"
[[ ${EUID} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
root_guard_check
OUT=$(mktemp -d)
trap 'rm -rf "${OUT}"' EXIT
# Every NVIDIA display device that is present (2 x K40c and the K600).
gpus=()
for d in /sys/bus/pci/devices/*; do
    [[ $(cat "$d/vendor") == 0x10de && $(cat "$d/class") == 0x03* ]] && gpus+=("$(basename "$d")")
done
[[ ${#gpus[@]} -gt 0 ]] || { echo "No NVIDIA display device found." >&2; exit 1; }
pat=$(IFS='|'; echo "${gpus[*]}")
for dev in "${gpus[@]}"; do
    bdf=${dev#0000:}; tag=${bdf//[:.]/_}
    lspci -vvv -nn -s "${bdf}" > "${OUT}/lspci-vvv-${tag}.txt"
    lspci -xxxx -s "${bdf}" > "${OUT}/lspci-xxxx-${tag}.txt"
    { echo "COMMAND=$(setpci -s "${bdf}" COMMAND)"
      echo "STATUS=$(setpci -s "${bdf}" STATUS)"
      echo "INTERRUPT_LINE=$(setpci -s "${bdf}" INTERRUPT_LINE)"
      echo "INTERRUPT_PIN=$(setpci -s "${bdf}" INTERRUPT_PIN)"; } > "${OUT}/setpci-${tag}.txt"
done
grep -iE "nvidia|${pat}" /proc/iomem > "${OUT}/iomem.txt" || true
dmesg | grep -iE "nvidia|nouveau|NVRM|${pat}" > "${OUT}/dmesg-gpu.txt" || true
dmidecode -t memory > "${OUT}/dmidecode-memory.txt"
dmidecode -t bios -t system > "${OUT}/dmidecode-system.txt"
root_guard_save reference/pci/root "${OUT}"/*
echo "Written to ${ROOT_GUARD_REPO}/reference/pci/root for: ${gpus[*]}"
