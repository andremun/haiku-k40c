#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Read PMC_BOOT_0 (BAR0 offset 0x0, 4 bytes) of the K40c at 0000:04:00.0.
# READ-ONLY: maps the first page of BAR0 read-only and reads one register.
# It answers open question Q1 (which Nouveau chipset entry the card uses).
# Run it in mode "one" (llm-mode.sh one), so that no model is on this card.
# Usage: sudo scripts/read_boot0.sh [BDF]      (default 0000:04:00.0)
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
BDF=${1:-0000:04:00.0}
OUT="$(cd "$(dirname "$0")/.." && pwd)/reference/pci/root"
mkdir -p "${OUT}"
python3 - "/sys/bus/pci/devices/${BDF}/resource0" "${BDF}" <<'PY' | tee "${OUT}/boot0-${BDF//[:.]/_}.txt"
import mmap, os, struct, sys
fd = os.open(sys.argv[1], os.O_RDONLY)
m = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ)
v = struct.unpack("<I", m[0:4])[0]
m.close(); os.close(fd)
chipset = (v >> 20) & 0x1ff
print(f"device {sys.argv[2]}")
print(f"PMC_BOOT_0 = 0x{v:08x}")
print(f"chipset field (bits 28:20) = 0x{chipset:03x}")
print("Nouveau: 0x0f0 -> nvf0_chipset (GK110), 0x0f1 -> nvf1_chipset (GK110B)")
PY
chown -R "${SUDO_USER:-root}:" "${OUT}"
