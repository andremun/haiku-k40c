# S3LAUNCH: one compute job, then one timed matrix product

## Why and inputs

Last part of S3. Sources: Mesa `nvc0/nve4_compute.c`, `nvc0_screen.c`, `nvc0_program.c`,
`cla0c0qmd.h`; src/compute/LaunchDesc.*, src/fifo/PushBuffer.*; firmware/compute_add1.bin;
docs/08-compute-launch.md; `haiku-k40c-llm` results/20261021-nvc0-compile/.

## Outputs

- Push-buffer encoder for the compute class set-up of Mesa and for one launch.
- Code segment, descriptor, constant buffers 0 and 7 and data buffers in owned VRAM, mapped in the channel.
- Completion by GP_GET and by a result read; GR, FECS and MMU fault capture.
- Job 1: `output[i] = input[i] + 1`, 1024 elements. Job 2: one FP32 matrix product, timed.
- work/S3LAUNCH/{PLAN,FINDINGS,RESULT}.md.

## Checks and limits

Host tests against the Mesa sequence and the descriptor of the reference run.
Rung 1 (Linux) gives the push-buffer reference on the card day. Rungs 5 and 6.
