#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Load one kernel driver in the Haiku test VM and print what it logged.
#
# Usage: tools/haiku/vm-test.sh DRIVER_FILE [DEV_SUBDIR]
#   DRIVER_FILE  output of build-driver.sh (build/haiku/NAME)
#   DEV_SUBDIR   directory under /dev that publishes it (default: misc)
#
# What it does: boots Haiku under QEMU/KVM from a throw-away snapshot (the
# disk image is never changed), installs the driver in non-packaged, makes
# devfs load it, copies the kernel log lines from that point, shuts down.
# Takes about 2 minutes. Full kernel log: $HAIKU_VM_DIR/serial.log.
#
# The VM has NO access to the GPUs. This script takes no QEMU options on
# purpose: never add host devices (vfio-pci) to it.
#
# Exit status: 0 the test commands ran to the end; 1 boot or test timeout;
# 3 kernel panic seen in the log.
set -u
. "$(dirname "$0")/config.sh"
drv=${1:?usage: vm-test.sh DRIVER_FILE [DEV_SUBDIR]}; sub=${2:-misc}
[ -f "$drv" ] || { echo "no such file: $drv" >&2; exit 2; }
name=$(basename "$drv"); V=$HAIKU_VM_DIR; T="$(dirname "$0")"
img=$(ls "$V"/haiku-*-anyboot.iso 2>/dev/null | head -1)
[ -n "$img" ] || { echo "no Haiku image in $V" >&2; exit 2; }
if [ -S "$V/monitor.sock" ] && python3 -c "
import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect('$V/monitor.sock')" 2>/dev/null; then
    echo "a test VM is already running (monitor.sock is live)" >&2; exit 2
fi
work=$(mktemp -d); mkdir "$work/share"; cp "$drv" "$work/share/$name"
log=$V/serial.log; rm -f "$log" "$V/monitor.sock"; cp /usr/share/OVMF/OVMF_VARS_4M.fd "$V/ovmf-vars.fd"
hmp()  { python3 "$T/qemu_hmp.py" "$V/monitor.sock" cmd "$1" >/dev/null; }
typ()  { python3 "$T/qemu_hmp.py" "$V/monitor.sock" type "$1"; }
waitlog() { # pattern timeout_seconds
    local i; for ((i = 0; i < $2; i++)); do grep -aq "$1" "$log" 2>/dev/null && return 0; sleep 1; done; return 1; }
cleanup() {
    [ -S "$V/monitor.sock" ] && hmp quit 2>/dev/null
    kill "$http" 2>/dev/null; rm -rf "$work"; rm -f "$V/monitor.sock"
}
trap cleanup EXIT
# The file server takes a free port and writes it to a file, so the guest
# never fetches the driver from another server on a fixed port.
python3 "$T/transfer_server.py" --root "$work" --port 0 --port-file "$work/port" --max-total 0 \
    >/dev/null 2>&1 & http=$!
for _ in $(seq 50); do [ -s "$work/port" ] && break; sleep 0.1; done
port=$(cat "$work/port" 2>/dev/null) || { echo "FAIL: the file server did not start" >&2; exit 2; }
qemu-system-x86_64 -name haiku-test -enable-kvm -machine q35 -cpu host -smp 2 -m 2048 -snapshot \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file="$V/ovmf-vars.fd" \
    -drive file="$img",format=raw,if=none,id=d0 -device ide-hd,drive=d0,bus=ide.0 \
    -vga std -netdev user,id=n0,restrict=off -device e1000,netdev=n0 \
    -display none -serial file:"$log" -monitor unix:"$V/monitor.sock",server,nowait \
    >"$V/qemu.out" 2>&1 &
waitlog "ps2: keyboard found" 120 || { echo "FAIL: Haiku did not boot in 120 s (see $log)"; exit 1; }
sleep 20; hmp "sendkey ret"                       # welcome dialog: "Try Haiku"
waitlog "first login script" 90 || { echo "FAIL: desktop did not start"; exit 1; }
sleep 12; hmp "sendkey alt-meta_l-t"; sleep 8     # Tracker shortcut: open Terminal
D=/boot/system/non-packaged/add-ons/kernel/drivers
typ "mkdir -p $D/bin $D/dev/$sub; cd $D/bin; echo VMTEST-BEGIN > /dev/dprintf"
typ "curl -s -O http://10.0.2.2:$port/$name; chmod +x $name; ln -sf ../../bin/$name ../dev/$sub/$name"
typ "ls /dev/$sub > /dev/null; sleep 3; echo VMTEST-END > /dev/dprintf"
rc=0
waitlog "VMTEST-END" 60 || { echo "FAIL: test commands did not finish in 60 s"; rc=1; }
sed -n '/VMTEST-BEGIN/,/VMTEST-END/p' "$log" | sed 's/\x1b\[[0-9;]*m//g'
if grep -aq "PANIC:" "$log"; then echo "KERNEL PANIC (see $log):"; grep -a -A12 "PANIC:" "$log" | head -30; rc=3; fi
exit $rc
