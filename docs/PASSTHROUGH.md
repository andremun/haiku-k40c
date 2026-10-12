# GPU passthrough: one K40c for a test VM

Status: PREPARED, NOT ENABLED, NOT TESTED. Written 2026-10-07 without
root; details checked against the machine and corrected on 2026-10-12
(see "Checked on 2026-10-12"). The first use is a user step, with this
document open. Nothing here is active until `scripts/passthrough.sh
attach` runs.

## Why

Phases E and later need the real card. Without passthrough each test is a
reboot into Haiku, and only the user can do it. With passthrough the
development card goes to a virtual machine while the other K40c keeps the
language model. A test then takes about two minutes and needs no reboot.
The same mechanism gives the Linux reference guest of task C5.

| Card | Address | Role |
|---|---|---|
| K40c, development card | 0000:04:00.0 (IOMMU group 23, alone) | Goes to the guest |
| K40c, second card | 0000:03:00.0 (IOMMU group 22, alone) | Keeps the model (`llm-mode.sh one-t1k`) |
| Quadro K600 | 0000:82:00.0 | Display. Never passed through. |

## What exists

| File | Use | Root |
|---|---|---|
| `scripts/passthrough.sh` | `status`, `prepare-xorg`, `attach`, `detach` | yes, except `status` |
| `tools/guest/linux-setup.sh` | Builds the Linux reference guest in `~/haiku-cross/linux-guest` | no |
| `tools/guest/linux-run.sh [--gpu] [CMD]` | Starts the guest, copies `tools/guest/files`, runs a command | no |
| `tools/guest/files/compute_test.c` | The reference job `output[i] = input[i] + 1` (GL ES 3.1 compute shader) | - |
| `tools/guest/files/run_test.sh [--k40c]` | In the guest: build and run the job; with `--k40c` load Nouveau under `mmiotrace` first, and fail unless the renderer is Nouveau | - |
| `tools/guest/files/build_mesa_debug.sh` | In the guest, once, no GPU: a debug build of Mesa in `/opt/mesa-debug`, needed for the print of the shader code | - |

The host has what it needs: the IOMMU is on (75 groups), `vfio-pci` is in
the kernel, the bus reset method is available for the card, QEMU and OVMF
are installed, and the memory-lock limit (8 GB) is above the guest size.

## Known obstacle: X holds the K40c cards

The X server opens every NVIDIA card (`nvidia-smi` shows Xorg with 4 MiB on
each K40c). The nvidia driver cannot release a card that X has open, so
`attach` would wait and fail. `prepare-xorg` writes
`/etc/X11/xorg.conf.d/20-display-k600-only.conf`, which limits X to the
K600. INFERRED: the options `AutoAddGPU false` and `ProbeAllGpus false`
are enough for driver 470. It is not tested. If the desktop does not
start after it, run `sudo scripts/passthrough.sh revert-xorg` from a text
console.

**Side effect seen on the first use (2026-10-12):** the file had
`Option "AutoAddGPU" "false"`, and with it X did not add the displays of
the DisplayLink dock (Dell D6000, `evdi`): the monitors on the dock stayed
dark. X did release both K40c cards (no X client on them), and the
monitor on the K600 worked. `prepare-xorg` now writes that option only
with `--strict`. Whether `ProbeAllGpus false` alone keeps X off the K40c
is not tested: check with `status` after the login. To get the dock
displays back at any time: `sudo scripts/passthrough.sh revert-xorg` and
a new login.

A second client is `nvidia-persistenced` (active). If `attach` still
fails after the X change, stop it: `sudo systemctl stop nvidia-persistenced`.

## Result of the first attempt (2026-10-12): use the boot-time attach

The live `attach` does not work from a desktop session. After
`prepare-xorg`, X used no memory on the K40c cards, but Xorg, gnome-shell
and gnome-remote-desktop each still kept the device file of every NVIDIA
card open (`/dev/nvidia1` for the card at 04:00.0), and so did
`nvidia-persistenced`. The unbind from the nvidia driver waits until all
of them close it, and it cannot be interrupted: it waited until the
reboot.

Use `sudo scripts/passthrough.sh attach-at-next-boot` and reboot. A
one-time unit gives the card to `vfio-pci` before the display manager
starts, so nothing has it open. No X configuration is needed (run
`revert-xorg` if `prepare-xorg` was used). After that boot the router
cannot load its two-card model: run `~/llm-server/llm-mode.sh one-t1k`.
Steps 1 to 4 below are replaced by this; steps 5 to 7 are unchanged.
`detach` works with the desktop running.

## Procedure

First use, in this order. Stop at the first step that fails.

1. `scripts/passthrough.sh status` (no root). The card must be on
   `nvidia` and in its own IOMMU group.
2. `sudo scripts/passthrough.sh prepare-xorg`, then log out and in. Run
   `status` again: no X client on the card.
3. `~/llm-server/llm-mode.sh one-t1k` (done by the scaffold on
   2026-10-12; check with `~/llm-server/llm-mode.sh status`). The model
   is on the card at 03:00.0. `status`: no compute process on 04:00.0.
   After a reboot the router starts in mode `dual-t1k` again: run the
   command again.
