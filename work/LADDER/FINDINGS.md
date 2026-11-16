# LADDER findings, card day 2026-11-16

## Results

| Rung | Stage | Result | Evidence |
|---|---|---|---|
| 1 | Linux guest | PASS: 0 of 4 jobs differ from the CPU; FP32 matrix product N=1024, median 0.1357 s | `reference/linux-run-ladder/RESULT.txt` |
| 2 | `s1` | PASS S1_CHANNEL_NOP, faults=0, 159 s | `results/20261116-batch1-a7-bar1-7972ea19/README.md` |
| 3 | `s2` | PASS S2_COPY: copied=1, launcherr=0, engine idle after 18 us; `s2d` not run | `results/20261116-s2-run-82bf52ab/README.md` |
| 4 | `s3a` | PASS S3_GOLDEN: GR program 6277 ops, GR_FAILURE all zero, faults=0 | `results/20261116-s3a-run-1fe37fd6/README.md` |
| 5 | `s3b` | STOPPED by the launcher after 144 s (R5 line). No retry | `results/20261116-s3b-run-b4d27e59/README.md` |

## Rung 5 stop

KNOWN (host journal, read by the user with root):

- `pcieport 0000:00:03.0: AER: Uncorrectable (Non-Fatal)`, transaction layer,
  `error status/mask=00004000/00000000`, `[14] CmpltTO (First)`, then
  `device recovery successful`. Kernel time 4311.31 s.
- 0000:00:03.0 is the root port of 0000:04:00.0. The K40c at 03:00.0 is
  behind 0000:00:02.0 and is not involved.
- sysfs `aer_dev_nonfatal`: CmpltTO 1 on 00:03.0; all counters 0 on 04:00.0.
- A completion timeout at the root port: a non-posted request that the root port
  sent down to the card (a guest read of BAR0 or BAR1) got no completion.

KNOWN (host file times): serial ends at `k40_mem: PREPARED` (13:52:21.87),
`memory-attestation.json` 13:52:21.99, AER 13:52:24.50, stop 13:52:26.02.

The owner prints the journal only in `drain()` after the work
(`src/memnative/NativeOwner.cpp`). So the empty serial after PREPARED does not
locate the stop.

INFERRED (timing): the error came about 2.5 s after the work started. In rung 4
the whole work (batch-1 phases and the compute stage up to the closed channel)
took less than about 1.9 s by its journal times. So at 2.5 s, `s3b` was most
likely past the attach, in `Compute::submit()` (BAR1 USERD reads of GP_GET) or
`Compute::result()` (slow-window reads of the output, 1 ms apart, up to 2 s), or
in the teardown after them (`src/gr/Compute.cpp`). Not verified: the delay
between the attestation file and the start of the work is not recorded.

INFERRED: the card stopped answering host reads after the GPFIFO submit. Candidate
causes, not tested: the launch push words (SOURCE_ONLY, no trace), a compute-only
channel without 3D-class state, the generation memory used as the channel context.

## Next steps (need the user's decision; none is on the approved ladder)

1. Print the journal to the serial line before the submit and after each poll,
   so a stop shows the last completed step.
2. Bisect the push buffer with new prebuilt variants: object bind only; set-up
   without LAUNCH; full launch.
3. Run the exact push words and descriptor under Linux through libdrm-nouveau
   (S3LAUNCH work package 7), to separate launch errors from Haiku bring-up errors.
