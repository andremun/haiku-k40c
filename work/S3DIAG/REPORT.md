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

## 9. Stage s3p is built (2026-11-17)

Approach F is ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage
s3p built"). The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3p python3 tools/memstage/run.py --run-approved-batch1-once`

How to read the serial log:
- Lines `OBS n=<sample> g=<group>`: g=1 and g=2 as section 7; g=7 FECS
  (current channel, next channel, signal, scratch 0, 1, 4, 5); g=8 MMU status
  and PBDMA 0 method address, data, channel; g=4 a fault record.
- The last value of each g=1 line is the engine status. 0 means idle; the
  load bit is 0x2000.
- `LIVE step=14` is the start of the teardown. The `GR` report line shows
  `closed=1` when the teardown passed.
- `OBS ... g=9` is printed before the last slow-window read. A log that ends
  there, with an AER message, shows that host access to VRAM does not return
  after the teardown.

Difference from the plan of section 8: the PBDMA copies of GP_GET and GP_PUT
are not read (no source in the references). The PBDMA 0 method address, data
and channel are read in their place.

## 10. Update after the s3p run (2026-11-17)

Approach F ran once (`work/S3DIAG/FINDINGS.md`, entry "s3p on the card").
- Registers stay readable for at least 4 s after GP_PUT, with one steady
  state: no fault, no interrupt, no FECS error, channel 1 current on the GR
  engine, engine not busy.
- The preempt of the teardown fails after 2 s. The slow-window read after the
  teardown gets no completion.
- Correction: the engine status 0x00012001 is not "load in progress"
  (section 8). It is "channel 1 loaded, engine idle" by the Nouveau decode.
- So the first schedule of our channel on the GR engine ends in a state where
  access to VRAM is lost, for the host and (INFERRED) for the context save.

### G. `s3q`: end with a report, and read the FECS trace word (next step)

- As `s3p`, without the last slow-window read. Then no access can time out,
  the driver prints its report, and the journal shows which teardown poll
  failed (`GR_FAILURE closing`, `closing_index`).
- New status reads: FECS trace word 0x40981c (`fuc/macros.fuc:253-261`): it
  names the FECS routine that runs (T_AUTO, T_CHAN, T_LOAD, T_SAVE, T_LCHAN,
  T_LCTXH). Also 0x001700 and 0x001704 (window selector and BAR1 context):
  a register list that FECS executes from wrong data can write any register.
- Sample also during the teardown is not needed: take one sample after it.

### H. `s3r`: the load without the register list (after G)

- As G, with the list count in word 0 of the channel image set to 0, so that
  FECS executes no register list (`fuc/hub.fuc:555-592`).
- If access to VRAM stays good: the register list (its address, its mapping
  or its content) is the cause. If not: the cause is in the image transfer or
  outside the GR engine; then approach C (`s3n`, host NOP on the GR runlist
  without a context) separates the two.

## 11. Stage s3q is built (2026-11-17)

Approach G is ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage
s3q built"). The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3q python3 tools/memstage/run.py --run-approved-batch1-once`

How to read the serial log:
- `OBS ... g=8` values: MMU status, PBDMA 0 method address, data, channel,
  FECS trace word, window selector, BAR1 context.
- FECS trace word bits (`fuc/macros.fuc:202-212`): 0 WAIT, 1 MMCTX,
  2 STRWAIT, 3 STRINIT, 4 AUTO, 5 CHAN, 6 LOAD, 7 SAVE, 8 LCHAN, 9 LCTXH,
  10 STRTPC. A set bit names a routine that FECS entered and did not leave.
- `GR_FAILURE ... closing=<error> closing_index=<n>`: the teardown op that
  failed. Find the op with `tools/gr/program.py` (stage `teardown`).
- The expected end is `FAIL` with a complete report, not an AER stop. An AER
  stop in this stage would be new: a register access without completion.

## 12. Update after the s3q run (2026-11-17)

Approach G ran once and ended with a complete report, without an AER message
(`work/S3DIAG/FINDINGS.md`, entry "s3q on the card").
- The first load of our channel completes: FECS trace word 0, current channel
  valid, engine idle, no error, for 2 s.
- The preempt of the teardown does not end: FECS stays in the register
  transfer of the context save (trace word 0x12, engine status 0x8001c001).
