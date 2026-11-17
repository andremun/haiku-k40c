# S3DIAG continuation report (2026-11-17)

Purpose: give the next session all that it needs to continue the S3 compute test
after the three stops of 2026-11-16. No card run was made for this report. All
work was read-only: run records, the Linux reference trace, the pinned Nouveau tree.

## 1. Where the test stands

| Run | Content | Result |
|---|---|---|
| Rung 4, `s3a` | GR start, golden context, attach, no submit | PASS |
| Rung 5, `s3b` | Full compute job | STOP, AER CmpltTO on 0000:00:03.0 |
| `s3c` | Object bind only (2 push words) | STOP, same |
| `s3e` | Object bind, channel state as Linux (context copy, PRIV PTEs, user channel) | STOP, same |

Records: `work/LADDER/FINDINGS.md`, `work/S3DIAG/FINDINGS.md`,
`results/20261116-s3b-run-b4d27e59/`, `results/20261116-s3c-run-bcaef9f5/`,
`results/20261116-s3e-run-13c36b79/`.

## 2. New facts from this investigation

### 2.1 The stop is one BAR1 read. The state of BAR0 is unknown.

- KNOWN: after GP_PUT, `Compute::submit` makes only BAR1 reads of USERD GP_GET
  until the poll ends (`src/gr/Compute.cpp:275-281`). The clock is the host clock
  (`src/memnative/NativeIo.cpp:55-56`). No BAR0 access occurs in that loop.
- KNOWN: the two BAR1 reads before GP_PUT returned 0 (`Compute.cpp:270`; a wrong
  value prints a failure line, and none was printed). BAR1 worked until GP_PUT.
- KNOWN: QEMU stops the guest at the first AER report
  (`qemu.log`: `vfio_err_notifier_handler ... Unrecoverable error detected`), and
  the launcher then ends QEMU. Thus each run shows the first read that timed out
  and nothing after it.
- KNOWN: the `s3e` serial log ends with `k`, the first letter of a new
  `k40_mem:` line. The `s3c` log ends after the GP_PUT line. The next possible
  print is the 100 ms poll line or the status line.
- Correction to the earlier wording "the card stopped answering host reads":
  the evidence is "at least one BAR1 read got no completion within about 100 ms
  of GP_PUT". If BAR0 reads still work after that moment is UNKNOWN.
- KNOWN (source): Nouveau binds BAR1 again after an MMU fault of unit BAR1
  (`engine/fifo/gf100.c:573-577`, `subdev/bar/base.c:40-47`, unit table
  `engine/fifo/gk104.c:478`). INFERRED: a BAR1 path that is stalled by a fault
  gives exactly a read without completion, with BAR0 alive. Not verified.

### 2.2 The golden image was never checked on the card

- KNOWN: the only image data in a report is `GR_IMAGE`, the first 8 words. The
  `s3a` pass printed `GR_IMAGE 0 0 0 0 0 0 0 0`
  (`results/20261116-s3a-run-1fe37fd6/serial.log`).
- KNOWN: the Linux image also starts with zeros. The reference trace holds the
  full Linux channel context: 80514 writes to MAP 26 (0x4f000 bytes at BAR3
  0x8103a5000), lines 811578-892192 of `reference/linux-run/mmiotrace.txt.xz`.
  The first non-zero word is at offset 0x100 (0x0905090a, the value of 0x17e91c).
  56574 words are not zero. The last two writes are the list words (0x24, 0x37f0).
- Result: `PASS S3_GOLDEN` proves that the generation sequence ended without an
  error. It does not prove that the image has the correct content. A first
  context load from a wrong or empty image is a possible cause of the stop
  (INFERRED, not verified). The `s3e` copy reads the full image but records no
  content.

### 2.3 A first load runs firmware paths that golden generation never ran

Source: `reference/nouveau/nvkm/engine/gr/fuc/hub.fuc` (the FECS program that
the trace uploads; KNOWN in source, SOURCE_ONLY).
- Golden generation uses "set channel" (`ctx_chan`, lines 532-544) and then a
  save (`chsw_prev_no_next`, lines 255-263). It never loads a context.
- The first schedule of a channel takes `chsw_no_prev` (lines 264-269): a load
  with no save before it. That path runs, for the first time on our card:
  `ctx_redswitch` (lines 432-444, GR power and enable bits), `ctx_load`
  (lines 471-523), the load transfer on HUB, GPCs and strands (lines 630-664),
  then `ctx_mmio_exec` (lines 555-592).