4. `sudo scripts/passthrough.sh attach`. The card is on `vfio-pci`.
5. `tools/guest/linux-run.sh --gpu` (a shell in the guest), then in the
   guest `cd files && ./run_test.sh --k40c`. Expected in
   `out/RESULT.txt`: `renderer:` names NVF1 or Nouveau, `PASS`, and
   `mesa: debug build`. With a command on the `linux-run.sh` line the
   guest powers off when the command ends and the logs are lost, so use
   the shell.
6. Before you leave the guest shell, from a second terminal on the
   host, in the repository: `mkdir -p reference/linux-run && scp -P 2222
   -i ~/haiku-cross/linux-guest/id_guest -o StrictHostKeyChecking=no -o
   UserKnownHostsFile=/dev/null 'dev@127.0.0.1:files/out/*'
   reference/linux-run/`. Then `exit` in the guest.
7. `sudo scripts/passthrough.sh detach`, then `~/llm-server/llm-mode.sh
   two-t1k` (or `dual-t1k`).

The model has one card while the other is attached: one agent session,
not two.

## Checked on 2026-10-12

Read-only checks by the scaffold, no root:

| Item | State |
|---|---|
| Card addresses, IOMMU groups, GPU UUID in `tools/guest/config.sh` | As in the table above. Each K40c is alone in its group. |
| IOMMU | On: 75 groups, `dmar0` and `dmar1` present. The kernel command line has no `intel_iommu=on`; the Ubuntu kernel enables it by default. |
| Interrupt remapping | Not verified (the kernel log needs root). If QEMU refuses the card with a message about interrupt remapping, stop and ask. |
| `vfio-pci` | A module of kernel 6.8.0-138, not loaded; `attach` loads it. |
| Reset method of the card | `bus`. |
| X server | Holds 4 MiB on the card at 04:00.0: `prepare-xorg` and a new login are needed, as described. No `/etc/X11/xorg.conf` and no file in `xorg.conf.d` exist. |
| `nvidia-persistenced` | Active. |
| Model | Mode `one-t1k`: the server runs on 03:00.0 only, no process on 04:00.0. |
| `/dev/kvm` | Readable and writable by the user (ACL). |
| Memory lock limit | 8 GB; the guest has 4 GB. |
| Guest | Boots without the GPU. Ubuntu 24.04, kernel 6.8.0-146, Mesa 25.2.8, `nouveau.ko` present and blacklisted for automatic loading, `mmiotrace` tracer available. |

Corrected on that day:

1. **False PASS.** The guest user was not in the group of the render
   node, so the test would have run on the software renderer and printed
   PASS. `run_test.sh` now runs the test as root and, with `--k40c`,
   fails unless the renderer is Nouveau.
2. **No shader code print.** The Mesa package of Ubuntu is a release
   build; `NV50_PROG_DEBUG=1` prints nothing in it. `build_mesa_debug.sh`
   makes a debug build of the same version in the guest (no GPU needed).
3. **Mode names.** `llm-mode.sh one-t1k`, `two-t1k`, `dual-t1k` (the
   modes with the working thinking limit).
4. **Logs.** The run is now done from a shell in the guest, because the
   guest powers off after a command and the logs were not copied out.

Known differences that the analysis must keep in mind: the guest kernel
is 6.8, and the Nouveau source that phases B and C analysed is 6.12. A
log out of the desktop ends the applications of the session; a session of
the coding assistant has to be opened again afterwards.

## Stages for Haiku work (decided at the gate)

| Stage | Guest | What the driver may do | Who runs it |
|---|---|---|---|
| P0 | Linux, Nouveau | Reference run and trace (task C5) | User |
| P1 | Haiku | Read only: PCI, BAR mapping, PMC_BOOT_0, VRAM size | User first, then the agent |
| P2 | Haiku | Writes, only to registers that are in `hardware/registers/` with a source and a status | Reviewed test by test |
| P3 | Haiku | Channel, copy engine, GR (milestones S1 to S3) | Reviewed test by test |

Until the gate, `AGENTS.md` stays as it is: the agent gives no GPU to a
VM. `tools/haiku/vm-test.sh` stays without host devices. A passthrough
test for Haiku will be a separate script.

## Risks

| Risk | Limit |
|---|---|
| A wrong register write hangs the card | The card gets a bus reset when the guest stops. The host and the other card are behind the IOMMU. |
| A write reaches the VBIOS flash or the fan control | Real, small. P2 allows only writes with a source. Save the VBIOS before P2 (`cat /sys/bus/pci/devices/0000:04:00.0/rom` after `echo 1 > .../rom`, as root, card on vfio-pci). |
| The card overheats with no driver in control | The K40c has its own thermal shutdown. Watch the first long P2 test. |
| The host loses the display | Only `prepare-xorg` touches X. It has a revert. |
| The card does not return to `nvidia` | `detach` reports it. A reboot restores the default binding: nothing here is persistent except the X file. |
