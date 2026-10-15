# Plan for milestone S1

First draft by the scaffold 2026-10-13. Rewritten 2026-10-16 to record the
plan as it now stands, after the external reviews and the five research
documents in `docs/external/`, and after reading the `haiku-k40c-llm`
package. For the user's review and the third opinion. No hardware task of
this plan starts before the user says so.

## What S1 is

The card accepts a command from a driver running in Haiku. Proof: we
create one channel, put one no-operation command in its queue, and the
card's read pointer moves to our write pointer, with no fault reported
and a clean teardown.

The command is the host no-operation, method `0x08` of the channel class
Nouveau uses for this chip. Our encoder produces the two words
`0x20010002 0x00000000`, which match NVIDIA's class header and the
research (`docs/external/`, S1 unknowns).

S1 needs no graphics engine and no firmware. It needs the card awake, its
memory manager working, and its command scheduler running.

## What changed since the first draft

**1. The card is not initialised when a guest starts.** The Linux driver
notices this (bit 1 of register `0x02240c` is 0,
`nvkm/subdev/devinit/gf100.c:101`) and runs the start-up scripts stored in
the card's firmware chip ("devinit"). The debug reference run
(`reference/linux-run-debug/`) has 2,232 log lines of it: 598
instructions, 560 executed and 38 skipped, 24 kinds. So bring-up is
required, and it comes first.

**2. No flat replay of the recorded writes.** The first draft proposed
to replay the writes from the Linux log. The reviews (`docs/external/`,
findings C1 to C4) showed why that is unsafe: the scripts read the card's
state and branch on it, wait on conditions, and write to board devices
(GPIO lines, I²C devices). A replay copies one run's choices without
checking that they still apply. The plan is now an **executor** that
interprets the script, built from three sources: NVIDIA's published
devinit specification, Nouveau's interpreter, and the envytools decoder.
Where they differ, the difference is recorded and Nouveau's behaviour is
followed.

**3. A readiness ladder.** The "initialised" bit is set by the script
itself, so it proves nothing on its own. Each step up the ladder has an
independent check (identity, then memory size and a small memory test,
then the scheduler state), and an explicit statement of the state the
card must be in before the step starts.

**4. The `haiku-k40c-llm` package** (the application side, built
separately) showed llama.cpp running natively on Haiku on the CPU. For
this plan it adds three things: reuse its persistent Haiku installation
for the guest tooling, but with KVM (it ran under software emulation);
compile GPU kernels on Linux through Mesa and ship the binaries, as we did
once for the first shader, instead of porting the compiler into Haiku;
and a timed matrix product as the decision point after S3 (see the end).

## The work, in three tracks

"Local" is the local agent; "me" is the scaffold (review, design,
interpretation). A track A or C step that writes to the card is run only
after review, and only with the user's go-ahead.

### Track A: card bring-up (the critical path)

| # | Work | Who | Card? | State |
|---|---|---|---|---|
| A1 | Capture the card's firmware image in the Linux guest, with checksum | Me | Read-only guest run | **Done** 2026-10-14 (`reference/vbios/README.md`) |
| A2 | Build the independent decoder; decode the tables and scripts offline | Me | No | **Done** 2026-10-14 (envytools `nvbios`, see `reference/vbios/README.md`) |
| A3 | Inventory of the script instructions, matched to the driver log (executed or skipped) | Local | No | **Stopped, not accepted** 2026-10-15. To rework, after the checker is locked down. |
| A4 | Executor design from the three sources; differences recorded | Me | No | Not started |
| A5 | Board-table lookup of every I²C and GPIO target; the safety list | Me, then the user | No | **List done** (`docs/BOARD-OPERATIONS.md`); **decision pending** |
| A6 | Executor code, with host tests for changing conditions, timeouts and skipped writes | Local | No | Not started |
| A7 | First write experiment: bring-up, with independent readiness checks and a small memory test | Reviewed, then run | Yes | Not started |

### Track B: Haiku side (independent of A until the end)

| # | Work | Who | Card? | State |
|---|---|---|---|---|
| B1 | Fix the seven code defects of the external review and the comparison tool, with regression tests | Local | No | **Done** 2026-10-14 (task R1) |
| B2 | The layer between the encoders and the hardware: host memory, card memory, address mapping, publishing bytes to the card | Me (interfaces), local (code) | No | Not started |
| B3 | Haiku backend, adapted from Haiku's in-tree drivers: find the card, map its regions, allocate, time, log, clean up | Local | Guest without card | Not started |
| B4 | Guest tooling: a start script with limits the host enforces, a runtime allow-list of registers, logs saved as the run goes. Reuses the `haiku-k40c-llm` installation, with KVM | Me | No | Not started |
| B5 | Read-only stages on the card: identity, then a survey compared with the Linux trace | Local, run by me | Read-only | Not started |

