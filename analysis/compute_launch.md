# Compute Launch Path (GK110 / K40c)

Source: Mesa Nouveau driver, pinned in `reference/mesa/`.

## Compute Class

- Class: `0x0000a1c0` (`NVF0_COMPUTE_CLASS`)
- Source: `reference/mesa/src/gallium/drivers/nouveau/nv_object.xml.h`

## Setup Methods (`nve4_screen_compute_setup`)

| # | Method | Offset | Macro | Count | Line |
|---|--------|--------|-------|-------|------|
| 1 | `NV01_SUBCHAN_OBJECT` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:51 |
| 2 | `TEMP_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:54 |
| 3 | `MP_TEMP_SIZE_HIGH` | `N/A` | `BEGIN_NVC0` | 3 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:61 |
| 4 | `MP_TEMP_SIZE_HIGH` | `N/A` | `BEGIN_NVC0` | 3 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:66 |
| 5 | `LOCAL_BASE` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:78 |
| 6 | `SHARED_BASE` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:80 |
| 7 | `CODE_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:83 |
| 8 | `0x0x2a0` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:87 |
| 9 | `0x0x7b0` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:90 |
| 10 | `0x0x0310` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:95 |
| 11 | `TIC_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 3 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:99 |
| 12 | `TSC_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 3 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:103 |
| 13 | `0x0x0248` | `N/A` | `BEGIN_NIC0` | 64 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:113 |
| 14 | `NV50_GRAPH_SERIALIZE` | `N/A` | `IMMED_NVC0` | 0 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:116 |
| 15 | `TEX_CB_INDEX` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:119 |
| 16 | `0x0x02c4` | `N/A` | `IMMED_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:125 |
| 17 | `UPLOAD_DST_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:131 |
| 18 | `UPLOAD_LINE_LENGTH_IN` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:134 |
| 19 | `UPLOAD_EXEC` | `N/A` | `BEGIN_1IC0` | 17 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:137 |
| 20 | `UPLOAD_DST_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:157 |
| 21 | `UPLOAD_LINE_LENGTH_IN` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:160 |
| 22 | `UPLOAD_EXEC` | `N/A` | `BEGIN_1IC0` | 8 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:163 |
| 23 | `FLUSH` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:174 |

## Launch Descriptor Fields (`nve4_compute_setup_launch_desc`)

| # | Field | Bits | Type | Value | Line |
|---|-------|------|------|-------|------|
| 1 | `INVALIDATE_TEXTURE_HEADER_CACHE` | 250:250 | `DEF_SET` | `TRUE` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:581 |
| 2 | `INVALIDATE_TEXTURE_SAMPLER_CACHE` | 251:251 | `DEF_SET` | `TRUE` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:582 |
| 3 | `INVALIDATE_TEXTURE_DATA_CACHE` | 252:252 | `DEF_SET` | `TRUE` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:583 |
| 4 | `INVALIDATE_SHADER_DATA_CACHE` | 253:253 | `DEF_SET` | `TRUE` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:584 |
| 5 | `INVALIDATE_SHADER_CONSTANT_CACHE` | 255:255 | `DEF_SET` | `TRUE` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:585 |
| 6 | `RELEASE_MEMBAR_TYPE` | 366:366 | `DEF_SET` | `FE_SYSMEMBAR` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:586 |
| 7 | `CWD_MEMBAR_TYPE` | 369:368 | `DEF_SET` | `L1_SYSMEMBAR` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:587 |
| 8 | `API_VISIBLE_CALL_LIMIT` | 378:378 | `DEF_SET` | `NO_CHECK` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:588 |
| 9 | `SASS_VERSION` | 1535:1528 | `VAL_SET` | `0x30` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:589 |
| 10 | `PROGRAM_OFFSET` | 287:256 | `VAL_SET` | `cp->code_base` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:591 |
| 11 | `CTA_RASTER_WIDTH` | 415:384 | `VAL_SET` | `info->grid[0]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:593 |
| 12 | `CTA_RASTER_HEIGHT` | 431:416 | `VAL_SET` | `info->grid[1]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:594 |
| 13 | `CTA_RASTER_DEPTH` | 447:432 | `VAL_SET` | `info->grid[2]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:595 |
| 14 | `CTA_THREAD_DIMENSION0` | 607:592 | `VAL_SET` | `info->block[0]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:596 |
| 15 | `CTA_THREAD_DIMENSION1` | 623:608 | `VAL_SET` | `info->block[1]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:597 |
| 16 | `CTA_THREAD_DIMENSION2` | 639:624 | `VAL_SET` | `info->block[2]` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:598 |
| 17 | `SHARED_MEMORY_SIZE` | 561:544 | `VAL_SET` | `align(shared_size, 0x100` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:600 |
| 18 | `SHADER_LOCAL_MEMORY_LOW_SIZE` | 1463:1440 | `VAL_SET` | `cp->hdr[1] & 0xfffff0` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:601 |
| 19 | `SHADER_LOCAL_MEMORY_HIGH_SIZE` | 1495:1472 | `VAL_SET` | `0` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:602 |
| 20 | `SHADER_LOCAL_MEMORY_CRS_SIZE` | 1527:1504 | `VAL_SET` | `0x800` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:603 |
| 21 | `REGISTER_COUNT` | 1503:1496 | `VAL_SET` | `cp->num_gprs` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:616 |
| 22 | `BARRIER_COUNT` | 1471:1467 | `VAL_SET` | `cp->num_barriers` | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:617 |

## Launch Methods (`nve4_launch_grid`, GK110 path)

| # | Method | Offset | Macro | Count | Line |
|---|--------|--------|-------|-------|------|
| 1 | `UPLOAD_DST_ADDRESS_HIGH` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:846 |
| 2 | `UPLOAD_LINE_LENGTH_IN` | `N/A` | `BEGIN_NVC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:849 |
| 3 | `LAUNCH_DESC_ADDRESS` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:872 |
| 4 | `LAUNCH` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:875 |
| 5 | `0x0x02c0` | `N/A` | `BEGIN_NIC0` | 2 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:878 |
| 6 | `NV50_GRAPH_SERIALIZE` | `N/A` | `BEGIN_NVC0` | 1 | reference/mesa/src/gallium/drivers/nouveau/nvc0/nve4_compute.c:882 |

## Kernel Requirements

- SASS version 0x30 (GK110 compute shader ISA)
- QMD v0.0.6 format (a0c0 class)
- 512-byte launch descriptor buffer (256-word QMD)
- MP temporary memory per-SM (screen->tls)
- TIC (texture instruction cache) table
- TSC (texture sampler cache) table
- Unified constant buffer for compute
- Text section (code) with GPU-addressable offset