- The window selector and the BAR1 context are unchanged, so the register
  list did not overwrite them.
- Summary of all runs: after the first context load, data does not move
  between the card and VRAM. Register access stays good.

Next steps, in the recommended order:
1. Approach H (`s3r`): the same stage with the list count 0 in word 0 of the
   channel image, so that `ctx_mmio_exec` does not run. Use the `s3q` form
   (no VRAM read during the samples), then, when the engine is idle, one
   slow-window read of GP_GET before the teardown. A read that completes
   shows that the register list is the cause.
2. If H changes nothing: compare the load-only steps with the Linux run.
   Approach D (PBDMA 0 and interrupt set-up of Linux, section 2.4) and a
   Linux trace of a bind-only submission (approach E) give the reference.
   Read more state after the load in a `s3q` variant: 0x409614 (red switch),
   0x409a24 and the FECS memory registers that `ctx_load` and `ctx_mem` use
   (`fuc/hub.fuc:471-483`).

## 13. Stage s3r is built (2026-11-17)

Approach H is ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage
s3r built"). The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3r python3 tools/memstage/run.py --run-approved-batch1-once`

How to read the result:

| Teardown (after `LIVE step=14`) | Last read (after `OBS ... g=9`) | Meaning |
|---|---|---|
| no `LIVE step=0` line | completes, GP_GET 1 | PASS: the register list is the cause. Next: check the list entries one by one against the Linux list |
| `LIVE step=0 ... b=11` (preempt) | no completion (AER) | The list is not the cause. Next: approach D and E, and more FECS state after the load |
| no `LIVE step=0` line | no completion (AER) | The save works, host reads of VRAM do not. Next: look at the host path (BAR1 and window) after a load |
| `LIVE step=0 ... b=11` | completes | The host path is good, the save is not. Next: the GPC and strand transfers of the save |

## 14. Update after the s3r run (2026-11-17)

