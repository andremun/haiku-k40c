# S3LAUNCH plan: the native compute stage

Written 2026-11-12 after the GR program and its runner passed the trace oracle.
Tasks: docs/tasks/S3CTX.md, docs/tasks/S3LAUNCH.md. Nothing here ran on a card.

## What the stage does, in order

1. Unchanged A7 and batch-1 gates (as S1).
2. Allocate the owned VRAM records, write the images, build the channel page
   tables, expose USERD at BAR1 VA 0 (as S1).
3. FIFO set-up and bind of one channel on the GR runlist (TOP type 0).
4. GR program stage `gating`, then `start`, then `golden` (src/gr/Runner.cpp).
   Inputs: instance block, page pool, bundle and attribute buffer addresses in the
   channel, and the two MMU fault pages (the batch-1 records DebugWrite and
   DebugRead, `fb/gf100.c:44-64`). The context-pointer hook writes words 0x210
   and 0x214 of the instance block (`ctxgf100.c:1483-1487`).
5. Attach the context to the channel: stop, preempt, write 0x210/0x214, start
   (`chan.c` `nvkm_chan_cctx_bind`, `fifo/gk104.c:134-170`; trace step 11). The
   context memory is the one that received the golden image. Words 0x00 and 0x04
   of the image get the patch-list count and address (`gf100.c:336-338`).
6. One GPFIFO entry: compute class set-up and one launch. Poll GP_GET.
7. Wait for the result, read the output buffer through the slow window, compare.
8. Read the GR, FECS, FIFO and MMU fault status. Teardown as S1. GR stays started.

## Difference from Linux, by decision

- Linux copies the golden image into a new context for each channel (about
  80,000 reads and 80,000 writes of instance memory). This stage has one channel
  and uses the generation memory as its context. Same content, no copy.
- Linux writes constant buffer 7 and the descriptor with the UPLOAD methods of
  the compute class. This stage writes them into VRAM through the slow window
  before the launch. Same bytes in the same places.
- No interrupt is enabled. Completion is polled.

## Compute class sequence (Mesa 25.2.8, SOURCE_ONLY until rung 1 or rung 5)

Subchannel 1 (`nvc0_winsys.h:45`), class 0xa1c0. From `nve4_screen_compute_setup`
(`nve4_compute.c:44-178`) and `nve4_launch_grid` (`nve4_compute.c:785-890`):

1. Object bind. TEMP_ADDRESS (TLS). MP_TEMP_SIZE 0 and 1. LOCAL_BASE 0xff000000.
   SHARED_BASE 0xfe000000. CODE_ADDRESS. Method 0x310 = 0x400.
2. TIC_ADDRESS and TSC_ADDRESS with their limits. Method 0x248, 64 values
   `0x38000 | i`, i from 63 to 0, non-incrementing. SERIALIZE. TEX_CB_INDEX 7.
3. FLUSH (constant buffers).
4. LAUNCH_DESC_ADDRESS = descriptor address >> 8. LAUNCH = 3. SERIALIZE.

Job 1 is the shader of the reference run, `firmware/compute_add1.bin` (160 bytes,
it computed correctly on this card under Linux). It reads the buffer addresses
from constant buffer 7: buffer i at 0x2a0 + 16*i as address low, address high,
size, 0 (`nvc0_context.h:148`, `nve4_compute.c:427-434`); grid information at
0x100 (`nvc0_context.h:128`, `nve4_compute.c:504-511`). The descriptor is the one
of D5 and D6 (155 of 155 fields equal to the reference run).

## Records and channel addresses (software choices)

Channel VA window 0x10000000-0x17ffffff (one small-page table).

| Record | Bytes | Why this size |
|---|---:|---|
| Text | 0x80000 | Code at offset 0x7f100 as in the reference descriptor; 0x800 spare at the end (`nvc0_screen.c:706-710`) |
| Tls | per `nvc0_screen_resize_tls_area` (`nvc0_screen.c:648-668`) | Same formula as Mesa |
| Txc | 0x20000 | `nvc0_screen.c:1098` |
| Aux (constant buffer 7) | 0x1000 | 0x800 used |
| Qmd, Input, Output | 0x1000 each | 1024 elements of 4 bytes |
| PagePool | 0x8000 | `ctxgk110b.c:88` |
| Bundle | 0x3000 | `ctxgk110b.c:84` |
| Attrib | 0x14f000 | `ctxgf100.c:1067`, 15 TPCs, page aligned |
| Context | 0xcf000 | 0x80000 reserved + 0x4ea00 image (`ctxgf100.c:1436,1474`); trace MAP 24 has this size |
| MmioList | 0x1000 | `gf100.c:455` |

With the 7 batch-1 and 7 channel records: 26. The ledger capacity becomes 32.

## Work packages

1. `tools/gr/launch.py`: layout, push words, descriptor, constant buffer 7,
   code placement; `--check`; host test against the Mesa sequence and D6.
2. Ledger capacity and roles; generic region table instead of fixed role arrays.
3. `src/gr/Stage.cpp`: the stage above over Io, Upload, Mapper, Runner.
4. Policy: the GR program as the allow-list (op by op), GR runlist channel
   script, status reads.
5. Host test: simulated card that checks tables, images and order.
6. Validator, package tools (`K40_MEM_STAGE=s3a|s3b`), rehearsal on the T7610.
7. Rung 1 job: the same push words under Linux through libdrm-nouveau, to
   separate launch errors from bring-up errors.

## Known risks

- The compute sequence has no trace to compare with (user-space writes are not in
  an mmiotrace). Rung 1 is its only check before rung 5.
- Whether a compute-only channel needs any state of the 3D class: UNKNOWN.
- The stage writes about 1 MiB of zeros through the slow window for the context
  memory. Its time must fit the stage budget; S1 timings are in the run journal.
- A second run after a failed one needs a guest restart (GR is not reset here).