- `ctx_load` reads 16 bytes at instance + 0x210 as VRAM and makes the context
  address from (word0 >> 8) | (word1 << 24) (lines 486-507). It then reads 256
  bytes of the context header through the channel address space.
- `ctx_mmio_exec` reads the register list through the channel address space,
  writes each pair, then writes the 256-byte header back with count 0
  (lines 584-591). The context must be writable.
- UNKNOWN: if the 2-word object bind makes PFIFO request this GR load at all.
  Linux's own first entry on the job channel was a bind of class 0x906e on
  subchannel 7, which PBDMA 0 answered with interrupt 0x00800000
  (`EMPTY_SUBC`, `engine/fifo/gf100.c:300-306`; trace lines 895451-895465).

### 2.4 Our FIFO stages for the GR runlist are not from the trace

- KNOWN: `fifo`, `bind`, `attach` and `teardown` in `tools/gr/program.py:171-199`
  are the S1 sequences rewritten for runlist 0 and PBDMA 0. Only `gating`,
  `start` and `golden` are compared with the trace. S1 and S2 ran on the CE0
  runlist. No stage ever consumed a GPFIFO entry on runlist 0.
- KNOWN differences from Linux on PBDMA 0 (trace lines 560983-561004): Linux
  writes 0x040108 = 0xffffffff, 0x04010c = 0xfffffeff, 0x04013c = 0xeffffeff,
  0x040148 = 0xffffffff, 0x04014c = 0xffffffff, 0x002100 = 0xffffffff,
  0x002140 = 0x7fffffff. Of these we make only the 0x04013c write. Linux then serves
  PBDMA interrupts (0x0025a0, 0x0400c0 = 0x80600008,
  `engine/fifo/gf100.c:347,737-744`). We never do.
- KNOWN: we write 0x000200 = 0xffffffff; the last Linux value is 0xf437b1ef.
  S1 and S2 passed with our value.
- KNOWN: Linux has channel 0 on runlist 0 from trace line 561566, before GR
  starts (line 616297). A channel on runlist 0 without a GR context is normal.
- INFERRED: none of these explains a read without completion. They are listed
  because the stop is on the one path that has no reference comparison.

### 2.5 Correction: the libdrm-nouveau idea

The earlier suggestion was to run "our exact channel set-up" under Linux with
libdrm-nouveau. That is not possible: the kernel owns the instance block, the
page tables, the RAMFC and the GR context. User space controls only the push
words, and `s3c` showed that the launch words are not the cause. Drop this
approach. A Linux trace of a bind-only program stays possible as a small extra
reference (approach E).

## 3. Approaches, in the recommended order

Each approach is one new stage of `tools/memstage/stage.py` with its own package
and work folder, as `s3c` and `s3e`. Each card run needs the user's yes.

### A. `s3g`: check the golden image (no submit; lowest risk)

- Card side: as `s3a`, then read the image (0x4ea00 bytes at `GrContext` +
  0x80000) through the slow window and print it. Recommended form: hex lines of
  8 words with the offset, lines of zeros left out, then a word count and a
  32-bit sum. About 7100 lines. No new register access; no GP_PUT.
- Host side: a tool that builds the Linux image from the trace (MAP 26, lines
  811578-892190) and compares it word by word with the printed image.
- Expected differences: only words that hold our own addresses (the registers
  of the 36-entry list, for example 0x408004, 0x40800c, 0x418810).
- If the image is empty or differs widely: the cause is in the generation or in
  where we read or point (0x210, the 0x80000 offset). Fix that first; the other
  approaches wait.
- If the image agrees: the image is HAIKU_VERIFIED content and this cause is
  ruled out.
- Risk: `s3a` and the `s3e` copy already do these reads without a stop.

### B. `s3o`: observe the stop through BAR0 (same risk as `s3c`)

- As `s3e`, but after GP_PUT make no BAR1 access. Poll with the status reads
  that `Compute::snapshot` already makes (all allowed by Guard today): 0x000100,
  0x002100, 0x00259c, 0x040108, 0x040148, channel state 0x800004 + chid*8,
  0x400100, 0x400108, 0x409c18, 0x002640. Read GP_GET of USERD through the slow
  window (`upload_.load` of the `Userd` record at offset 0x288).
- Print a live line before each read group and one with the values after it.
  A timeout is then tied to one named read. Take one snapshot before GP_PUT as
  the baseline.
