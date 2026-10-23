#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Build the Linux reference guest (Ubuntu 24.04, Nouveau and Mesa). No root.
# The guest is the reference for milestone S3: with the K40c passed
# through, it shows that Nouveau and Mesa run a compute job on this card,
# and it gives the register trace. Without the card it runs the same test
# on Mesa's software renderer, which only tests the test program.
# Usage: tools/guest/linux-setup.sh      (about 10 minutes, 3 GB)
set -euo pipefail
. "$(dirname "$0")/config.sh"
T="$(cd "$(dirname "$0")" && pwd)"
IMG_URL=https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img
mkdir -p "$GUEST_DIR"; cd "$GUEST_DIR"
[ -f base.img ] || curl -fL --progress-bar -o base.img "$IMG_URL"
[ -f id_guest ] || ssh-keygen -q -t ed25519 -N "" -C haiku-k40c-guest -f id_guest
if [ ! -f disk.qcow2 ]; then
    qemu-img create -q -f qcow2 -F qcow2 -b base.img disk.qcow2 20G
    rm -f .provisioned
fi
# cloud-init seed: one user with the key above, the packages, no Nouveau
# at boot (the trace must start before the driver loads).
mkdir -p seed
cat > seed/meta-data <<META
instance-id: haiku-k40c-linux-1
local-hostname: k40c-linux
META
cat > seed/user-data <<USER
#cloud-config
users:
  - name: dev
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    ssh_authorized_keys:
      - $(cat id_guest.pub)
write_files:
  - path: /etc/modprobe.d/nouveau-manual.conf
    content: |
      # Loaded by hand (trace.sh), so that mmiotrace can start first.
      blacklist nouveau
package_update: true
packages: [linux-generic, build-essential, pkg-config, libegl-dev, libgles-dev, libgbm-dev,
           libdrm-dev, mesa-utils, pciutils, trace-cmd]
runcmd:
  - touch /var/lib/cloud/provision-done
power_state:
  mode: poweroff
  condition: true
USER
genisoimage -quiet -output seed.iso -volid cidata -joliet -rock seed/user-data seed/meta-data
if [ ! -f .provisioned ]; then
    echo "first boot: install packages (the guest powers off when it is done)"
    cp "$OVMF_VARS" ovmf-vars.fd
    timeout 1800 qemu-system-x86_64 -name k40c-linux -enable-kvm -machine q35 -cpu host -smp 4 -m 4096 \
        -drive if=pflash,format=raw,readonly=on,file="$OVMF_CODE" \
        -drive if=pflash,format=raw,file=ovmf-vars.fd \
        -drive file=disk.qcow2,if=virtio -drive file=seed.iso,media=cdrom \
        -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
        -display none -serial file:serial-setup.log
    touch .provisioned
fi
echo "Ready: $GUEST_DIR. Start it with tools/guest/linux-run.sh"
