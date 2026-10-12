#!/usr/bin/env bash
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
#   sudo scripts/passthrough.sh attach-at-next-boot   the same, once, early in the next boot
#                                              (use this from a desktop session)
#   sudo scripts/passthrough.sh detach         vfio-pci -> nvidia (card for the model)
#
# The card is the development card of tools/guest/config.sh (0000:04:00.0).
# The other K40c and the K600 are never touched.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
. "$HERE/tools/guest/config.sh"
DEV=/sys/bus/pci/devices/$GPU_BDF
XCONF=/etc/X11/xorg.conf.d/20-display-k600-only.conf
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
attach-at-next-boot)
    # The live attach cannot work while a desktop session runs: Xorg,
    # gnome-shell and gnome-remote-desktop each keep the device file of
    # every NVIDIA card open (seen on 2026-10-12), and the unbind waits for
    # them. This gives the card to vfio-pci once, early in the next boot,
    # before the display manager and the nvidia services start. No X
    # configuration is needed for it.
    need_root; check_card
    unit=/etc/systemd/system/k40c-vfio-once.service
    cat > "$unit" <<UNIT
[Unit]
Description=Give the Tesla K40c at $GPU_BDF to vfio-pci once (haiku-k40c passthrough)
ConditionPathExists=/etc/k40c-vfio-once
DefaultDependencies=no
After=systemd-modules-load.service local-fs.target
Before=display-manager.service gdm.service nvidia-persistenced.service multi-user.target

[Service]
Type=oneshot
ExecStart=$HERE/scripts/passthrough.sh boot-attach
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
UNIT
    echo "${SUDO_USER:-root}" > /etc/k40c-vfio-once
    systemctl daemon-reload
    systemctl enable k40c-vfio-once.service >/dev/null
    echo "Installed $unit and the one-time mark /etc/k40c-vfio-once."
    echo "Reboot. After the boot: scripts/passthrough.sh status must show driver 'vfio-pci'."
    echo "The mark is removed at that boot, so the boot after it is normal again."
    echo "To cancel before the reboot: sudo rm /etc/k40c-vfio-once" ;;
boot-attach)
    # Run by k40c-vfio-once.service, not by hand.
    need_root; check_card
    owner=$(cat /etc/k40c-vfio-once 2>/dev/null || echo root)
    rm -f /etc/k40c-vfio-once
    modprobe vfio-pci
    echo vfio-pci > "$DEV/driver_override"
    if [[ $(driver) == nvidia ]]; then
        # no client can have the card open this early, so this returns at once
        timeout 20 sh -c "echo $GPU_BDF > /sys/bus/pci/drivers/nvidia/unbind" || die "unbind from nvidia did not finish"
    fi
    echo "$GPU_BDF" > /sys/bus/pci/drivers_probe
    [[ $(driver) == vfio-pci ]] || die "the card did not bind to vfio-pci (driver '$(driver)')"
    grp=$(basename "$(readlink -f "$DEV/iommu_group")")
    # A network account may not be known this early in the boot. Then the
    # device stays with root, and "sudo scripts/passthrough.sh attach" after
    # the login gives it to the user.
    chown "$owner" "/dev/vfio/$grp" 2>/dev/null \
        && echo "$GPU_BDF is on vfio-pci, /dev/vfio/$grp belongs to $owner" \
        || echo "$GPU_BDF is on vfio-pci; /dev/vfio/$grp still belongs to root (run: sudo scripts/passthrough.sh attach)" ;;
detach)
    need_root; check_card
    [[ $(driver) == nvidia ]] && { echo "already on nvidia"; exit 0; }
    pgrep -f "vfio-pci,host=${GPU_BDF#0000:}" >/dev/null && die "a guest still uses the card. Shut it down first."
    [[ $(driver) == vfio-pci ]] && echo "$GPU_BDF" > /sys/bus/pci/drivers/vfio-pci/unbind
    echo > "$DEV/driver_override"
    echo "$GPU_BDF" > /sys/bus/pci/drivers_probe
    nvidia-smi drain -p "$GPU_BDF" -m 0 >/dev/null 2>&1 || true
    systemctl start nvidia-persistenced 2>/dev/null || true
    [[ $(driver) == nvidia ]] || die "the card did not return to nvidia (driver '$(driver)'). A reboot restores it."
    echo "Detached: $GPU_BDF is on nvidia again. Model: ~/llm-server/llm-mode.sh two-t1k (or dual-t1k)" ;;
*) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
