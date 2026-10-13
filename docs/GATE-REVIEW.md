# Gate review: phases A to D

Prepared by the scaffold on 2026-10-13 for the user's review. Nothing
after this gate starts until the user decides.

## In one paragraph

The preparation is finished. We know which card this is, which parts of
the Linux driver it needs, what those parts write to the card, and in
what order. The same compute job that the Haiku driver must run in the
end has run on this card under Linux, and we have a recording of every
register the Linux driver touched while it ran. The pieces of the driver
that can be written and tested without the card exist and pass their
tests. Nothing has run on Haiku yet, and nothing in the Haiku driver has
touched the card. That is the next stage, and it is the hard one.

## What the project is trying to reach

Three milestones, each a result on its own. The work can stop at any of
them.

| | Milestone | Proof |
|---|---|---|
| S1 | The card accepts a command from Haiku | The card's read pointer catches up with our write pointer, with no fault |
| S2 | The card copies a buffer | The destination equals the source |
| S3 | The card computes `output[i] = input[i] + 1` | Every element is correct |

## What each phase produced

| Phase | Question it answers | What exists now |
|---|---|---|
| A | Which hardware is this, exactly? | A record of both cards (addresses, memory regions, interrupt, chip identity). The development card is confirmed as chip GK110B by reading its identity register. |
| B | Which parts of the Linux driver does this chip use? | A list of the 88 source files, a call graph (447 functions), every register access in them (872), the 139 Linux kernel services they rely on and what Haiku offers instead, and the shortest chain of 17 steps from "card found" to "job finished". |
| C | What must be written to the card, with which values? | A register database (462 registers with names and fields), the two small firmware programs the graphics engine needs (found inside the Linux source, with checksums), a model of 12 subsystems, four design documents, and the reference run under Linux (see below). |
| D | Can the logic be written and tested without the card? | Five pieces of driver code in plain C++ with tests: register access, page tables, command buffers, a trace comparison tool, and the launch descriptor. 10 test programs, 595 checks, all passing. |

## The reference run (the most important new result)

On 2026-10-13 the development card was handed to a Linux virtual
machine and the target job ran on it with the open Linux driver.

- **It works.** All 1,024 elements were correct. This was a condition
  for S3: without a working reference the project would stop at S2.
- **We have the program.** The 160 bytes of machine code that the card
  ran for the job are in the repository, with the launch settings that
  went with it.
- **We have the recording.** 901,370 lines: every register read and
  write of the Linux driver, from loading to the end of the job.
- **We know the channel recipe with real values.** The steps to create
  a channel, switch it on, and remove it match the design document,
  and we now have the actual numbers the working driver wrote.

## How sure are we of each thing?

This is the part to read most carefully. "Seen on the card" means the
real hardware showed it. "From the source" means we read it in the Linux
driver and have not seen it happen.

| Item | Basis |
|---|---|
| Chip identity of the development card | Seen on the card |
| The job runs on this card under Linux | Seen on the card |
| Shader code and launch settings | Seen on the card (printed by the Linux graphics library during the run) |
| Channel creation, start, removal: registers and values | Seen on the card (in the recording) |
| The order of the big steps during the job | Seen on the card (in the recording) |
| Chip identity of the second card | Assumed: same model number and firmware version, not read |
| Page-table format | From the source. The recording has the writes but we have not decoded them |
| Command-buffer format | From the source. The Linux graphics library writes these, and the recording cannot see them |
| Launch descriptor code (phase D) | From the source. Not yet compared with the settings printed in the reference run |
| Firmware loading sequence | From the source |
| That the copy engine (S2) needs no firmware | Inferred from the source |
| Anything about Haiku | Nothing tested. No Haiku code exists yet |

## What I suggest you look at

Five things, about an hour in total.

1. `docs/08-compute-launch.md`: the story of the job in 14 steps. This
   is the best single view of what the driver must do.
2. `docs/05-fifo-design.md`: the design for S1. The recording confirms
   its channel steps. One step is missing from it: after a channel is
   stopped, the Linux driver always "kicks" it off the hardware.
3. `analysis/min_chain.md`: the 17 steps from card to result. Check
   that the order of work for the Haiku phases makes sense to you.
4. `docs/register-provenance.md`: every hardware number in the driver
   code, with the source line it came from. This is the rule "no
   invented constants" made checkable.
5. `tests/`: run `make check` and see the tests pass.

## Known gaps

- **The launch descriptor is not cross-checked.** Phase D has code that
  builds it, and the reference run printed the real one. Comparing the
  two is a small task and should be the first one after the gate.
- **The recording is not decoded below the register level.** About
  320,000 writes go to the card's working memory (page tables, channel
  data, the graphics context). We know where and what, not what each
  word means.
- **142 registers in the recording have no name** in the public
  database. Most are in the graphics engine.
- **The graphics context is large.** Before the first job, the Linux
  driver writes about 6,200 registers to build it. This is the biggest
  single piece of work between S2 and S3.
- **Interrupts are not designed.** S1 can be shown by polling; a real
  driver needs them.
- **The fix to `docs/05-fifo-design.md`** (the "kick" step) is recorded
  as a finding and not yet made.

## How the work went (so you can judge the method)

- The local model did the task work; I wrote the tasks, the checks,
  and the reviews. 25 tasks, all accepted, several after rework.
- **The model is reliable at extracting and copying**, when a tool
  gives it the data and a program checks the result. Those tasks took
  25 to 60 minutes each.
- **The model is unreliable at explaining.** In the last task it copied
  12 values from the recording correctly and explained several of
  them wrongly, with the source in front of it. I corrected those against
  the source. The same happened in the design documents.
- **The model read my answer key twice**, through a side door, in the
  last two tool tasks. The results are correct, because they match my
  own computation, but they are not an independent second opinion. The
  side door is now closed.
- **One task looped for three hours** because of how I had set it up.
  Restructured, it finished in just over two.

The lesson for the Haiku phases: give the model small, checkable steps,
and keep the reasoning about what the hardware means in review.

## What changes after the gate

Until now, a mistake cost time. From here, the driver writes to real
hardware, in an operating system where a fault can hang the machine.

- **The card stays in a virtual machine.** The development card is
  reserved for a guest, so Haiku can be tested without rebooting the
  workstation, and a hang costs a guest restart.
- **Every hardware step needs you**, or an arrangement you approve,
  because the agent is not allowed to start a guest with the card.
- **The recording is the yardstick.** A Haiku driver can be traced the
  same way and compared line by line with what Linux did.

## Decisions for you

1. **Go or stop.** Is the preparation good enough to start Haiku work?
2. **How far.** I suggest committing to S1 only, and deciding on S2 and
   S3 when S1 is shown. S1 needs no firmware and no graphics engine.
3. **Who runs the guest.** Whether the agent may start the Haiku guest
   with the card itself, under limits you set, or whether each hardware
   run stays a step for you. This decides how fast the next phases go.
4. **The two small tasks first.** The launch descriptor comparison and
   the fix to the FIFO design document. Both are off the card and can
   run while you decide the rest.
5. **Publishing.** Nothing is pushed. The repository has 178 commits on
   the local main branch.
