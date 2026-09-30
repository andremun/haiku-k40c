#!/usr/bin/env bash
# Read-only PCI captures that need root. Writes to reference/pci/root/.
# No writes to PCI config space, no BAR access, no driver changes.
# Usage: sudo scripts/capture_root.sh
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
OUT="$(cd "$(dirname "$0")/.." && pwd)/reference/pci/root"
mkdir -p "${OUT}"
for bdf in 04:00.0 81:00.0 03:00.0; do
    tag=${bdf//[:.]/_}
    lspci -vvv -nn -s "${bdf}" > "${OUT}/lspci-vvv-${tag}.txt"
    lspci -xxxx -s "${bdf}" > "${OUT}/lspci-xxxx-${tag}.txt"
    { echo "COMMAND=$(setpci -s "${bdf}" COMMAND)"
      echo "STATUS=$(setpci -s "${bdf}" STATUS)"
      echo "INTERRUPT_LINE=$(setpci -s "${bdf}" INTERRUPT_LINE)"
      echo "INTERRUPT_PIN=$(setpci -s "${bdf}" INTERRUPT_PIN)"; } > "${OUT}/setpci-${tag}.txt"
done
grep -iE "nvidia|0000:(03|04|81):00" /proc/iomem > "${OUT}/iomem.txt" || true
dmesg | grep -iE "nvidia|nouveau|NVRM|0000:(04|81):00" > "${OUT}/dmesg-gpu.txt" || true
dmidecode -t memory > "${OUT}/dmidecode-memory.txt"
dmidecode -t bios -t system > "${OUT}/dmidecode-system.txt"
chown -R "${SUDO_USER:-root}:" "${OUT}"
echo "Written to ${OUT}"
