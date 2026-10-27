# Plan for milestone S1

First draft by the scaffold 2026-10-13. Rewritten 2026-10-16 to record the
plan as it now stands, after the external reviews and the five research
documents in `docs/external/`, and after reading the `haiku-k40c-llm`
package. The user accepted the board-operation decisions and waived further outside
review in [ADR 004](decisions/004-board-operations-and-review.md).
Every card stage still requires the user's go-ahead.

## What S1 is

The card accepts a command from a driver running in Haiku. Proof: we
create one channel, put one no-operation command in its queue, and the
card's read pointer moves to our write pointer, with no fault reported
and a clean teardown.

The command is the host no-operation, method `0x08` of the channel class
Nouveau uses for this chip. Our encoder produces the two words
`0x20010002 0x00000000`, which match NVIDIA's class header and the
research (`docs/external/`, S1 unknowns).

S1 aims to omit graphics-engine initialization and GR context-switch
microcode; scheduling in that state remains unverified (unknown 1 below).
It still depends on the card's VBIOS initialization program, working memory
management and command scheduling. Do not describe this as "no firmware".

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

## S1 documents

| Document | Role |
|---|---|
| This file | Plan, tracks, limits and unknowns. The latest scaffold review. |
| [S1-RECIPE.md](S1-RECIPE.md) | Step-by-step recipe for the card stages |
| [S1-VERIFICATION.md](S1-VERIFICATION.md) | Verification gates and their results |
| [BOARD-OPERATIONS.md](BOARD-OPERATIONS.md) | Board operations and the accepted ADR 004 limits |
| [DEVINIT-EXECUTOR.md](DEVINIT-EXECUTOR.md) | Design of the semantic start-up script executor |
| [MEMORY-CONTRACT.md](MEMORY-CONTRACT.md) | Memory ownership and publication boundary |
| [PASSTHROUGH.md](PASSTHROUGH.md) | How a VM gets one K40c (user step) |
| [ABC-CARDLESS-OUTCOME.md](ABC-CARDLESS-OUTCOME.md) | Cardless A/B/C results and native gate commands |
| [GATE-REVIEW.md](GATE-REVIEW.md) | Gate review package for phases A to D |
| [history/20261020-s1-plan-reviews.md](history/20261020-s1-plan-reviews.md) | Earlier reviews of this plan |

## Scaffold review 2026-10-21

Steps 1 and 2 of the list above. Host only, no card, no VM. The user
directed that code fixes go to the local agent: the scaffold wrote the
task texts (`docs/tasks/S1A.md`, `S1B.md`) and the acceptance test
`tests/accept/s1a_accept.cpp`. Findings and their state:

| # | Item | Finding | Evidence | State |
|---|---|---|---|---|
| F1 | Executor, opcode 0x7a | Nouveau sets bit 0 when ZM_REG writes `0x000200`; our core does not. The ROM writes `0x00002020` there (0x8638); our core would clear bit 0 of the master enable register | `init.c:1901-1902`; trace line 45511 writes `0x2021` (TRACE_VERIFIED) | Fixed in S1A (2026-10-23). `s1a_accept` 8 of 8 |
| F2 | Executor, other 24 opcodes | Lengths, operand offsets, masks (`(old & keep) \| value`), flag model, CONDITION_TIME, TIME, RAM group, MACRO, copy/shift agree with Nouveau. Known fail-closed differences (zero-count REPEAT, END_REPEAT outside a loop, DONE in a repeat, shift ≥ 32) are documented | `init.c:55-82,182-212,479-536,610-2225` | Accepted |
| F3 | Executor, IO when skipped | Correct to call the helper for a skipped IO: Nouveau's two 10 ms waits in `init_io` run even when skipped; only the writes are gated | `init.c:1638-1655`, `init_wrport` 221-225 | Accepted; the helper must keep this |
| F4 | Executor cites | 0x91 dispatch is `init.c:2290`, not 2289 | dispatch table | Fixed in S1A (2026-10-23) |
| F5 | Bootstrap cites | `nv50.c` cites are 2-3 lines off (masks 62-63/81-82, selector 68/88, data 71/91). Values and code are right | `instmem/nv50.c` | Fixed in S1A (2026-10-23) |
| F6 | Bootstrap encodings | Slow window 44-bit masks, BAR flush `0x070000` bit 1, runlist `0x002270`/`0x002274`, pending `0x002284+id*8` bit 20, aperture 0/3, ID ≤ 15 all agree | `g84.c:29-40`, `gk104.c:77,426,438-447` | Accepted |
| F7 | Recipe, preemption | GK110 uses `gk110_chan_preempt`: a channel in a hardware group is preempted as a group (`0x01000000 \| id`). The recipe cited only gf100 | `gk110.c:36-46,57,61-64` | Fixed in `docs/S1-RECIPE.md` |
| F8 | Recipe, other cites | Flush page `0x100c10`, slow window, BAR flush, runlist cites verified | `fb/gf100.c:83` and above | Accepted |
| F9 | Haiku probe, B5 gap | The K40c probe prints any identity and reports PASS; `0xffffffff` (BAR not answering) would pass. Haiku's nvidia driver turns on memory decode before mapping; ours writes no PCI config (correct for B5) but does not check it | `driver.c:543-550`; `hardware/record.json:37` (`0x0f1240a1`) | Fixed in S1A (2026-10-23) (read command register, refuse if decode off, compare identity) |
| F10 | Haiku backend | BAR high word, page bounds, read-only map, cleanup on failure correct. Host allocation is `B_CONTIGUOUS`, not `B_32_BIT_CONTIGUOUS` as Haiku's nvidia driver uses; matters for B2, not B5 | `driver.c:674-695,939-957` | Note for B2 |
| F11 | Memory layer | No hardware constants. Ownership, publication, pin and quarantine rules hold | `src/memory/` | Accepted |
| F12 | A3 inventory | Counts 598/560/38, 24 names, 7 scripts agree with the plan and RESULT. The IO at 0x8506 (port `0x3c3`, data 1) ran in the Linux run, and its register writes are in the trace | trace lines 45579-45594 (TRACE_VERIFIED) | Accepted; input for board decision 5 |
| F13 | Restore helper | `--check` says "clean" for a sparse cache that lacks a file a tool needs. Its `SOURCES` lists also differ from the real caches (nouveau, envytools, mesa) | `git sparse-checkout list` of each cache | Fixed in S1B (2026-10-23) |
| F14 | `devinit_sources.py` | Needs `nvbios/nvbios.c`; the full checkout `~/haiku-cross/src/envytools` is at the pin and its hash equals the recorded one. The scaffold's private fix passes `--check` with no change to the output | `analysis/devinit_sources.json` | Fixed in S1B (2026-10-23). Note added to `reference/MANIFEST.md` |