- Make the BAR1 read of GP_GET the last action, after the status lines.
- Decode of 0x002640 (`engine/fifo/gk104.c:206-216`): busy 0x80000000, faulted
  0x40000000, chsw 0x8000, save 0x4000, load 0x2000, next and previous channel.
- What each outcome means:

| Outcome | Meaning | Next step |
|---|---|---|
| BAR0 reads continue, GP_GET = 1 by slow window, 0x00259c bit 4 set | BAR1 unit fault; the job path works | Read the fault record 0x002800 + unit*0x10 (`engine/fifo/gf100.c:699`); add the BAR1 bind after a fault as Nouveau |
| BAR0 reads continue, 0x00259c bit 0 set | GR MMU fault during the load | Read the fault record: address and access show the missing or wrong mapping |
| BAR0 reads continue, engine status shows load without end, GP_GET = 0 | FECS load does not finish | Compare with approach A; check 0x409c18 and the FECS scratch registers |
| BAR0 reads continue, 0x040108 not zero | PBDMA interrupt waits (for example 0x00800000) | Add the Linux PBDMA 0 set-up and the interrupt service (section 2.4) |
| The first BAR0 read gets no completion | The card stops all host access | Go to approach C to find the smallest trigger |

- Optional second package: add reads of the fault record (0x002800 + unit*0x10
  and the next three words) and of 0x409b00 and 0x409b04. These are new read
  addresses for Guard, with the Nouveau citations above.

### C. `s3n`: bisect below the bind with a host NOP (same risk as `s3c`)

- C1: the S1 host NOP on runlist 0 and PBDMA 0 with the `fifo` and `bind`
  stages only (no GR start). Tests our rewritten FIFO stages alone.
- C2: as `s3a`, then the host NOP (GR started, context attached, no GR method).
- C3 is `s3c` (the bind).
- C1 stops: the fault is in the FIFO stages of section 2.4, not in GR.
- C1 passes, C2 stops: a started GR with an attached context is enough.
- C2 passes: only a method that reaches GR starts the fault; the first load is
  then the cause with more certainty.
- Use the live poll of approach B in these stages too, so that each run also
  reports the status registers.

### D. Align PBDMA 0 and the interrupt registers with Linux (host work)

Add the writes of section 2.4 to the `fifo` stage, with the trace lines as
source, and service a PBDMA interrupt in the poll as
`engine/fifo/gf100.c:309-349`. Do this only if B or C points at PFIFO. It is a
change of the write set: it needs Guard, Policy, provenance and review.

### E. Linux reference for a bind-only submission (optional)

A small libdrm-nouveau program in the Linux guest: one channel, the compute
object, one push of the bind, with mmiotrace. It shows the interrupts and the
register reads that Linux makes for exactly the `s3c` case. It needs
`tools/guest/linux-run.sh --gpu` and the user's approval. Low priority.

## 4. Requests to the user (root, read-only)

Recorded in `docs/REQUESTS.md`:
- The completion timeout range of the root port and its AER state:
  `sudo lspci -vvv -s 00:03.0` (lines `DevCap2`, `DevCtl2`, `UESta`, `UEMsk`,
  `HeaderLog`). The timeout length says if BAR1 reads worked for some time after
  GP_PUT or if the first read after GP_PUT failed.

## 5. State to resume from

- Branch `ccr-5d33feda-7ni61l`. Commits after f491240 are local. The user pushes.
- Card 0000:04:00.0: on `vfio-pci` with the boot-time reservation
  (`attach-at-boot`). A live `attach` hangs from a desktop session on this
  machine. The kernel-log stream writes `~/k40-s1-kernel.log`.
- When finished, the user runs `detach` and `llm-mode.sh one`.
- Consumed or superseded packages, not to be run: `package-s1c`, `package-s3b`,
  `package-s3b-diag`, `package-s3c`, `package-s3d`, `package-s3e`.
- `make check` needs Mediaflux mounted (VBIOS file).
- Each new stage follows the pattern of `s3e`: stage entry in
  `tools/memstage/stage.py`, mode in `src/gr/Compute.*` and
  `src/memnative/NativeOwner.cpp`, validator in `tools/memstage/evidence.py`,
  names in `tools/memstage/build.py` and `run.py`, host test in
  `tests/test_gr_compute.cpp` and `tests/test_memstage_tools.py`. Then:
  `K40_MEM_STAGE=<name> python3 tools/memstage/build.py`, `rehearse.py --run`,
  `build.py --check`, `run.py --host-check`, and with the user's yes
  `run.py --run-approved-batch1-once`.
