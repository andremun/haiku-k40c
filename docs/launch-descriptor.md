# Launch Descriptor (Task D5)

A compute job on GK110 (K40c) is started by a 256-byte **launch descriptor**
(QMD — Queue Message Descriptor) written to GPU memory, followed by two MMIO
methods that tell the GPU where it is and command the launch.  This document
covers the QMD layout, the constant-buffer helpers, and the launch encoding.

Source: Mesa Nouveau driver (`reference/mesa/src/gallium/drivers/nouveau/nvc0/`),
with header `cla0c0qmd.h` defining field bit positions and `nve4_compute.c`
defining the assignment sequence.

## Constants

| Name | Value | Source |
|------|-------|--------|
| `kComputeClass` | `0xa1c0` | `nv_object.xml.h:209` |
| `kComputeSubchannel` | `1` (CP) | Mesa `SUBC_CP` |
| `kQmdBytes` | `256` | 256 × 32-bit words |

## QMD Field Table

All bit positions are from `cla0c0qmd.h` (`QMDV00_06`). `nve4_compute_setup_launch_desc`
(`nve4_compute.c:573-632`) assigns these fields in order.  Fields not listed
below are left at zero by Mesa and must remain zero in the Haiku descriptor.

| # | Field | Bits | Type | Default value | Source line |
|---|-------|------|------|---------------|-------------|
| 1 | INVALIDATE_TEXTURE_HEADER_CACHE | 250:250 | flag | `1` (TRUE) | nve4_compute.c:581 |
| 2 | INVALIDATE_TEXTURE_SAMPLER_CACHE | 251:251 | flag | `1` (TRUE) | nve4_compute.c:582 |
| 3 | INVALIDATE_TEXTURE_DATA_CACHE | 252:252 | flag | `1` (TRUE) | nve4_compute.c:583 |
| 4 | INVALIDATE_SHADER_DATA_CACHE | 253:253 | flag | `1` (TRUE) | nve4_compute.c:584 |
| 5 | INVALIDATE_SHADER_CONSTANT_CACHE | 255:255 | flag | `1` (TRUE) | nve4_compute.c:585 |
| 6 | RELEASE_MEMBAR_TYPE | 366:366 | enum | `FE_SYSMEMBAR` | nve4_compute.c:586 |
| 7 | CWD_MEMBAR_TYPE | 369:368 | enum | `L1_SYSMEMBAR` | nve4_compute.c:587 |
| 8 | API_VISIBLE_CALL_LIMIT | 378:378 | enum | `NO_CHECK` | nve4_compute.c:588 |
| 9 | SASS_VERSION | 1535:1528 | val | `0x30` (GK110) | nve4_compute.c:589 |
| 10 | PROGRAM_OFFSET | 287:256 | val | `codeOffset` (32-bit) | nve4_compute.c:591 |
| 11 | CTA_RASTER_WIDTH | 415:384 | val | `grid[0]` (default 1) | nve4_compute.c:593 |
| 12 | CTA_RASTER_HEIGHT | 431:416 | val | `grid[1]` (default 1) | nve4_compute.c:594 |
| 13 | CTA_RASTER_DEPTH | 447:432 | val | `grid[2]` (default 1) | nve4_compute.c:595 |
| 14 | CTA_THREAD_DIMENSION0 | 607:592 | val | `block[0]` (default 1) | nve4_compute.c:596 |
| 15 | CTA_THREAD_DIMENSION1 | 623:608 | val | `block[1]` (default 1) | nve4_compute.c:597 |
| 16 | CTA_THREAD_DIMENSION2 | 639:624 | val | `block[2]` (default 1) | nve4_compute.c:598 |
| 17 | SHARED_MEMORY_SIZE | 561:544 | val | `align(sharedMemSize, 0x100)` (18-bit) | nve4_compute.c:600 |
| 18 | SHADER_LOCAL_MEMORY_LOW_SIZE | 1463:1440 | val | `localMemLow & 0xfffff0` (24-bit) | nve4_compute.c:601 |
| 19 | SHADER_LOCAL_MEMORY_HIGH_SIZE | 1495:1472 | val | `0` (always) | nve4_compute.c:602 |
| 20 | SHADER_LOCAL_MEMORY_CRS_SIZE | 1527:1504 | val | `0x800` (always) | nve4_compute.c:603 |
| 21 | L1_CONFIGURATION | 671:669 | val | `1`–`3` (16/32/48 KB) | nve4_compute.c:606,610,613 |
| 22 | REGISTER_COUNT | 1503:1496 | val | `numGprs` (8-bit) | nve4_compute.c:616 |
| 23 | BARRIER_COUNT | 1471:1467 | val | `numBarriers` (5-bit) | nve4_compute.c:617 |