**Next steps, in order.**

1. S1B5 is accepted by Claude Code (2026-10-27). See work/S1B5/REVIEW.md.
2. Implement the host-only board-operation policy and helpers under ADR 004.
   Allow only its specified ROM and observed operations. Deny other operations.
3. Complete B2 allocation and mapping, A4 pre-start state, and the C2 choices.
4. Start A7 only after the user's go-ahead. First writes in C3 also need that approval.

Work uses only main. Related host macro tasks may share a review batch (ADRs 005 and 007).
No further outside review is required. The reviewed hardware integration gate remains for the executor.

S1A and S1B host work is complete. The 2026-10-26 checks and probe links
passed (`docs/STATUS.md`). B5 identity passed on 2026-10-27.
KNOWN / HARDWARE_VERIFIED: PMC_BOOT_0 was `0x0f1240a1` under Haiku
(`results/20261027-b5-identity/attempt-02/serial.log`). No write stage has run.

## Requirements carried from the S1B5 review

Claude accepted S1B5 on 2026-10-27. After any launcher-reported stop,
report and ask before another run, including a later-diagnosed false alarm (ADR 006).

Before A7, prove that write-stage startup runs once per guest boot despite devfs reloads.
The B5 probe ran twice. Its read-only behavior does not establish safe repeated initialization.

KNOWN: B5 observed PCI command `0x0007`, including the bus-master enable bit.
Sources: `results/20261027-b5-identity/attempt-02/serial.log:902` and
`reference/haiku/headers/os/drivers/PCI.h:686`.
INFERRED: Haiku or VM firmware enabled it before the probe. The source is unverified.
Account for the enabled bit in B2 and A7. B5 proves no DMA or IOVA correctness.

## The work, in three tracks

Codex implements the remaining host work. Claude Code reviews it.
The user decided board policy and outside review in ADR 004.
Each card stage still needs user approval.
Completed rows name their historical contributor. Other Who entries assign
responsibility for remaining work and its review.

### Track A: card bring-up (the critical path)

