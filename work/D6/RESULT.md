# Result D6: QMD comparison against reference run

## Summary

Built `tools/qmd_compare.py` — a tool that parses the Nouveau header at
runtime (no typed tables), runs `ref_qmd --words`, reads the reference
JSON, and compares every field.

## Result

155 fields match, 0 differ.

All non-zero fields verified:

| Field | Bits | Reference | Ours |
|-------|------|-----------|------|
| INVALIDATE_TEXTURE_HEADER_CACHE | [250:250] | 0x1 | 0x1 |
| INVALIDATE_TEXTURE_SAMPLER_CACHE | [251:251] | 0x1 | 0x1 |
| INVALIDATE_TEXTURE_DATA_CACHE | [252:252] | 0x1 | 0x1 |
| INVALIDATE_SHADER_DATA_CACHE | [253:253] | 0x1 | 0x1 |
| INVALIDATE_SHADER_CONSTANT_CACHE | [255:255] | 0x1 | 0x1 |
| PROGRAM_OFFSET | [287:256] | 0x7f100 | 0x7f100 |
| RELEASE_MEMBAR_TYPE | [366:366] | 0x1 | 0x1 |
| CWD_MEMBAR_TYPE | [369:368] | 0x1 | 0x1 |
| API_VISIBLE_CALL_LIMIT | [378:378] | 0x1 | 0x1 |
| CTA_RASTER_WIDTH | [415:384] | 0x10 | 0x10 |
| CTA_RASTER_HEIGHT | [431:416] | 0x1 | 0x1 |
| CTA_RASTER_DEPTH | [447:432] | 0x1 | 0x1 |
| CTA_THREAD_DIMENSION0 | [607:592] | 0x40 | 0x40 |
| CTA_THREAD_DIMENSION1 | [623:608] | 0x1 | 0x1 |
| CTA_THREAD_DIMENSION2 | [639:624] | 0x1 | 0x1 |
| CONSTANT_BUFFER_VALID(7) | [647:647] | 0x1 | 0x1 |
| L1_CONFIGURATION | [671:669] | 0x1 | 0x1 |
| CONSTANT_BUFFER_ADDR_LOWER(7) | [1407:1376] | 0x510000 | 0x510000 |
| CONSTANT_BUFFER_SIZE(7) | [1439:1423] | 0x800 | 0x800 |
| REGISTER_COUNT | [1503:1496] | 0x5 | 0x5 |
| SHADER_LOCAL_MEMORY_CRS_SIZE | [1527:1504] | 0x800 | 0x800 |
| SASS_VERSION | [1535:1528] | 0x30 | 0x30 |

## Differences

None.

## Outputs

- `tools/qmd_compare.py` — the comparison tool (standard library only)
- `analysis/qmd_compare.json` — structured comparison data
- `analysis/qmd_compare.md` — human-readable report
