#!/usr/bin/env bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Give one K40c to a virtual machine (vfio-pci) and take it back.
# USER STEP: the agent must not run this (AGENTS.md, hardware safety).
# NOT TESTED YET (written 2026-10-07 without root, details checked
# 2026-10-12). Read docs/PASSTHROUGH.md.
#
#   scripts/passthrough.sh status              no root, changes nothing
#   sudo scripts/passthrough.sh prepare-xorg [--strict]   X uses only the K600 (--strict:
#                                              also no USB display adapters, see below)
#   sudo scripts/passthrough.sh revert-xorg    undo prepare-xorg
#   sudo scripts/passthrough.sh attach         nvidia -> vfio-pci (card for a guest); only works
#                                              with no desktop session (text console)
#   sudo scripts/passthrough.sh attach-at-boot the nvidia driver never gets the card, from the
#                                              next boot until "detach" (use this from a desktop)
#   sudo scripts/passthrough.sh detach         vfio-pci -> nvidia (driver card back on the host driver)
#
# The card is the development card of tools/guest/config.sh (0000:04:00.0).
# The other K40c and the K600 are never touched.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
# As root: run only when this script and config.sh are equal to origin/main.
. "$HERE/scripts/root-guard.sh"
root_guard_check
. "$HERE/tools/guest/config.sh"
# GPU_BDF goes into a modprobe.d line that runs as root at each boot.
root_guard_bdf "$GPU_BDF"
[[ $GPU_UUID =~ ^GPU-[0-9a-f-]{36}$ ]] || root_guard_die "not a GPU UUID: '$GPU_UUID'"
DEV=/sys/bus/pci/devices/$GPU_BDF
XCONF=/etc/X11/xorg.conf.d/20-display-k600-only.conf
MODCONF=/etc/modprobe.d/k40c-vfio.conf
INITHOOK=/etc/initramfs-tools/hooks/k40c-vfio
OWNERFILE=/etc/k40c-vfio-owner
# Name of the bound driver, or nothing when the card has no driver.
driver() { [[ -L $DEV/driver ]] && basename "$(readlink -f "$DEV/driver")" || true; }
need_root() { [[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }; }
die() { echo "ERROR: $*" >&2; exit 1; }

# Refuse to continue unless the card is the K40c that the project expects.
check_card() {
    [[ -d $DEV ]] || die "no PCI device $GPU_BDF"
    [[ $(cat "$DEV/vendor") == 0x10de && $(cat "$DEV/device") == 0x1024 ]] || die "$GPU_BDF is not a Tesla K40c"
    [[ $(cat "$DEV/class") == 0x030200 ]] || die "$GPU_BDF is a display adapter, not the compute card"
    local n; n=$(ls "$DEV/iommu_group/devices" | wc -l)
    [[ $n -eq 1 ]] || die "$GPU_BDF shares its IOMMU group with $((n - 1)) other device(s)"
}

status() {
    check_card
    echo "card $GPU_BDF: driver '$(driver)', IOMMU group $(basename "$(readlink -f "$DEV/iommu_group")"), reset $(cat "$DEV/reset_method" 2>/dev/null || echo '?')"
    if [[ $(driver) == vfio-pci ]]; then
        g=/dev/vfio/$(basename "$(readlink -f "$DEV/iommu_group")")
        [[ -w $g ]] && echo "guest access: $g is writable by $(id -un): ready for tools/guest/linux-run.sh --gpu" \
                    || echo "guest access: $g is NOT writable by $(id -un): run sudo scripts/passthrough.sh attach"
    fi
    for d in /sys/bus/pci/devices/*; do
        [[ $(cat "$d/vendor") == 0x10de && $(cat "$d/class") == 0x03* ]] || continue
        echo "  $(basename "$d") $(cat "$d/device") driver=$(basename "$(readlink -f "$d/driver" 2>/dev/null)" 2>/dev/null)"
    done
    if [[ $(driver) == nvidia ]]; then
        echo "processes on the card (must be none before attach):"
        nvidia-smi --query-compute-apps=gpu_uuid,pid,name --format=csv,noheader | grep "$GPU_UUID" || echo "  no compute process"
        nvidia-smi | awk -v i="$(nvidia-smi --query-gpu=index,uuid --format=csv,noheader | grep "$GPU_UUID" | cut -d, -f1)" \
            '/Processes/{p=1} p && $2==i && $6=="G"{print "  X client: " $0}'
    fi
    [[ -f $MODCONF ]] && echo "boot-time reservation: installed (the card goes to vfio-pci at every boot until detach)"
    [[ -f $XCONF ]] && echo "X config: $XCONF is installed" || echo "X config: not installed (X opens every NVIDIA card)"
    echo "memlock limit: $(ulimit -l) kB (a guest with the card pins all of its memory)"
}

case "${1:-status}" in
status) status ;;
prepare-xorg)
    need_root
    k600=""
    for d in /sys/bus/pci/devices/*; do
        [[ $(cat "$d/vendor") == 0x10de && $(cat "$d/class") == 0x030000 ]] && k600=$(basename "$d")
    done
    [[ -n $k600 ]] || die "no NVIDIA VGA adapter found"
    IFS=':.' read -r _ bus slot fn <<< "$k600"
    mkdir -p "$(dirname "$XCONF")"
    # "AutoAddGPU false" also stops X from adding USB display adapters:
    # with it, the monitors on a DisplayLink dock (evdi) stay dark (seen on
    # 2026-10-12). It is written only with --strict. Without it, check with
    # "status" after the login that X is not on the K40c.
    flags=""
    [[ ${2:-} == --strict ]] && flags='Section "ServerFlags"
    Option "AutoAddGPU" "false"
EndSection'
    cat > "$XCONF" <<CONF
# Written by haiku-k40c/scripts/passthrough.sh. X uses only the display
# adapter at $k600 and does not open the Tesla K40c cards, so that a
# K40c can be unbound from the nvidia driver while X runs.
$flags
Section "Device"
    Identifier "DisplayAdapter"
    Driver "nvidia"
    BusID "PCI:$((16#$bus)):$((16#$slot)):$fn"
    Option "ProbeAllGpus" "false"
EndSection
CONF
    echo "Wrote $XCONF. It takes effect when X starts again (log out and in, or reboot)."
    echo "If the desktop does not start: boot to a text console and run 'sudo $0 revert-xorg'." ;;
revert-xorg)
    need_root; rm -f "$XCONF"; echo "Removed $XCONF. Restart X." ;;
attach)
    need_root; check_card
    if [[ $(driver) == vfio-pci ]]; then
        grp=$(basename "$(readlink -f "$DEV/iommu_group")")
        chown "${SUDO_USER:-root}" "/dev/vfio/$grp"
        echo "already attached; /dev/vfio/$grp belongs to ${SUDO_USER:-root}"; exit 0
    fi
    modprobe vfio-pci
    if [[ -z $(driver) ]]; then
        # No driver: an earlier attach got as far as the unbind. Go on.
        echo "the card has no driver (an earlier attach unbound it): binding vfio-pci"
    else
        [[ $(driver) == nvidia ]] || die "unexpected driver '$(driver)'"
        nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | grep -q "$GPU_UUID" \
            && die "a compute process uses the card. Run ~/llm-server/llm-mode.sh one-t1k first."
        # nvidia-persistenced keeps every NVIDIA card open, and the unbind
        # below waits until all clients have closed the card (seen on
        # 2026-10-12: it waited for minutes). Stop it; detach starts it again.
        if systemctl is-active --quiet nvidia-persistenced; then
            echo "stopping nvidia-persistenced (it holds the card open)"
            systemctl stop nvidia-persistenced
        fi
        # Tell the driver to stop using the card, then unbind. The unbind
        # waits, and cannot be interrupted, while a client has the card open.
        nvidia-smi drain -p "$GPU_BDF" -m 1 || die "nvidia-smi drain failed: a client (X?) holds the card. See prepare-xorg."
        echo "unbinding from nvidia (if this takes more than a minute, a client still holds the card)"
        echo "$GPU_BDF" > /sys/bus/pci/drivers/nvidia/unbind
    fi
    echo vfio-pci > "$DEV/driver_override"
    echo "$GPU_BDF" > /sys/bus/pci/drivers_probe
    [[ $(driver) == vfio-pci ]] || die "the card did not bind to vfio-pci (driver '$(driver)')"
    grp=$(basename "$(readlink -f "$DEV/iommu_group")")
    chown "${SUDO_USER:-root}" "/dev/vfio/$grp"
    echo "Attached: $GPU_BDF is on vfio-pci, /dev/vfio/$grp belongs to ${SUDO_USER:-root}."
    echo "Guest: tools/guest/linux-run.sh --gpu     Take it back: sudo $0 detach" ;;
attach-at-boot|attach-at-next-boot)
    # The card cannot be taken from the nvidia driver once that driver has
    # it: with a desktop session Xorg, gnome-shell and gnome-remote-desktop
    # keep it open, and early in the boot nvidia_modeset does (2026-10-13:
    # an unbind from a boot unit never returned and the display did not
    # start). So the driver must never get the card. The nvidia module is
    # loaded from the initramfs; the line below runs each time it is
    # loaded and reserves the card for vfio-pci first. It stays in force
    # at every boot until "detach" removes it.
    need_root; check_card
    systemctl disable k40c-vfio-once.service >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/k40c-vfio-once.service /etc/k40c-vfio-once
    systemctl daemon-reload
    cat > "$MODCONF" <<CONF
# haiku-k40c passthrough (scripts/passthrough.sh attach-at-boot). Remove
# with "sudo scripts/passthrough.sh detach".
install nvidia grep -q 0x1024 $DEV/device && echo vfio-pci > $DEV/driver_override; /sbin/modprobe vfio-pci; echo $GPU_BDF > /sys/bus/pci/drivers_probe; /sbin/modprobe --ignore-install nvidia \$CMDLINE_OPTS
CONF
    cat > "$INITHOOK" <<'HOOK'
#!/bin/sh
# haiku-k40c passthrough: put vfio-pci into the initramfs.
case "$1" in prereqs) echo ""; exit 0 ;; esac
. /usr/share/initramfs-tools/hook-functions
manual_add_modules vfio-pci
HOOK
    chmod 755 "$INITHOOK"
    echo "${SUDO_USER:-root}" > "$OWNERFILE"
    initrd=/boot/initrd.img-$(uname -r)
    [[ -f $initrd.before-k40c ]] || cp -p "$initrd" "$initrd.before-k40c"
    update-initramfs -u -k "$(uname -r)"
    grep -q 'vfio-pci.ko' <<<"$(lsinitramfs "$initrd")" || die "vfio-pci is not in $initrd. Run: sudo $0 detach"
    grep -q "etc/modprobe.d/$(basename "$MODCONF")" <<<"$(lsinitramfs "$initrd")" || die "$MODCONF is not in $initrd. Run: sudo $0 detach"
    echo "Installed $MODCONF and rebuilt $initrd (copy of the old one: $initrd.before-k40c)."
    echo "Reboot. After the boot: 'scripts/passthrough.sh status' must show driver 'vfio-pci';"
    echo "then run 'sudo $0 attach' once to give the device to your account."
    echo "The card stays with vfio-pci at every boot until: sudo $0 detach" ;;
detach)
    need_root; check_card
    pgrep -f "vfio-pci,host=${GPU_BDF#0000:}" >/dev/null && die "a guest still uses the card. Shut it down first."
    if [[ -f $MODCONF || -f $INITHOOK ]]; then
        echo "removing the boot-time reservation and rebuilding the initramfs"
        rm -f "$MODCONF" "$INITHOOK" "$OWNERFILE"
        update-initramfs -u -k "$(uname -r)"
        rm -f "/boot/initrd.img-$(uname -r).before-k40c"
    fi
    [[ $(driver) == nvidia ]] && { echo "already on nvidia"; exit 0; }
    [[ $(driver) == vfio-pci ]] && echo "$GPU_BDF" > /sys/bus/pci/drivers/vfio-pci/unbind
    echo > "$DEV/driver_override"
    echo "$GPU_BDF" > /sys/bus/pci/drivers_probe
    nvidia-smi drain -p "$GPU_BDF" -m 0 >/dev/null 2>&1 || true
    systemctl start nvidia-persistenced 2>/dev/null || true
    [[ $(driver) == nvidia ]] || die "the card did not return to nvidia (driver '$(driver)'). A reboot restores it."
    echo "Detached: $GPU_BDF is on nvidia again. Keep llm-server in mode one: this is the driver card (ADR 003)." ;;
*) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