| # | Work | Who | Card? | State |
|---|---|---|---|---|
| A1 | Capture the card's firmware image in the Linux guest, with checksum | Historical scaffold | Read-only guest run | **Done** 2026-10-14 (`reference/vbios/README.md`) |
| A2 | Build the independent decoder; decode the tables and scripts offline | Historical scaffold | No | **Done** 2026-10-14 (envytools `nvbios`, see `reference/vbios/README.md`) |
| A3 | Inventory of the script instructions, matched to the driver log (executed or skipped) | Independent rework (A3) | No | **Reworked** 2026-10-16; observed inventory passes checks. Raw-ROM structural supplement covers 530 potential starts / 25 opcodes; see `docs/ABC-CARDLESS-OUTCOME.md`. |
| A4 | Executor design from the three sources; differences recorded | Codex, Claude Code review | No | Source cross-reference/design drafted; production helper/preinit integration still pending (`docs/DEVINIT-EXECUTOR.md`) |
| A5 | Board-table lookup of every I²C and GPIO target; the safety list | Codex implementation, Claude Code review | No | **List done** (`docs/BOARD-OPERATIONS.md`); **decisions accepted** 2026-10-27 (ADR 004) |
| A6 | Executor code, with host tests for changing conditions, timeouts and skipped writes | Codex, Claude Code review | No | Host core implemented: 20 core + 5 default-denied helpers; synthetic and artificial real-ROM tests pass. Not a production executor |
| A7 | First write experiment: bring-up, with independent readiness checks and a small memory test | Claude Code review, user-authorized run | Yes | Host scratch-check algorithm tested; no card experiment performed |

### Track B: Haiku side (independent of A until the end)

| # | Work | Who | Card? | State |
|---|---|---|---|---|
| B1 | Fix the seven code defects of the external review and the comparison tool, with regression tests | Historical local agent (R1) | No | **Done** 2026-10-14 (task R1) |
| B2 | The layer between the encoders and the hardware: host memory, card memory, address mapping, publishing bytes to the card | Codex, Claude Code review | No | Typed ownership/publication layer implemented/tested; real allocation/VMM/visibility adapter pending |
| B3 | Haiku backend, adapted from Haiku's in-tree drivers: find the card, map its regions, allocate, time, log, clean up | Codex, Claude Code review | Guest without card | OS backend/probes cross-compile; host failure tests pass. Matching-kernel cardless link/load passed (ESC-001). S1A cardless rerun passed 2026-10-27 |
| B4 | Guest tooling: a start script with limits the host enforces, a runtime allow-list of registers, logs saved as the run goes. Reuses the `haiku-k40c-llm` installation, with KVM | Codex, Claude Code review | No | Cardless overlay/watchdog/logging runner implemented; current probe allows identity reads only. Cardless KVM native load passed (ESC-001). S1A rerun and B5 identity passed 2026-10-27. Write-stage allow-lists pending |
| B5 | Read-only stages on the card: identity, then a survey compared with the Linux trace | Codex, Claude Code macro review | Read-only | Identity passed 2026-10-27 (S1B5, HARDWARE_VERIFIED). Register survey remains pending |

### Track C: from "awake" to S1

| # | Work | Who | State |
|---|---|---|---|
| C1 | Decode the load phase of the Linux trace into named steps | Codex, Claude Code review | Six source anchors + chronological domain survey generated; full semantic attribution remains partial |
| C2 | One ordered recipe: master control, working memory through the slow window, address translation, scheduler set-up, channel, runlist, submission, teardown. Each step with its address domain, wait, error test and rollback | Codex, Claude Code review | Gated integration recipe prepared (`docs/S1-RECIPE.md`); unresolved MMU/helper/routing/quiescence choices explicit |
| C3 | Implement and host-test each step; then one reviewed card experiment per stage that writes to the card for the first time | Codex, Claude Code review | Slow window, BAR flush, runlist, scratch and S1 controller host-tested/cross-compiled; full backend/channel/MMU integration and hardware experiments pending |

Facts already established for track C, from the reference runs
(`docs/05-fifo-design.md`, "Verified by the reference run"): the host
flush page is set before the card's start-up; bootstrap uses the slow
window (`0x1700` / `0x700000`); big pages are 128 KiB; the chip has three
command-fetch units (mask `0x7`) and needs no doorbell; a runlist entry is
the channel number followed by 0. Runlist commit uses `0x002270` and
`0x002274`; `0x002634` is channel preemption, not runlist start
(`nvkm/engine/fifo/gk104.c:430-447`, `gf100.c:43-46`).

### Housekeeping

- Rebuild the local source/review artifacts with `tools/review_bundle.py`; reproduce checks using `docs/ABC-CARDLESS-OUTCOME.md` and exact external inputs. Firmware and caches are excluded.
- No further outside review is required (ADR 004). Claude Code reviews completed macro tasks.

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

ADR 005 permits the agent to start read-only Haiku stages with the development card. These limits apply, and are enforced by the
host where possible (B4):

- Use only the guarded card launcher. It accepts no additional QEMU options.
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
  Board operations in the script (GPIO, I²C) only within ADR 004's ROM and operation limits.
- Every run saves its log. A hang or a panic is recorded, and the agent
  stops and reports instead of trying again with changes.
- Stages that write to the card for the first time (A7, and each first
  write in C3) require review and the user's go-ahead. B5 read-only stages
  are authorized by ADR 005.

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
   remains UNKNOWN. ADR 004 permits the observed write within its stated limits.

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
