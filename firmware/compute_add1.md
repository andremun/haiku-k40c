## Source
```glsl
#version 310 es
layout(local_size_x = 64) in;
layout(std430, binding = 0) readonly buffer In { uint a[]; } inbuf;
layout(std430, binding = 1) writeonly buffer Out { uint a[]; } outbuf;
void main() {
	uint i = gl_GlobalInvocationID.x;
	outbuf.a[i] = inbuf.a[i] + 1u;
}
```

Source file: `tools/guest/files/compute_test.c` (variable `kSource`).

## How it was made

- **Renderer:** NVF1
- **Mesa version:** OpenGL ES 3.2 Mesa 25.2.8
- **Command:** `./compute_test`
- **Environment:** `NV50_PROG_DEBUG=1` and `NV50_PROG_CHIPSET=0xf1`
- **Log:** `reference/linux-run/compute_test.log` line 120

## Code

Size: 160 bytes
SHA-256: 02944d8f43830afad4f9d6538a1a26810085aea98a6520b09f7b5c9cce3ed417

```
a0a09c80 0810b0a0 129c0002 86400000 109c0006 86400000 031c0001 c2400400
009c0002 e0800000 011c0009 c2400400 541c0802 608400e0 549ffc06 608040e0
a080b0a0 0810b010 021c080d c0800000 551c0c1e 5b401ce0 00200000 c4800000
0003c002 74000000 009c0011 c0800000 561c0802 608400e0 569ffc06 608040e0
00b810b0 08000000 571c0c1e 5b401ce0 00200010 e4800000 001c003c 18000000
```

## Launch descriptor

| Field | Value |
|-------|-------|
| INVALIDATE_TEXTURE_HEADER_CACHE | TRUE |
| INVALIDATE_TEXTURE_SAMPLER_CACHE | TRUE |
| INVALIDATE_TEXTURE_DATA_CACHE | TRUE |
| INVALIDATE_SHADER_DATA_CACHE | TRUE |
| INVALIDATE_SHADER_CONSTANT_CACHE | TRUE |
| PROGRAM_OFFSET | 0x7f100 |
| RELEASE_MEMBAR_TYPE | FE_SYSMEMBAR |
| CWD_MEMBAR_TYPE | L1_SYSMEMBAR |
| API_VISIBLE_CALL_LIMIT | NO_CHECK |
| SHARED_MEMORY_BANK_MAPPING | FOUR_BYTES_PER_BANK |
| SAMPLER_INDEX | INDEPENDENTLY |
| CTA_RASTER_WIDTH | 0x10 |
| CTA_RASTER_HEIGHT | 0x1 |
| CTA_RASTER_DEPTH | 0x1 |
| CTA_THREAD_DIMENSION0 | 0x40 |
| CTA_THREAD_DIMENSION1 | 0x1 |
| CTA_THREAD_DIMENSION2 | 0x1 |
| CONSTANT_BUFFER_VALID(7) | TRUE |
| L1_CONFIGURATION | DIRECTLY_ADDRESSABLE_MEMORY_SIZE_16KB |
| RELEASE0_REDUCTION_OP | RED_ADD |
| RELEASE0_REDUCTION_FORMAT | UNSIGNED_32 |
| RELEASE0_STRUCTURE_SIZE | FOUR_WORDS |
| RELEASE1_REDUCTION_OP | RED_ADD |
| RELEASE1_REDUCTION_FORMAT | UNSIGNED_32 |
| RELEASE1_STRUCTURE_SIZE | FOUR_WORDS |
| CONSTANT_BUFFER_ADDR_LOWER(7) | 0x510000 |
| CONSTANT_BUFFER_SIZE(7) | 0x800 |
| REGISTER_COUNT | 0x5 |
| SHADER_LOCAL_MEMORY_CRS_SIZE | 0x800 |
| SASS_VERSION | 0x30 |

## Not known

- What each instruction word in the shader binary means (opcode, operands).
- The meaning of the QMD field sizes and layout in memory.
- How the constant buffer at address 0x510000 is laid out.