- After a launcher stop: report, then ask the user before another run (ADR 006).
- Escalation rule: `s3b`, `s3c` and `s3e` are three attempts at the same stop.
  Approaches A to C observe; they do not retry the same guess. If the user
  prefers a formal escalation, write `escalations/ESC-NNN.md` from this report.

## 6. Update after the s3g run (2026-11-17)

Approach A ran once (`work/S3DIAG/FINDINGS.md`, entry "s3g on the card").
- The golden image is not empty and has the Linux layout. For the first 64 KiB
  it differs from a Linux image less than two Linux images differ from each
  other. The cause "empty or grossly wrong image" is ruled out for that part.
- A word-by-word comparison has limits: about half of the image changes between
  two Linux runs. `tools/gr/golden.py` judges only the words that agree in both.
- The run failed on the 30 s deadline of the driver during the print, without a
  PCIe error. To print the full image, copy it to driver memory during the
  stage and print it after the teardown.
- Approach B (`s3o`) is now the next step. Keep its live lines few: one line
  costs about 8 to 16 ms.


## 7. Stage s3o is built (2026-11-17)

Approach B is ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage
s3o built"). The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3o python3 tools/memstage/run.py --run-approved-batch1-once`

How to read the serial log. The last `k40_mem: OBS` line names the last group
of reads that completed.

| Log ends after | The read without completion | Meaning |
|---|---|---|
| `LIVE step=11 ... a=1` (GP_PUT) | a BAR0 status read of g=1 | The card stops all host access. Go to approach C |
| `OBS ... g=1` | a GR status read of g=2 | GR registers stop; FIFO registers still answer |
| `OBS ... g=2` | a fault-record read (g=4) or the slow window (g=3) | See the 0x00259c value of the g=1 line |
| `OBS ... g=4` | the slow-window read (g=3) | The window stops after an MMU fault; the fault record is in the log |
| `OBS ... g=3` | a BAR0 status read of the next sample | The card stops host access some time after GP_PUT; the earlier samples show the state before |
| `OBS ... g=5` | the BAR1 read | Only BAR1 is stalled, without a pending MMU fault |
| the run ends with a report | none | Read the g=1 values with the table of section 3, approach B |

Values of a g=1 line, in order: 0x000100, 0x002100, 0x00259c (MMU fault units),
0x040108 (PBDMA 0 interrupt), 0x040148, channel state, 0x002640 (engine
status). A g=4 line holds: unit, instance, address low, address high, type
(`engine/fifo/gf100.c:699-712`).

Differences from the plan of section 3:
- The fault record is read in this stage already (no second package).
- 0x409b00 and 0x409b04 are not read.
- The BAR1 read is left out while an MMU fault is pending.

## 8. Update after the s3o run (2026-11-17)

Approach B ran once (`work/S3DIAG/FINDINGS.md`, entry "s3o on the card").
- Outcome: none of the rows of the table of approach B in its plain form.
  BAR0 register reads continue after GP_PUT. No fault and no interrupt is
  pending. The engine status shows a load of channel 1 (0x002640 = 0x00012001).
  The first host read of VRAM after GP_PUT (slow window) got no completion.
- Thus the stop is not "BAR1 only" and not "all host access". It is host
  access to VRAM (BAR1 and the slow window) while the engine loads the context.

### F. `s3p`: observe with registers only (next step)

- As `s3o`, but after GP_PUT make no access to VRAM at all: no BAR1, no slow
  window. Poll registers only for about 2 s, then run the teardown. The
  teardown and `closeUserd` use registers only, so a clean end is possible.
- Read in each sample: the group 1 and group 2 registers of `s3o`, and new
  status reads (each needs a Nouveau citation and a Guard entry before the
  build): the FECS current and next context 0x409b00 and 0x409b04, the FECS
  scratch registers that `hub.fuc` writes during a load, the MMU status
  0x100c80, and PBDMA 0 GP_GET and GP_PUT registers (the PBDMA copy of the
  USERD values) in place of the USERD read.
- Questions it answers: does the load end; does a fault or an interrupt appear
  after 62 ms; does the PBDMA fetch the entry; does the teardown recover the
  card without a VM restart.
- After the teardown, one slow-window read as the last action shows if host
  access to VRAM returns.
