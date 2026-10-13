# Plan for milestone S1

Draft by the scaffold, 2026-10-13. For the user's review and the third
opinion. No task of this plan starts before the user says so.

## What S1 is

The card accepts a command from a driver running in Haiku. Proof: we
create one channel, put one entry in its command queue, and the card's
read pointer moves to our write pointer, with no fault reported.

S1 needs no graphics engine and no firmware. It needs the card awake,
its memory manager working, and its command scheduler (FIFO) running.

## A finding that changes the plan

The reference run with the driver's debug log shows something the
earlier analysis missed: **when a guest starts, the card is not
initialised.** The Linux driver notices this (bit 1 of register
`0x02240c` is 0, `nvkm/subdev/devinit/gf100.c:101`) and runs the
start-up scripts stored in the card's own firmware chip. The log has
2,232 lines of that script running. It sets up clocks and memory
before anything else can work.

`analysis/min_chain.md` lists this step ("devinit") as optional. For a
card in a guest it is required. On a bare-metal machine the PC firmware
may do it at power-on for a primary card; for our card in a guest
nobody does it for us.

Consequences:

- The Haiku driver must bring the card up before S1 can start. This is
  new work, and it comes first.
- The scripts write to clock and memory-controller registers. Those
  are among the registers the safety rules meant to keep the driver
  away from. The rule becomes: such writes are allowed only when they
  come from the card's own script, never from our own numbers.
- Two ways to do it. (A) Port Nouveau's script interpreter (about
  2,300 lines of C that read the script from the firmware chip and
  execute it). (B) Replay: the debug log records every register write
  the script made on this exact card; a first driver can send the same
  writes in the same order. B is much smaller and good enough to reach
  S1 on this card; A is the correct long-term answer. The plan starts
  with B and records A as later work.
- Risk of B: the script has conditions that read the card's state. On
  the same card after the same reset they should take the same path,
  and the log shows which path was taken, but this is an assumption
  until tested. The test is cheap: replay, then compare a trace of our
  run with the Linux trace.

## How much of the path is proven

| Step toward S1 | Basis |
|---|---|
| Find the card, map its registers, read its identity | Seen on the card (identity value recorded) |
| Bring the card up from reset (start-up scripts) | Seen on the card under Linux (full log of the writes); not yet tried by us |
| Master control: switch on the units | From the source and in the trace; not yet decoded step by step |
| Memory: size, working memory (instance memory), address translation | Modelled from source; formats tested on the host; the trace has the writes but they are not decoded |
| Command scheduler set-up: 3 units, the enable mask | Seen on the card (values recorded) |
| Create a channel, bind, start, put it on the runlist | Seen on the card (values recorded) |
| Tell the card about a new entry (write pointer; no doorbell on this chip) | From the source; done by user space in the reference run, so not in the trace |
| Read the card's read pointer back | From the source |

The middle rows are the weakest part. Before code is written for them,
the load phase of the trace must be decoded the way the job phase was.

## Stages

Each stage ends with a result that can be checked, and the earlier
stages only read from the card.

| Stage | What | Writes to the card? | Proof |
|---|---|---|---|
| E0 | Tooling: a script that starts the Haiku guest with the card, under the limits below; a register allow-list in the driver; a way to get the driver's log out | No | The guest starts and stops; Haiku sees the device |
| E1 | Driver skeleton: find the card, map registers, read the identity register | No | The value equals the recorded one (`0x0f1240a1`) |
| E2 | Read-only survey: read the registers that say whether the card is initialised and how much memory it has; compare with what Linux read at the same point | No | Values equal the Linux trace |
| E3 | Decode the load phase of the Linux trace into named steps (host work, no card) | No | A step table like the one for the job, checked against the trace |
| E4 | Bring-up by replay of the start-up script writes | Yes, script writes only | The "initialised" bit is set; a trace of our run matches the Linux trace for this part |
| E5 | Master control, timer, memory, working memory, address translation | Yes | Each sub-step compared with the Linux trace |
| E6 | Command scheduler set-up, one channel, runlist | Yes | The channel state register reads "enabled"; values match the recorded ones |
| E7 | One command-queue entry | Yes | S1: the read pointer equals the write pointer, no fault pending |

E3 can start now: it is host work. E0 and E1 can be prepared on the
host and in the Haiku guest without the card.

## Limits for the agent starting the guest with the card

The user decided on 2026-10-13 that the agent may start the Haiku guest
with the development card. Proposed limits:

- Only through one script written by the scaffold. The agent cannot
  change the script or its virtual-machine options.
- Only the development card (`0000:04:00.0`), only while it is bound to
  the guest driver. The other card and the display card are never
  touched. The script refuses anything else.
- One guest at a time, with a time limit (10 minutes), then it is
  powered off. The card is reset at each start.
- Only a driver build whose allow-list test passed on the host. The
  build embeds the stage number, and the driver refuses writes outside
  the ranges of that stage.
- Never: writes to fan, voltage or firmware-chip registers; clock
  registers only from the replay table of stage E4.
- Every run saves its log. A hang or a panic is recorded and the agent
  stops and reports instead of trying again with changes.
- Stages that write to the card for the first time (E4, E5, E6, E7) are
  started by the scaffold after review of the previous stage, not by
  the agent on its own.

## What could stop S1

- The replay does not bring the card up (a script condition takes a
  different path). Then the interpreter must be ported first: weeks,
  not days.
- Haiku in the guest cannot map the card's large memory regions or
  deliver its interrupts. Tested in E0 and E1.
- A step in the middle rows needs something not yet understood. E3 is
  there to find this before code is written.

## Not in this plan

Interrupts (S1 is shown by polling), the copy engine (S2), the graphics
engine and firmware (S3), power management, running on bare metal.
