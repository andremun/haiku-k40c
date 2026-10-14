#!/usr/bin/env bash
# Run in the Linux guest with the K40c (tools/guest/linux-run.sh --gpu).
# Saves Nouveau's copy of the card's firmware image (VBIOS) to out/vbios/.
# Reads only. The guest has no PCI ROM file for the card (QEMU does not
# expose one), so Nouveau's copy from debugfs is the source.
set -u
mkdir -p out/vbios
lsmod | grep -q '^nouveau' || sudo modprobe nouveau
sleep 12
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
f=$(sudo sh -c 'ls /sys/kernel/debug/dri/*/vbios.rom' | head -1)
[ -n "$f" ] || { echo "no vbios.rom in debugfs"; exit 2; }
sudo cat "$f" > out/vbios/vbios.rom
sudo dmesg | grep -i "nouveau.*bios" > out/vbios/dmesg-bios.txt
sha256sum out/vbios/vbios.rom
