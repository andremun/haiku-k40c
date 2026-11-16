# S3DIAG plan: live progress and a bisect of the rung 5 stop

Written 2026-11-16 after rung 5 (`s3b`) stopped on a PCIe completion timeout
(work/LADDER/FINDINGS.md). The user chose: live journal and bisect. Nothing here
ran on a card. Every new package needs review, a cardless rehearsal and an
explicit yes of the user before its run (ADR 007, ADR 008; it is not on the
approved ladder of decision 012).

## Problem

The owner prints its journal only in `drain()`, after the work. A stop during
the work leaves the serial log at `PREPARED`, so the stop is not located.

## 1. Live progress lines

`gr::Compute` gets an optional progress sink. The owner prints one line per
event with `dprintf`, at once:

    k40_mem: LIVE step=<Step> us=<since compute start> a=<hex> b=<hex>

- At the start of every step of `Compute::run()` (Route .. Teardown, Done).
- After the GP_PUT write; then every 100 ms of the GP_GET poll (a = GP_GET).
- Every 100 ms of the result poll (a = last output word).
- After the stop of a step that failed (a = error).

Host only: the sink does not touch the card. No new register access, so the
Guard and the Policy do not change. Cost: under 40 lines of serial output.

## 2. Bisect variants (prefixes of the same push buffer)

The push buffer page keeps the same 106 words in every variant. Only the length
of the one GPFIFO entry changes (`nouveau_dma.c:83-84`), so the GPU fetches a
prefix:

| Stage | Number | GPFIFO entry | Pass marker | Pass rule |
|---|---|---|---|---|
| `s3c` | 5 | object bind: 2 words (method 0 = 0xa1c0) | `PASS S3_BIND` | golden, attach, GP_GET 1/1, clean status, teardown |
| `s3d` | 6 | set-up: the 100 words up to FLUSH, no launch | `PASS S3_SETUP` | as `s3c` |
| `s3b` | 3 | full: 106 words, with LAUNCH | `PASS S3_COMPUTE` | as rung 5: also 1024 of 1024 elements |

`s3b` gets a new package folder and work folder (`package-s3b-diag`,
`work/S3DIAG/s3b`): the rung 5 package is consumed and stays unchanged.
Order on the card: `s3c`, then `s3d`, then `s3b`. Stop at the first stop.

What each result would show:

- `s3c` stops: the channel or the context fails on the first method, not the launch.
- `s3c` passes, `s3d` stops: a set-up method (addresses, TIC/TSC, 0x248 list, FLUSH).
- `s3d` passes, `s3b` stops: the launch or the job (descriptor, code, constant buffer 7).
- With the live lines, every stop also shows the last step that finished.

## Work

1. `src/gr/Compute.*`: launch mode (none, bind, setup, full), GPFIFO length per
   mode, progress sink. `src/memnative/NativeOwner.*`: sink with `dprintf`,
   new stage numbers and pass markers.
2. `tools/gr/program.py`: emit the prefix lengths (`pushBindBytes`, `pushSetupBytes`).
3. `tools/memstage/stage.py`, `build.py`, `run.py`, `evidence.py`: stages `s3c`
   and `s3d`, their validator rules.
4. `tests/test_gr_compute.cpp`, `tests/test_memstage_tools.py`: the new modes,
   the live lines, the validator for each stage.
5. `make check`; build and cardless rehearsal of `s3c`, `s3d`, `s3b` on the T7610.
