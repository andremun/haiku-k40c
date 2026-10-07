# GPU passthrough: one K40c for a test VM

Status: PREPARED, NOT ENABLED, NOT TESTED (2026-10-07). The scripts were
written without root. The first use is a user step, with this document
open. Nothing here is active until `scripts/passthrough.sh attach` runs.

## Why

Phases E and later need the real card. Without passthrough each test is a
reboot into Haiku, and only the user can do it. With passthrough the
development card goes to a virtual machine while the other K40c keeps the
language model. A test then takes about two minutes and needs no reboot.
The same mechanism gives the Linux reference guest of task C5.

| Card | Address | Role |
|---|---|---|
| K40c, development card | 0000:04:00.0 (IOMMU group 23, alone) | Goes to the guest |
| K40c, second card | 0000:03:00.0 (IOMMU group 22, alone) | Keeps the model (`llm-mode.sh one`) |
| Quadro K600 | 0000:82:00.0 | Display. Never passed through. |

## What exists

| File | Use | Root |
|---|---|---|
| `scripts/passthrough.sh` | `status`, `prepare-xorg`, `attach`, `detach` | yes, except `status` |
| `tools/guest/linux-setup.sh` | Builds the Linux reference guest in `~/haiku-cross/linux-guest` | no |
| `tools/guest/linux-run.sh [--gpu] [CMD]` | Starts the guest, copies `tools/guest/files`, runs a command | no |
| `tools/guest/files/compute_test.c` | The reference job `output[i] = input[i] + 1` (GL ES 3.1 compute shader) | - |
| `tools/guest/files/run_test.sh [--k40c]` | In the guest: build and run the job; with `--k40c` load Nouveau under `mmiotrace` first | - |

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

A second client is `nvidia-persistenced` (active). If `attach` still
fails after the X change, stop it: `sudo systemctl stop nvidia-persistenced`.

## Procedure

First use, in this order. Stop at the first step that fails.

1. `scripts/passthrough.sh status` (no root). The card must be on
   `nvidia` and in its own IOMMU group.
2. `sudo scripts/passthrough.sh prepare-xorg`, then log out and in. Run
   `status` again: no X client on the card.
3. `~/llm-server/llm-mode.sh one`. The model moves to the card at
   03:00.0. `status`: no compute process on 04:00.0.
4. `sudo scripts/passthrough.sh attach`. The card is on `vfio-pci`.
5. `tools/guest/linux-run.sh --gpu ./run_test.sh --k40c`. Expected in
   `out/RESULT.txt`: `renderer:` names NVF1 or Nouveau, and `PASS`.
6. Copy the logs out before the guest stops, or run the guest with a
   shell (`tools/guest/linux-run.sh --gpu`) and use
   `scp -P 2222 -i ~/haiku-cross/linux-guest/id_guest dev@127.0.0.1:files/out/* reference/linux-run/`.
7. `sudo scripts/passthrough.sh detach`, then `~/llm-server/llm-mode.sh
   dual` (or `two`).

The model has one card while the other is attached: one agent session,
not two.

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
