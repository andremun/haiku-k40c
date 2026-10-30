# S1 channel package for review (2026-10-31)

Task S1CHANNEL (`docs/tasks/S1CHANNEL.md`). Lean implementation of the batch-2
design (`docs/S1-BATCH2-REVIEW.md`, "Claude Code review and final design
decisions"): one host NOP on one copy-engine (CE0) channel, polling only.
**Run 1 stopped at the 8 MiB BAR0 view before any bind (results/20261031-batch1-a7-bar1-3f33bd37/). The S1CHANNEL2 run ran every step but GP_GET stayed 0 (results/20261031-batch1-a7-bar1-c261b19b/). Current package: S1CHANNEL3 (work/S1CHANNEL3/RESULT.md), adding the post-POST unit enable. It needs the user's explicit yes for one run.**

## What runs

One fresh guest, as in batch 1 (`results/20261030-batch1-a7-bar1-ec8db47d/`):
unchanged A7 (POST, readiness), unchanged batch-1 memory and BAR1 gates, then
the new channel phase in the same resident memory owner, under the same signed
grant and the same 30 s native window.

```sh
python3 tools/memstage/build.py --check
python3 tools/memstage/run.py --host-check
python3 tools/memstage/run.py --run-approved-batch1-once
```

The R5 stream and `/dev/vfio/23` access are needed as before. One launch
consumes `build/memstage/package-s1c/`. After any stop: report, no retry (ADR 006).

| Artifact | SHA-256 |
|---|---|
| Package manifest `work/S1CHANNEL3/package.json` | `1c7d71d55a314a90a9907fb6910771a729dc76ca9b620b121f55f8b26b17f0a4` |
| Plan | `de1b97187f1aa7d8fe39ff773db69da6759ec524fb692e7307b2cc0da89b78af` |
| memory_owner (channel code, 16 MiB BAR0, unit enable) | `4454fd0f8cffb252a31592ffdedd60834245ba4da6b85fae2f8ef48bbe4a6118` |
| memory_client / memory_helper (unchanged) | `04848c97...` / `bfcd7361...` |
| A7 owner (frozen sources, new key/nonce) | `b4f73dcfbe24062b00f2a7cb2cff3c29d7a3e21a86e51bdfb9b1fd7fa635ccab` |
| A7 client / helper / identity (unchanged) | `d11b0d37...` / `58bec7c5...` / `8c45ec7b...` |
| Guest kernel / ROM | `2da9a5b9...` / `aecb0b5f...` |

## Design choices and evidence

- **CE0 runlist, no engine context.** A GR channel needs a GR context pointer
  (`fifo/gk104.c:134-141`); the CE function table has no ctor/bind
  (`fifo/gk104.c:281-287`). CE0 is TOP type 1 (`top/gk104.c:79`); the batch-1
  Haiku capture puts it on runlist 4 (KNOWN). Linux's kernel channel 1 used
  runlist 4 (mmiotrace 562288-562370, TRACE_VERIFIED). The runlist is read from
  TOP at run time, never assumed.
- **PBDMA from routing.** `0x2390+p*4` lists the runlists each PBDMA serves
  (`fifo/gk104.c:392`). Linux read `0x1`, `0x6e`, `0x10`: PBDMA2 serves
  runlist 4 (trace 230517-230519). Selected at run time.
- **RAMFC as Linux wrote it.** Every word follows `fifo/gk104.c:84-102`; the
  fixed words equal trace lines 562271-562285. USERD is a VRAM page; the RAMFC
  holds its physical slot address (`fifo/gk104.c:84,88-89`).
- **GP_PUT through BAR1, as Linux.** `0x2254` is PFIFO `BAR1_BASE`
  (`rnndb fifo/gf100_pfifo.xml:58-61`); Linux set `0x10000000` (trace 560992,
  USERD at BAR1 VA 0) and mapped its USERD slots there. Whether a plain VRAM
  write of GP_PUT is noticed is UNKNOWN, so the package maps the USERD page at
  BAR1 VA 0 (writable entry, `mmu/vmmgf100.c:313-316`) through the batch-1
  BAR1 tables, and writes GP_PUT once through BAR1.
- **No interrupts.** No `0x2100`/`0x2140`/PBDMA INTR/INTREN write. Progress is
  polled: BAR1 read of GP_GET, 2 s bound.

## Every new card write, in order

The resident `Policy` (`src/memnative/Policy.cpp`, `channelWrite`) accepts only
this sequence. Values that depend on a read must use the Policy's own observed
read. Any other write is refused.

| Step | Register = value | Source |
|---|---|---|
| VRAM | zero 7 new pages (64 KiB PDB, 256 KiB SPT, instance, USERD, GPFIFO, push, runlist) and write their images | `memstage/ChannelImage.cpp` |
| 0-1 | `0x100cb8` = channel PDB selector, `0x100cbc = 0x80000001` | `mmu/vmmgf100.c:199-233` PAGE_ALL |
| 2 | BAR1 SPT entry 0 = writable USERD page (VRAM) | `mmu/vmmgf100.c:313-316` |
| 3-4 | `0x100cb8` = BAR1 PDB, `0x100cbc = 0x80000005` | as batch 1 |
| 5 | `0x1704 = 0x80000000 \| inst>>12` (batch-1 BAR1 context), two BAR flushes | `bar/gf100.c:38-58` |
| 6 | `0x200 = 0xffffffff` (every unit enabled, as Linux after POST) | `mc/nv04.c:120`, trace 47330 |
| 7-8 | `0x204 = 0xffffffff`, then `0x204` = present mask read back | `fifo/gf100.c:927-934`, `fifo/gk104.c:739` |
| 8 | `0x2a04 = read \| 0xbfffffff` | `fifo/gk104.c:740` |
| 9 | `0x4013c+p*0x2000 = read & ~0x10000100` (selected PBDMA only) | `fifo/gf100.c:357` |
| 10 | `0x2254 = 0x10000000` | `fifo/gk104.c:749`, trace 560992 |
| 11 | `0x80000c = runlist << 16` (channel 1, inactive 0 read first) | `fifo/gk104.c:77`, trace 562288-562289 |
| 12 | `0x800008 = 0x80000000 \| inst>>12` | `fifo/gk104.c:68` |
| 13 | `0x80000c = read \| 0x400` (start) | `fifo/gk104.c:52` |
| 14-15 | `0x2270 = runlist page>>12`, `0x2274 = runlist<<20 \| 1`, poll pending clear | `fifo/gk104.c:426,446-447` |
| 16 | BAR1 `0x28c` (GP_PUT) `= 1`, once | `nouveau_dma.c:92` |
| 17 | `0x80000c = read \| 0x800` (stop) | `fifo/gk104.c:44` |
| 18 | `0x2634 = 1` (preempt), poll bit 20 clear | `fifo/gf100.c:43,372` |
| 19-20 | `0x2270` = runlist page, `0x2274 = runlist<<20` (empty), poll | `fifo/gk104.c:426,446-447` |
| 21 | `0x800008 = 0` (unbind) | `fifo/gk104.c:60` |
| 22 | `0x1704` = context with enable cleared | `bar/gf100.c:46-49` |

Teardown is mandatory after step 11: a stall (no GP_GET progress) or a later
failure still runs steps 17-22. The Policy allows only those jumps.

## Pass test (S1)

`evidence.memory_final` re-derives everything from the journal, with an
independent Python encoder of the channel image. S1 PASS needs:
GP_GET 0 before and 1 after GP_PUT 1; no MMU fault (`0x259c`), no PBDMA or HCE
interrupt status, no `0x2100` bit other than 30/31 (`fifo/gk104.c:654-718`);
the exact write order above; completed runlist and preempt polls; teardown and
BAR1 disable; all batch-1 checks. Any miss is a FAIL, recorded with all lines.

## Checks done (host and cardless only)

- `tests/test_mem_channel.cpp`: full path, stall with teardown, MMU-fault
  refusal, through the real Policy, zero denials. Its simulated FIFO advances
  GP_GET only if the RAMFC, channel page tables, GPFIFO entry and NOP decode
  correctly, against trace-literal RAMFC words. Mutations of the NOP header and
  device mask are detected.
- `tests/test_memstage_tools.py`: the dump passes `memory_final`; nine
  mutations (progress, fault, route, RAMFC, invalidate type, NOP) are refused.
- Cardless rehearsal of the exact package:
  `results/20261031-batch1-rehearsal-8779e475/` PASS_CARDLESS_NO_CARD.
- `build.py`, `rehearse.py`, `host_check.py`, `run.py --check` and full
  `make check` pass (`work/S1CHANNEL/check-final.log`).

## Limits and risks

- Implemented and reviewed by Claude Code in one session; no second reviewer.
- UNKNOWN until the run: host scheduling of a CE channel without any CE engine
  set-up; whether GP_PUT through BAR1 is noticed without other FIFO init that
  Linux did (interrupt status/enables). A stall is a clean, recorded FAIL.
- Worst case on the card: a stuck channel or scheduler; the teardown and the
  VFIO reset at the next guest start bound it. The host is protected by the
  IOMMU and the watchdog. No other card is touched.
- Q7 (DMA visibility) and Q11 stay open. No GR, no copy, no compute.
