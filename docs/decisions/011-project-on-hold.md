# 011. Put the driver project on hold after S1

Date: 2026-10-31. Status: accepted (user instruction: "write the status of the
driver project as on hold").

## Context

S1 passed on 2026-10-31 (`results/20261031-batch1-a7-bar1-d198d424/`). A native
Haiku driver ran the card's start-up script, reached VRAM through its own BAR1
page tables, and one channel on the CE0 runlist consumed one host NOP. No fault
occurred, and the teardown was clean. The user said before: "Complete S1, then we
archive."

## Decision

1. The project is on hold. No task is active. No card run is approved.
2. The repository keeps its state: `main`, the evidence in `results/`, the task
   log and the open questions. Nothing is deleted.
3. The lessons go to the shared skills (`claude-skills/hardware-bringup`,
   `claude-skills/local-agent-scaffold`) and to `optima-agent-bench`
   (`docs/long-tasks-and-grader-access.md`).

## State at the hold

| Item | State |
|---|---|
| S1 | PASS, HARDWARE_VERIFIED for this card under Haiku |
| S2 (copy) | Not started. Needs the copy-engine class set-up on the S1 channel and Q7. |
| S3 (compute) | Not started. Needs GR, FECS/GPCCS firmware and a GR context. |
| Q7, Q11 | OPEN (`docs/OPEN_QUESTIONS.md`) |
| Approvals | Decisions 004 to 010 stay as records. They do not approve a new run. |

## To resume

1. Read `docs/STATUS.md`, this record and `docs/S1-PLAN.md`. If the card is with `llm-server`, switch it to mode `one` and attach the card first (see "The card during the hold").
2. Ask the user for a new approval before any card run (decision 008).
3. After a host reboot, the user restores VFIO access
   (`sudo scripts/passthrough.sh attach`) and starts the filtered journal stream.
4. Build a new single-use package and rehearse it without the card first.

## The card during the hold

The user returns 0000:04:00.0 to the host `nvidia` driver and to `llm-server`
in a dual-card mode (router boot mode). The user steps:

1. Stop the filtered journal stream.
2. `sudo scripts/passthrough.sh detach`: removes the boot-time reservation
   (`/etc/modprobe.d/k40c-vfio.conf` and the initramfs hook), rebuilds the
   initramfs and binds the card to `nvidia`.
3. `~/llm-server/llm-mode.sh dual-t1k`, then
   `LLM_BOOT_MODE=router recovery/recover.sh services` in `~/llm-server`.

To resume driver work, first switch `llm-server` to mode `one`, then attach
the card again (`docs/PASSTHROUGH.md`). Push `main` and delete the old remote
task branches if wanted.
