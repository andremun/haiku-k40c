# Compute Launch Path (GK110 / K40c)

Source: Mesa Nouveau driver, pinned in `reference/mesa/`.

## Compute Class

- Class: `0x0000a1c0` (`NVF0_COMPUTE_CLASS`)
- Source: `src/gallium/drivers/nouveau/nv_object.xml.h`

## Setup Methods (`nve4_screen_compute_setup`)

| # | Method | Offset | Macro | Count | Value | Line |
|---|--------|--------|-------|-------|-------|------|
| 1 | `NV01_SUBCHAN_OBJECT` | `N/A` | `BEGIN_NVC0` | 1 | screen->compute->oclass | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:51 |
| 2 | `TEMP_ADDRESS_HIGH` | `0x00000790` | `BEGIN_NVC0` | 2 | screen->tls->offset | screen->tls->offset | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:54 |
| 3 | `MP_TEMP_SIZE_HIGH` | `0x000002e4` | `BEGIN_NVC0` | 3 | screen->tls->size / screen->mp_count | (screen->tls->size / screen->mp_count | 0xff | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:61 |
| 4 | `MP_TEMP_SIZE_HIGH` | `0x000002e4` | `BEGIN_NVC0` | 3 | screen->tls->size / screen->mp_count | (screen->tls->size / screen->mp_count | 0xff | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:66 |
| 5 | `LOCAL_BASE` | `0x0000077c` | `BEGIN_NVC0` | 1 | 0xff << 24 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:78 |
| 6 | `SHARED_BASE` | `0x00000214` | `BEGIN_NVC0` | 1 | 0xfe << 24 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:80 |
| 7 | `CODE_ADDRESS_HIGH` | `0x00001608` | `BEGIN_NVC0` | 2 | screen->text->offset | screen->text->offset | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:83 |
| 8 | `0x2a0` | `N/A` | `BEGIN_NVC0` | 2 | 0xfeULL << 24 | 0xfeULL << 24 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:87 |
| 9 | `0x7b0` | `N/A` | `BEGIN_NVC0` | 2 | 0xffULL << 24 | 0xffULL << 24 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:90 |
| 10 | `0x0310` | `N/A` | `BEGIN_NVC0` | 1 | (obj_class >= NVF0_COMPUTE_CLASS | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:95 |
| 11 | `TIC_ADDRESS_HIGH` | `0x00001574` | `BEGIN_NVC0` | 3 | screen->txc->offset | screen->txc->offset | NVC0_TIC_MAX_ENTRIES - 1 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:99 |
| 12 | `TSC_ADDRESS_HIGH` | `0x0000155c` | `BEGIN_NVC0` | 3 | screen->txc->offset + 65536 | screen->txc->offset + 65536 | NVC0_TSC_MAX_ENTRIES - 1 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:103 |
| 13 | `0x0248` | `N/A` | `BEGIN_NIC0` | 64 | 0x38000 | i | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:113 |
| 14 | `NV50_GRAPH_SERIALIZE` | `N/A` | `IMMED_NVC0` | 0 | N/A | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:116 |
| 15 | `TEX_CB_INDEX` | `0x00002608` | `BEGIN_NVC0` | 1 | 7 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:119 |
| 16 | `UPLOAD_DST_ADDRESS_HIGH` | `0x00000188` | `BEGIN_NVC0` | 2 | address + NVC0_CB_AUX_MS_INFO | address + NVC0_CB_AUX_MS_INFO | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:131 |
| 17 | `UPLOAD_LINE_LENGTH_IN` | `0x00000180` | `BEGIN_NVC0` | 2 | 64 | 1 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:134 |
| 18 | `UPLOAD_EXEC` | `0x000001b0` | `BEGIN_1IC0` | 17 | NVE4_COMPUTE_UPLOAD_EXEC_LINEAR | (0x20 << 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 2 | 0 | 3 | 0 | 2 | 1 | 3 | 1 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:137 |
| 19 | `FLUSH` | `0x00001698` | `BEGIN_NVC0` | 1 | NVE4_COMPUTE_FLUSH_CB | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:174 |

## Launch Descriptor Fields (`nve4_compute_setup_launch_desc`)

| # | Field | Bits | Type | Value | Line |
|---|-------|------|------|-------|------|
| 1 | `INVALIDATE_TEXTURE_HEADER_CACHE` | 250:250 | `DEF_SET` | `TRUE` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:581 |
| 2 | `INVALIDATE_TEXTURE_SAMPLER_CACHE` | 251:251 | `DEF_SET` | `TRUE` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:582 |
| 3 | `INVALIDATE_TEXTURE_DATA_CACHE` | 252:252 | `DEF_SET` | `TRUE` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:583 |
| 4 | `INVALIDATE_SHADER_DATA_CACHE` | 253:253 | `DEF_SET` | `TRUE` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:584 |
| 5 | `INVALIDATE_SHADER_CONSTANT_CACHE` | 255:255 | `DEF_SET` | `TRUE` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:585 |
| 6 | `RELEASE_MEMBAR_TYPE` | 366:366 | `DEF_SET` | `FE_SYSMEMBAR` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:586 |
| 7 | `CWD_MEMBAR_TYPE` | 369:368 | `DEF_SET` | `L1_SYSMEMBAR` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:587 |
| 8 | `API_VISIBLE_CALL_LIMIT` | 378:378 | `DEF_SET` | `NO_CHECK` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:588 |
| 9 | `SASS_VERSION` | 1535:1528 | `VAL_SET` | `0x30` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:589 |
| 10 | `PROGRAM_OFFSET` | 287:256 | `VAL_SET` | `cp->code_base` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:591 |
| 11 | `CTA_RASTER_WIDTH` | 415:384 | `VAL_SET` | `info->grid[0]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:593 |
| 12 | `CTA_RASTER_HEIGHT` | 431:416 | `VAL_SET` | `info->grid[1]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:594 |
| 13 | `CTA_RASTER_DEPTH` | 447:432 | `VAL_SET` | `info->grid[2]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:595 |
| 14 | `CTA_THREAD_DIMENSION0` | 607:592 | `VAL_SET` | `info->block[0]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:596 |
| 15 | `CTA_THREAD_DIMENSION1` | 623:608 | `VAL_SET` | `info->block[1]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:597 |
| 16 | `CTA_THREAD_DIMENSION2` | 639:624 | `VAL_SET` | `info->block[2]` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:598 |
| 17 | `SHARED_MEMORY_SIZE` | 561:544 | `VAL_SET` | `align(shared_size, 0x100` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:600 |
| 18 | `SHADER_LOCAL_MEMORY_LOW_SIZE` | 1463:1440 | `VAL_SET` | `cp->hdr[1] & 0xfffff0` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:601 |
| 19 | `SHADER_LOCAL_MEMORY_HIGH_SIZE` | 1495:1472 | `VAL_SET` | `0` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:602 |
| 20 | `SHADER_LOCAL_MEMORY_CRS_SIZE` | 1527:1504 | `VAL_SET` | `0x800` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:603 |
| 21 | `REGISTER_COUNT` | 1503:1496 | `VAL_SET` | `cp->num_gprs` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:616 |
| 22 | `BARRIER_COUNT` | 1471:1467 | `VAL_SET` | `cp->num_barriers` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:617 |

## Launch Methods (`nve4_launch_grid`, GK110 path)

| # | Method | Offset | Macro | Count | Value | Line |
|---|--------|--------|-------|-------|-------|------|
| 1 | `UPLOAD_DST_ADDRESS_HIGH` | `0x00000188` | `BEGIN_NVC0` | 2 | desc_gpuaddr | desc_gpuaddr | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:846 |
| 2 | `UPLOAD_LINE_LENGTH_IN` | `0x00000180` | `BEGIN_NVC0` | 2 | 256 | 1 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:849 |
| 3 | `LAUNCH_DESC_ADDRESS` | `0x000002b4` | `BEGIN_NVC0` | 1 | desc_gpuaddr >> 8 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:872 |
| 4 | `LAUNCH` | `0x000002bc` | `BEGIN_NVC0` | 1 | 0x3 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:875 |
| 5 | `0x02c0` | `N/A` | `BEGIN_NIC0` | 2 | 1 | 2 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:878 |
| 6 | `NV50_GRAPH_SERIALIZE` | `N/A` | `BEGIN_NVC0` | 1 | 0 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:882 |

## Kernel Requirements

| # | Need | Source |
|---|------|--------|
| 1 | SASS version 0x30 (GK110 compute shader ISA) | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:589 |
| 2 | QMD v0.0.6 format (a0c0 class) | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:574 |
| 3 | 512-byte launch descriptor buffer (256-word QMD) | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:853 |
| 4 | MP temporary memory per-SM (screen->tls) | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:55 |
| 5 | TIC (texture instruction cache) table | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:99 |
| 6 | TSC (texture sampler cache) table | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:103 |
| 7 | Unified constant buffer for compute | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:131 |
| 8 | Text section (code) with GPU-addressable offset | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:83 |

## Shader Code Delivery (CODE_ADDRESS)

The shader code (SASS text section) reaches the GPU through CODE_ADDRESS_HIGH in nve4_screen_compute_setup (line 83), which sets screen->text->offset. In nve4_launch_grid (line 872), the LAUNCH_DESC_ADDRESS method receives desc_gpuaddr pointing to the QMD descriptor buffer. The QMD's PROGRAM_OFFSET field (set at line 591 via cp->code_base) contains the GPU address of the shader code relative to the descriptor. The kernel driver resolves these offsets to actual GPU addresses via the channel's address space.

## Other-Chip Branches (not taken on GK110)

| Chip | Condition | Description | Line |
|------|-----------|-------------|------|
| GM107/GK20A | `oclass < NVF0_COMPUTE_CLASS` | Uses SUBC_CP(0x02c4) and different upload paths | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:108 |
| GV100 / GA102+ | `oclass >= GV100_COMPUTE_CLASS` | Uses SUBC_CP(0x2a0)/(0x7b0) for local/shared base; MP_TEMP_SIZE_HIGH(1) skipped | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:65 |
| GP100+ | `oclass >= GP100_COMPUTE_CLASS` | Uses gp100_compute_setup_launch_desc (C0C0 class), UPLOAD_EXEC with 0x08 << 1, and SUBC_CP(0x02c0) for launch | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:821 |
| GA102+ | `oclass >= GA102_COMPUTE_CLASS` | Uses SUBC_CP(0x02c0) with values (1, 2) instead of LAUNCH with 0x3 | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:874 |
