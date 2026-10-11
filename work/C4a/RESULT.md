# C4a: Source provenance of driver constants

## Summary

Added source citations to every constant line in `src/mmu/PageTable.h`,
`src/mmu/PageTable.cpp`, `src/fifo/PushBuffer.h`, and `src/fifo/PushBuffer.cpp`.
Wrote `tools/provenance.py` and generated `docs/register-provenance.md`.

## Constant lines found: 24

| File | Lines | Cited | No-source |
|------|-------|-------|-----------|
| `src/fifo/PushBuffer.cpp` | 10 | 8 | 2 |
| `src/fifo/PushBuffer.h` | 4 | 4 | 0 |
| `src/mmu/PageTable.cpp` | 4 | 4 | 0 |
| `src/mmu/PageTable.h` | 10 | 9 | 1 |

### No-source lines (4)

| Line | Reason |
|------|--------|
| `src/fifo/PushBuffer.cpp:33` | 0x7ffc is max 13-bit value aligned to 4 (derived, not explicit in source) |
| `src/fifo/PushBuffer.cpp:39` | 0x1fff is max 13-bit count field value (derived) |
| `src/fifo/PushBuffer.cpp:257` | 0xff is 8-bit mask for address upper bits (standard arithmetic) |
| `src/mmu/PageTable.h:40` | 0 is all-zero unmapped PTE convention |

### Citations used

- `nouveau_dma.c:82-83` — GPFIFO entry encoding (lower/upper 32-bit split)
- `nouveau_dma.c:92,104` — USERD offsets (get at 0x88, put at 0x8c)
- `nouveau_dma.h:50` — NV50_DMA_PUSH_MAX_LENGTH = 0x7fffff
- `nvc0_winsys.h:68,74,81,87` — header base constants (0x20..0xa0)
- `nvkm/subdev/mmu/vmmgk104.c:29,40-51` — page-table geometry constants
- `nvkm/subdev/mmu/vmmgf100.c:35` — PTE decode formula

## Open questions

- The 4 `no source:` lines are plain arithmetic/conventions, not hardware facts.
- A mmiotrace in task C5 can verify which constants are actually exercised.

## Checks

- `make check`: 0 failures (9 test suites, all passing)
- `tools/provenance.py --check`: passes
- Deterministic: running the tool twice produces identical output