Approach H ran once. Row 1 of the table in section 13: the teardown passed and
the last read completed with GP_GET 1. The driver printed `PASS S3_NO_LIST`.
The launcher result is `failed` because a validator rule of mine ("engine
status 0 at the end") is wrong; see `work/S3DIAG/FINDINGS.md`.

Result: the register list that FECS executes at the first load is the cause
(INFERRED from `s3q` against `s3r`). Also the first card proof that the GR
runlist channel fetches its entry.

Next steps:
1. Fix the validator rule (busy bit clear, not status 0) for later stages.
2. Host only: compare our 36 list entries with the list of the Linux run.
3. If the comparison shows no clear difference: bisect on the card with a list
   count of 18, then 9, and so on.

## 15. Validator fixed, list compared (2026-11-17)

- The engine rule is now "not busy" (bit 31), in the validator and in the
  report-mode pass rule. With it the `s3r` log validates (recheck after the
  run; the run result stays `failed`).
- `tools/gr/patchlist.py`: our register list equals the Linux list in order
  and in all 28 constants. The 6 address entries hold our own record
  addresses, which the golden stage already used on the card. No difference
  explains the stop.
- Next card stage (proposed, not built): `s3s`, list count 34 (all but the LTC
  pair 0x17e91c, 0x17e920). See `work/S3DIAG/FINDINGS.md`.

## 16. Stage s3s is built (2026-11-17)

Ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage s3s built").
The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3s python3 tools/memstage/run.py --run-approved-batch1-once`

Read the log as `s3r` (section 13):
- Teardown passes and the last read gives GP_GET 1: the LTC pair (entries 34,
  35) is the cause.
- Teardown fails on the preempt, or the last read gets no completion: the
  cause is in entries 0-33 or in the header write-back. Next: list count 1
  (entry 0 and the write-back), then halve.

## 17. Cause found (2026-11-17)

`s3s` passed on the card with list entries 0-33. Entries 34 and 35 (LTC
registers 0x17e91c, 0x17e920) are written into the list record before the
golden stage reads their values, so the list holds 0 for both. At the first
load FECS writes 0 into the two L2 cache registers; after that, data no
longer moves between the card and VRAM (INFERRED; it matches all runs from
`s3b` to `s3s`). Details and the fix: `work/S3DIAG/FINDINGS.md`, entry "s3s on
the card".

## 18. List fix made (host, 2026-11-17)

The two card-read list entries are now written in the attach hook, after the
golden stage read them (`work/S3DIAG/FINDINGS.md`, entry "fix of the register
list"). Host tests check the whole list against Linux. No card run with the
fix yet.

## 19. Stage s3t is built (2026-11-17)

Ready for one card run (`work/S3DIAG/FINDINGS.md`, entry "stage s3t built").
The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3t python3 tools/memstage/run.py --run-approved-batch1-once`

- Pass (teardown passes, last read GP_GET 1): the fix works with the whole
  list. Next: the compute job (`s3b` with the fix).
- Fail like `s3q` (preempt does not end, or the last read gets no completion):
  the LTC values are not the whole cause; compare the run with `s3s`.

## 20. The fix works on the card (2026-11-17)

`s3t` passed: the whole register list, with its LTC entries written after the
golden stage, keeps access to VRAM; the preempt, the teardown and the last
read of GP_GET (1) pass. This closes the S3DIAG question "why does the first
GR channel submission stop the card". Next: the compute job with the fix.

## 21. Stage s3u is built (2026-11-18)

The compute job (`s3b`) with the channel set-up of `s3e` and the whole fixed
register list (`work/S3DIAG/FINDINGS.md`, entry "stage s3u built"). Ready for
one card run. The run needs the user's explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3u python3 tools/memstage/run.py --run-approved-batch1-once`

- Pass (`PASS S3_COMPUTE`, `wrong=0`, clean teardown): rung 5 reached, one
  compute job on the card with every element checked.
- GP_GET 1 but wrong elements, or the result poll to the bound: the job ran
  with a wrong set-up; compare the push buffer with the Linux run.
- Stop at the BAR1 poll of GP_GET (AER): rebuild with the registers-only
  observation of `s3t` (approach H) and read the output after the teardown.

## 22. s3u on the card: the job faults in GR (2026-11-18)

`s3u` fetched the entry (GP_GET 1 by BAR1 after 27 ms, so BAR1 after GP_PUT
works with the fix) but wrote no output: the last element read 0 for 2 s,
and at the end an MMU fault of unit 0 (GR) was pending. No AER. The driver
then failed on a full journal (the result poll journals every read), and the
teardown did not run. The fault record was not read. Details in
`work/S3DIAG/FINDINGS.md`, entry "s3u on the card". Next: read the fault
record of the job (stage proposed there).

## 23. Stage s3v is built (2026-11-18)

`s3u` with the fault record (`work/S3DIAG/FINDINGS.md`, entry "stage s3v
built"). Ready for one card run. The run needs the user's explicit yes
(ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3v python3 tools/memstage/run.py --run-approved-batch1-once`

- Fault again: the launcher reports `failed`; the serial log holds the fault
  record (`OBS ... g=4`: unit, instance, address, type). Decode the address
  against the job's regions (`tools/gr/launch.py`) and the type against
  `fifo/gk104.c` fault tables.
- Pass (`PASS S3_COMPUTE`): the job ran; `s3u` failed for another reason.

## 24. s3v: the job writes its read-only launch descriptor (2026-11-18)

The fault record of `s3v`: a write by the GR hub (client DFALCON) to VA
0x13e40000, offset 0 of the launch descriptor (Qmd), which we map read-only;
reason RO_VIOLATION. No output written, no AER. With the fault pending the
teardown preempt did not end. Details in `work/S3DIAG/FINDINGS.md`, entry
"s3v on the card". Proposed next: map the descriptor writable, as Mesa's
scratch buffer is on Linux, and run the job again with the fault mode.

## 25. Stage s3w is built (2026-11-18)

`s3v` with the launch descriptor mapped writable (`work/S3DIAG/FINDINGS.md`,
entry "stage s3w built"). Ready for one card run. The run needs the user's
explicit yes (ADR 006).

Command, after the yes and with the card on `vfio-pci`:
`K40_MEM_STAGE=s3w python3 tools/memstage/run.py --run-approved-batch1-once`

- Pass (`PASS S3_COMPUTE`, `wrong=0`, clean teardown): rung 5 reached.
- Another fault: decode the printed record as in section 24.
- No fault but output wrong or not written: compare the job set-up with the
  Linux run.