### Track C: from "awake" to S1

| # | Work | Who | State |
|---|---|---|---|
| C1 | Decode the load phase of the Linux trace into named steps | Local tool, my interpretation | Not started |
| C2 | One ordered recipe: master control, working memory through the slow window, address translation, scheduler set-up, channel, runlist, submission, teardown. Each step with its address domain, wait, error test and rollback | Me | Not started |
| C3 | Implement and host-test each step; then one reviewed card experiment per stage that writes to the card for the first time | Local, then reviewed | Not started |

Facts already established for track C, from the reference runs
(`docs/05-fifo-design.md`, "Verified by the reference run"): the host
flush page is set before the card's start-up; bootstrap uses the slow
window (`0x1700` / `0x700000`); big pages are 128 KiB; the chip has three
command-fetch units (mask `0x7`) and needs no doorbell; a runlist entry is
the channel number followed by 0, and the runlist is started by a write
to `0x002634`.

### Housekeeping

- Rebuild the review package so that every check in it can be rerun.
- The third opinion (an outside review) before any hardware task.

## How the old stages map to the tracks

| Old stage (first draft) | Now |
|---|---|
| E0 tooling, guest with the card | B4 |
| E1 driver skeleton, read identity | B3 + B5 |
| E2 read-only survey | B5 |
| E3 decode the load phase | C1 |
| E4 bring-up by replay | A4, A6, A7 (executor, not replay) |
| E5 master control, memory, address translation | C2, C3 |
| E6 scheduler, channel, runlist | C2, C3 |
| E7 one command | C3, ending in S1 |

## Limits for the agent starting the guest with the card

The user decided on 2026-10-13 that the agent may start the Haiku guest
with the development card. These limits apply, and are enforced by the
host where possible (B4):

- Only through one script written by the scaffold. The agent cannot
  change the script or its virtual-machine options.
- Only the development card (`0000:04:00.0`), only while it is bound to
  `vfio-pci`. The other card and the display card are never touched. The
  script refuses anything else.
- One guest at a time, with a time limit (10 minutes), then it is powered
  off. The card is reset at each start.
- Only a driver build whose allow-list test passed on the host. The build
  carries its stage, and the driver refuses writes outside the ranges of
  that stage.
- Never: writes to fan, voltage or firmware-chip registers. Clock and
  memory-controller writes only when they come from the card's own
  start-up script through the executor, never from our own numbers.
  Board operations in the script (GPIO, I²C) only as the user decides on
  `docs/BOARD-OPERATIONS.md`.
- Every run saves its log. A hang or a panic is recorded, and the agent
  stops and reports instead of trying again with changes.
- Stages that write to the card for the first time (A7, and each first
  write in C3) are started by the scaffold after review, not by the agent
  on its own.

## The unknowns

**Could stop or reshape S1**

1. Does the scheduler run a command while the graphics engine is left
   uninitialised? Nothing shows that it does in that state. Only the card
   can answer. If not, S1 needs part of the engine start-up first.
2. Does our executor bring the card up from the guest's reset state? It
   depends on the script's conditions, timing, and the set-up Nouveau
   does before the scripts run.
3. How do we know bring-up worked? Independent checks are needed (the
   readiness ladder); they are not all identified yet.
4. What do the I²C and GPIO operations control? Answered for most of
   them in `docs/BOARD-OPERATIONS.md`; the device at I²C address `0x20`
   is still unknown. The safety decision is the user's.

**Would cost time, not stop it**

5. Whether memory addresses handed to the card from Haiku in a guest are
   the ones the card must use. Needs one early test.
6. Whether the slow window works before address translation exists, as
   the source suggests.
7. Whether a bus reset at guest start returns the card to a known state,
   and whether it affects anything else on the host.
8. Which page-size setting and which cache flushes the S1 path needs.
9. The meaning of some words in the channel's control block. We can write
   Nouveau's values, but each address and mask in them must be ours.

**Housekeeping**

10. The reference run used kernel 6.8, our source tree is 6.12, and some
    research used newer source. Differences must be checked where we rely
    on them.
11. Whether Haiku in the guest can map the card's large memory regions.
    Tested in the first read-only stage (B5).

## After S1

Not in this plan: interrupts (S1 is shown by polling), the copy engine
(S2), the graphics engine and its firmware (S3), power management,
running on bare metal.

For S3, `output[i] = input[i] + 1` stays the first proof. A second proof
is added: one single-precision matrix product on the card, checked
against the CPU and timed. That is the first moment the speed question of
the whole project (whether a Haiku backend can beat the CPU) can be
answered with a measurement, so it is the go / no-go point before the
larger work of a kernel library and model coverage.