## What Mesa Leaves at Zero

Mesa's `nve4_compute_setup_launch_desc` assigns only the 23 fields above
up to and including `BARRIER_COUNT`.  All other QMD bits are zero by virtue
of the descriptor being allocated with `calloc`.  Notable zero fields include:
- `PRIORITY` (367:367), `DEPENDENT_QMD` (248:248), `PERF_COUNT` flags
- All constant-buffer fields (CB0–CB7) which are set separately
- `SYSTEM_PRIORITY`, `DEPENDENT_MASK`, `RESERVED_ZERO` regions
- Words 16–24 of the QMD (bits 512–799) used for CB address/size on GK110

## Constant Buffers

`setConstantBuffer(Qmd&, index, address, size)` assigns 4 fields per buffer
(8 buffers, index 0–7), each occupying a 64-bit slot starting at bit 928:

| Field | Bits | Width | Source |
|-------|------|-------|--------|
| CONSTANT_BUFFER_ADDR_LOWER | 928+i*64 … 959+i*64 | 32 | cla0c0qmd.h:203 |
| CONSTANT_BUFFER_ADDR_UPPER | 960+i*64 … 967+i*64 | 8 | cla0c0qmd.h:206 |
| CONSTANT_BUFFER_SIZE | 975+i*64 … 991+i*64 | 17 | cla0c0qmd.h:209 |
| CONSTANT_BUFFER_VALID | 640+i | 1 | cla0c0qmd.h:200 |

Validation: `index` must be 0–7, `address` low 8 bits must be zero, address
must fit 40 bits, `size` must fit 17 bits (`0x1FFFF`).  On any error the
descriptor is left unchanged.

## Launch Methods

`encodeLaunch(descGpuAddr)` emits 3 method push-buffer entries (6 words total):

| # | Method | Offset | Value | Source |
|---|--------|--------|-------|--------|
| 1 | `LAUNCH_DESC_ADDRESS` | `0x02b4` | `descGpuAddr >> 8` | nve4_compute.xml.h:165 |
| 2 | `LAUNCH` | `0x02bc` | `3` | nve4_compute.xml.h:170 |
| 3 | `NV50_GRAPH_SERIALIZE` | — | `0` | nv_object.xml.h:284 |

The address is shifted right by 8 because the GPU stores 256-byte-aligned
addresses in 32-bit words (the low 8 bits are implicit).  `LAUNCH` value 3
is the GK110 compute launch opcode.  `NV50_GRAPH_SERIALIZE` with value 0 is
a fence to ensure the descriptor is fully written before launch.

Validation: the low 8 bits of `descGpuAddr` must be zero (256-byte alignment),
and the address must fit 40 bits.

## Not Covered

The following are required for S3 but are out of scope for this task:

1. **Descriptor upload** — The `UPLOAD_*` method sequence (`UPLOAD_DST_ADDRESS_HIGH`,
   `UPLOAD_LINE_LENGTH_IN`, `UPLOAD_EXEC`, `FLUSH`) that copies the QMD from
   host memory to GPU-resident memory (`nve4_compute.c:843-856`).  These use
   the upload engine, not the compute subchannel.
2. **Setup methods** — `nve4_screen_compute_setup` (lines 51–174) which programs
   the compute channel state: TLS address, code address, TIC/TSC tables,
   constant-buffer address, etc.  These run once per context, not per dispatch.
3. **Shader code upload** — The text section (SASS) upload to GPU memory, which
   is separate from the QMD.  `CODE_ADDRESS_HIGH` in setup points to it.
4. **Dependent QMDs** — `DEPENDENT_QMD` and `DEPENDENT_MASK` fields for chained
   launches (not used in the simple compute path).
5. **Performance counters** — `PERF_COUNT` and related fields in the QMD.
6. **GK20A/GK210 path** — Different launch sequence and QMD version.

## Tests

- `tests/test_launchdesc.cpp` — 16 test categories, 56 CHECKs (cross-word
  fields, max-fit, overflow rejection, all 8 constant buffers, encode/decode
  round-trip, boundary, wide fields, error preservation, default job).
- `tests/accept/d5_accept.cpp` — 101 acceptance checks generated from
  `cla0c0qmd.h` bit positions.
