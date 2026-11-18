# S2COPY: one copy between two VRAM buffers on the S1 channel

## Why and inputs

Milestone S2 (docs/PHASES.md). Depends on the S1 channel (src/memstage/Channel.*,
docs/S1-CHANNEL-REVIEW.md). Sources: `nouveau_boa0b5.c` (the kernel copy sequence),
`include/nvhw/class/cla0b5.h` (methods and fields), `nvkm/engine/ce/gk104.c`
(error status), `nouveau_dma.h` (method headers). Decision 012.

## Outputs

- A push-buffer encoder for the copy sequence, with host tests against the class header.
- Two owned VRAM pages (source, destination) mapped in the channel address space.
- A channel phase after the NOP: bind the copy class, copy 4096 bytes, poll GP_GET,
  read the copy-engine status, read the destination, compare with the source pattern.
- Policy script, host validator and package changes; work/S2COPY/{PLAN,FINDINGS,RESULT}.md.

## Checks and limits

Host tests: pass, stall, launch error, wrong data, MMU fault, mutations. `make check`.
Native link, cardless rehearsal and package build are T7610 steps (decision 012).
No card run before ladder rung 3. No interrupt is enabled. Q7 is not used.
