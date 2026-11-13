# S3LAUNCH findings

## Launch images (2026-11-12, SOURCE_ONLY)

`tools/gr/launch.py` builds the layout (12 records, 66,379,776 bytes, of which the
TLS area is 63,438,848), the push buffer (106 words: 100 set-up, 6 launch), the
descriptor and constant buffer 7 from the Mesa sources. The descriptor equals the
one of the reference run in 154 of 155 fields. The one difference is the address
of constant buffer 7, which follows our layout.

- KNOWN: `mp_count` of Mesa is the TPC total (`gf100.c:1160-1169`,
  `nvc0_screen.c:1065`): 15 on this card. TLS bytes per unit 0x408000.
- UNKNOWN: whether the 64 values of method 0x248 and the TIC/TSC addresses are
  needed for a job without textures. They are kept, as in Mesa.

## Slow-window speed (KNOWN, HARDWARE_VERIFIED under Haiku, S1 run of 2026-10-31)

results/20261031-batch1-a7-bar1-d198d424/serial.log: a 262,144-byte record is
zeroed in 21 to 124 ms and read back in about 100 ms; one 8-byte patch with flush
and readback takes about 6 us. Consequence: zeroing the 847,872-byte context
memory and writing about 16,000 page-table entries fit in well under one second
each when the entries are written in bulk with one flush.

## Native compute stage, host result (2026-11-12, HOST_ONLY)

New code: `src/gr/Compute.{h,cpp}` (the stage of PLAN.md), `src/gr/Guard.{h,cpp}`
(write rules), `memnative::Extension` (the Policy asks the Guard in the channel
phase), ledger capacity 32 with twelve S3 records, `Upload::store` and `load`.
The channel sequences on the GR runlist (fifo, bind, attach, teardown) are ops of
the generated program, like the GR stages.

Write rules of the Guard:
- A register write is accepted only as the next writing op of the program, at
  that address, with the value the Guard computes from the owned ledger and from
  the values the card returned. The Runner and the Guard share the op tables only.
- Outside the program: the two TLB invalidations and the BAR1 context enable and
  disable of S1, each once, with exact values. GP_PUT = 1 once, after the attach.
- After a failure the only accepted continuation is the teardown sequence.
- Data writes: owned records of the stage before the first program write; later
  only the context pointer words of the instance block and the two list words
  of the context image. The value of image words is not checked (weaker than S1,
  where every data word had an expected value).

`tests/test_gr_compute` (simulated card): the GR registers answer from the Linux
trace and refuse any access that is not the next trace access, so the whole
bring-up runs trace-exact through Policy and Guard (6,333 accesses). On GP_PUT
the simulation decodes page tables, instance block, context words, register
list, push buffer, descriptor and constant buffer 7 on its own and computes
out[i] = in[i] + 1 through the page tables. Scenarios: pass, no launch (rung 4),
FECS never ready (stops, teardown completes), one wrong output element, entry
never fetched. Four source mutations make the test fail (context pointer bit,
push length, launch value, guard value rule).

Native: Compute, Guard, Runner and the generated data compile for Haiku kernel
mode with the package flags. No link here.

Open: NativeOwner integration and report lines, validator and package tools for
stages s3a and s3b, T7610 build and rehearsal, review. The test does not prove
that the compute class sequence is right for the card: it checks our own images
against Mesa's sources and against an independent decode.

## Status registers in the reference run (2026-11-13, KNOWN, from the mmiotrace)

Checked because the pass rule of the stage requires zero GR interrupt, GR trap
and FECS interrupt status, and no PBDMA interrupt.

- Linux never read 0x400100, 0x400108 or 0x409c18 after the engine start: no GR
  or FECS interrupt occurred in the reference run. It wrote 0xffffffff to
  0x400100 and 0x400108 once at init (lines 616755, 616954), as the program does.
- The GR engine status 0x002640 read 0 in all 8 reads.
- One PBDMA interrupt occurred during the job: 0x002100 = 0x20000000 and
  0x040108 = 0x00800000 (lines 895452-895460), acknowledged by Linux. INFERRED:
  a method that the host passes to software (Mesa binds a software object on its
  channel). Our push buffer has no such method. If rung 5 stops with
  `pbdma=800000`, this is the first thing to look at: it would mean one of our
  methods is handled by software under Linux.
- 0x000100 read 0x100000 and 0x100 at times: pending bits of other units. The
  stage records 0x000100 and does not use it in the pass rule.
