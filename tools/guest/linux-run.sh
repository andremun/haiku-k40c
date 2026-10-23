#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Start the Linux reference guest and run a command in it over SSH.
#
#   tools/guest/linux-run.sh                 start, copy tools/guest/files, open a shell
#   tools/guest/linux-run.sh CMD...          start, copy the files, run CMD, power off
#   tools/guest/linux-run.sh --gpu [CMD...]  the same with the K40c passed through
#
# --gpu needs the card bound to vfio-pci first (sudo scripts/passthrough.sh
# attach, see docs/PASSTHROUGH.md). Without --gpu the guest has no GPU.
# The agent must not use --gpu (AGENTS.md, hardware safety).
set -uo pipefail
. "$(dirname "$0")/config.sh"
T="$(cd "$(dirname "$0")" && pwd)"
gpu=(); mem=4096
if [ "${1:-}" = "--gpu" ]; then
    shift
    drv=$(basename "$(readlink -f "/sys/bus/pci/devices/$GPU_BDF/driver" 2>/dev/null)" 2>/dev/null)
    [ "$drv" = "vfio-pci" ] || { echo "The card $GPU_BDF is bound to '${drv:-nothing}', not vfio-pci. See docs/PASSTHROUGH.md." >&2; exit 2; }
    grp=$(basename "$(readlink -f "/sys/bus/pci/devices/$GPU_BDF/iommu_group")")
    [ -w "/dev/vfio/$grp" ] || { echo "No write access to /dev/vfio/$grp (sudo scripts/passthrough.sh attach sets it)." >&2; exit 2; }
    gpu=(-device "vfio-pci,host=${GPU_BDF#0000:}")
fi
cd "$GUEST_DIR" || { echo "No guest: run tools/guest/linux-setup.sh" >&2; exit 2; }
[ -f .provisioned ] || { echo "The guest is not set up: run tools/guest/linux-setup.sh" >&2; exit 2; }
ss -ltn 2>/dev/null | grep -q ":$GUEST_SSH_PORT " && { echo "Port $GUEST_SSH_PORT is in use: a guest is running." >&2; exit 2; }
qemu-system-x86_64 -name k40c-linux -enable-kvm -machine q35 -cpu host -smp 4 -m "$mem" \
    -drive if=pflash,format=raw,readonly=on,file="$OVMF_CODE" \
    -drive if=pflash,format=raw,file=ovmf-vars.fd \
    -drive file=disk.qcow2,if=virtio \
    -netdev user,id=n0,hostfwd=tcp:127.0.0.1:$GUEST_SSH_PORT-:22 -device virtio-net-pci,netdev=n0 \
    "${gpu[@]}" -display none -serial file:serial.log -monitor unix:monitor.sock,server,nowait \
    >qemu.out 2>&1 &
qpid=$!
S=(-i id_guest -p "$GUEST_SSH_PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5)
for _ in $(seq 60); do
    kill -0 "$qpid" 2>/dev/null || { echo "QEMU stopped:"; cat qemu.out; exit 1; }
    ssh "${S[@]}" dev@127.0.0.1 true 2>/dev/null && break; sleep 3
done
ssh "${S[@]}" dev@127.0.0.1 true || { echo "No SSH to the guest in 3 minutes (see $GUEST_DIR/serial.log)"; kill "$qpid"; exit 1; }
scp -q -P "$GUEST_SSH_PORT" "${S[@]:0:2}" "${S[@]:4}" -r "$T/files" dev@127.0.0.1:
if [ $# -eq 0 ]; then
    ssh "${S[@]}" -t dev@127.0.0.1; rc=$?
else
    ssh "${S[@]}" dev@127.0.0.1 "cd files && $*"; rc=$?
fi
ssh "${S[@]}" dev@127.0.0.1 sudo poweroff 2>/dev/null
for _ in $(seq 30); do kill -0 "$qpid" 2>/dev/null || break; sleep 1; done
kill "$qpid" 2>/dev/null
exit $rc
