# 013. S3 complete: the project goal is reached in its designed scope

Date: 2026-11-18. Status: accepted (user instruction: "First repeat run, then
records update, and call it completed to the scope designed").

## Context

The goal of the project (`AGENTS.md`, `docs/PHASES.md` milestone S3,
`docs/design/specification.md` Stage 7) is a native Haiku kernel driver that
runs one verified compute job on the Tesla K40c: `output[i] = input[i] + 1`,
with the host reading the output buffer and checking every element.

Evidence (HARDWARE_VERIFIED for this card under Haiku, two runs):

| Run | Result folder | Result |
|---|---|---|
| `s3w` | `results/20261118-s3w-run-c25fd943/` | PASS S3_COMPUTE, 1024/1024 elements right |
| `s3y` (repeat, current driver) | `results/20261118-s3y-run-27b46ec2/` | PASS S3_COMPUTE, 1024/1024 elements right |

Both runs: GP_GET 1, no MMU fault, no GR, FECS or PBDMA interrupt, clean
teardown, no AER. The earlier milestones also passed on the card: S1
(2026-10-31) and S2 (2026-11-16, `work/LADDER/FINDINGS.md`). The teardown also
recovers from a GR MMU fault (`s3x`, `results/20261118-s3x-run-2b7741b3/`).

## Decision

1. S3 is complete, and with it the goal of the design documents, in this
   scope:
   - one compute job (`firmware/compute_add1.bin`, from the Mesa reference
     run), 1024 elements, buffers in VRAM owned by the driver;
   - Haiku runs as a QEMU guest with the card passed through by VFIO (the
     set-up of the whole project), not on bare metal;
   - each run is a single-use package with a validator; the driver is not a
     general runtime.
2. The project is complete to its designed scope. No task is active and no
   card run is approved.
3. Out of scope and still open: Q7 (host DMA visibility) and Q11 (0x100c10
   readback), `docs/OPEN_QUESTIONS.md`, which holds the proposed plan for both:
   one owned host DMA page, then D-a (0x100c10 readback), D-b and D-c (copies
   to and from host memory). It needs a change of the memory contract.
4. Not done: a separate macro review of the S2 and S3 work (decision 005).
   The user closed the milestone without it.
5. Any further goal (for example a persistent runtime or an LLM backend) needs
   its own decision.

## Causes of the S3 stops (for the record)

- The register list was uploaded before the golden stage read the two LTC
  values, so FECS wrote 0 into the L2 cache registers at the first load
  (`s3q` to `s3t`).
- The launch descriptor was mapped read-only; the card writes it during the
  launch (`s3u`, `s3v`).

Both were defects of this driver, not of the card or of Nouveau.
