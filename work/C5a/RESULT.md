# Result C5a: Shader binary and launch descriptor of the reference run

## What was made

- `tools/shader_extract.py` — reads the log and shader source, writes three files. Supports `--check`.
- `firmware/compute_add1.bin` — 160 bytes, the compute shader binary (40 words, little-endian).
- `analysis/linux_run_shader.json` — JSON with log path, log line 120, size, words, SHA-256, renderer, version, source (7 lines), and 143 QMD fields.
- `firmware/compute_add1.md` — document with 5 sections (Source, How it was made, Code, Launch descriptor, Not known).

## Numbers

- Shader binary size: 160 bytes (0xa0)
- Word count: 40
- SHA-256: 02944d8f43830afad4f9d6538a1a26810085aea98a6520b09f7b5c9cce3ed417
- QMD fields: 143
- Launch descriptor table rows (non-zero/non-FALSE): 29
- Shader source lines: 7
- Renderer: NVF1
- Version: OpenGL ES 3.2 Mesa 25.2.8

## Launch descriptor fields (non-zero, non-FALSE)

INVALIDATE_TEXTURE_HEADER_CACHE, INVALIDATE_TEXTURE_SAMPLER_CACHE, INVALIDATE_TEXTURE_DATA_CACHE, INVALIDATE_SHADER_DATA_CACHE, INVALIDATE_SHADER_CONSTANT_CACHE, PROGRAM_OFFSET (0x7f100), RELEASE_MEMBAR_TYPE, CWD_MEMBAR_TYPE, API_VISIBLE_CALL_LIMIT, SHARED_MEMORY_BANK_MAPPING, SAMPLER_INDEX, CTA_RASTER_WIDTH (0x10), CTA_RASTER_HEIGHT (0x1), CTA_RASTER_DEPTH (0x1), CTA_THREAD_DIMENSION0 (0x40), CTA_THREAD_DIMENSION1 (0x1), CTA_THREAD_DIMENSION2 (0x1), CONSTANT_BUFFER_VALID(7), L1_CONFIGURATION, RELEASE0_REDUCTION_OP, RELEASE0_REDUCTION_FORMAT, RELEASE0_STRUCTURE_SIZE, RELEASE1_REDUCTION_OP, RELEASE1_REDUCTION_FORMAT, RELEASE1_STRUCTURE_SIZE, CONSTANT_BUFFER_ADDR_LOWER(7) (0x510000), CONSTANT_BUFFER_SIZE(7) (0x800), REGISTER_COUNT (0x5), SHADER_LOCAL_MEMORY_CRS_SIZE (0x800), SASS_VERSION (0x30).

## Open questions

- What does each instruction word in the shader binary mean (opcode, operands)?
- What is the exact QMD memory layout (field offsets and sizes)?
- How is the constant buffer at 0x510000 structured?
- Why is the renderer reported as "NVF1" rather than "GK110"?
