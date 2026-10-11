# Register Provenance

Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`
(excluding `src/hw/`) is listed below with its source citation.

Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).

## src/fifo/PushBuffer.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/fifo/PushBuffer.cpp:33` | `if (method & 3 \|\| method > 0x7ffc)` | no source: 0x7ffc is max 13-bit value aligned to 4; nvc0_winsys.h shifts mthd >> 2 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:39` | `if (count > 0x1fff)` | no source: 0x1fff is max 13-bit value for the count field;    nvc0_winsys.h uses (size << 16) with 13-bit field | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:45` | `case HeaderType::INCREASING:     base = 0x20000000u; break;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:68 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:46` | `case HeaderType::NON_INCREASING: base = 0x60000000u; break;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:74 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:47` | `case HeaderType::IMMEDIATE:      base = 0x80000000u; break;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:81 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:48` | `case HeaderType::INCREASE_ONCE:  base = 0xa0000000u; break;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:87 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:74` | `h.method = (word & 0x1fff) << 2;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:68 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:75` | `h.count = (word >> 16) & 0x1fff;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:68 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:244` | `e.word0 = static_cast<uint32_t>(addr & 0xffffffffULL);` | nouveau_dma.c:82 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:246` | `e.word1 = static_cast<uint32_t>((addr >> 32) & 0xffffffffULL) \|` | nouveau_dma.c:83 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:257` | `info.addr = static_cast<uint64_t>(e.word1 & 0xff) << 32 \| e.word0;` | no source: 0xff is just 8-bit mask for address upper bits | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:259` | `info.lengthBytes = (e.word1 >> 8) & 0x7fffff;` | nouveau_dma.h:50 | SOURCE_ONLY |

## src/fifo/PushBuffer.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/fifo/PushBuffer.h:23` | `constexpr uint32_t kPushMaxLength = 0x7fffff;` | nouveau_dma.h:50 | SOURCE_ONLY |
| `src/fifo/PushBuffer.h:26` | `constexpr unsigned kUserdGpGet = 0x88;` | nouveau_dma.c:92 | SOURCE_ONLY |
| `src/fifo/PushBuffer.h:27` | `constexpr unsigned kUserdGpPut = 0x8c;` | nouveau_dma.c:104 | SOURCE_ONLY |
| `src/fifo/PushBuffer.h:30` | `constexpr unsigned kGpEntryBytes = 8;` | nouveau_dma.c:82 | SOURCE_ONLY |

## src/mmu/PageTable.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/mmu/PageTable.cpp:90` | `uint32_t pde = static_cast<uint32_t>((va >> kPdeShift) & 0x1fff);` | nvkm/subdev/mmu/vmmgk104.c:42 | SOURCE_ONLY |
| `src/mmu/PageTable.cpp:92` | `uint32_t lpte = static_cast<uint32_t>((va >> kLargeShift) & 0x3ff);` | nvkm/subdev/mmu/vmmgk104.c:48 | SOURCE_ONLY |
| `src/mmu/PageTable.cpp:94` | `uint32_t spte = static_cast<uint32_t>((va >> kSmallShift) & 0x7fff);` | nvkm/subdev/mmu/vmmgk104.c:41 | SOURCE_ONLY |
| `src/mmu/PageTable.cpp:364` | `uint64_t phys = (pte & 0xfffffff0ULL) << 8;` | nvkm/subdev/mmu/vmmgf100.c:35 | SOURCE_ONLY |

## src/mmu/PageTable.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/mmu/PageTable.h:29` | `static constexpr uint32_t kVaBits = 40;` | nvkm/subdev/mmu/vmmgk104.c:40 | SOURCE_ONLY |
| `src/mmu/PageTable.h:30` | `static constexpr uint32_t kSmallShift = 12;` | nvkm/subdev/mmu/vmmgk104.c:41 | SOURCE_ONLY |
| `src/mmu/PageTable.h:31` | `static constexpr uint32_t kLargeShift = 17;` | nvkm/subdev/mmu/vmmgk104.c:48 | SOURCE_ONLY |
| `src/mmu/PageTable.h:32` | `static constexpr uint32_t kPdeShift = 27;` | nvkm/subdev/mmu/vmmgk104.c:42 | SOURCE_ONLY |
| `src/mmu/PageTable.h:35` | `static constexpr uint32_t kPdEntries = 1u << 13;` | nvkm/subdev/mmu/vmmgk104.c:41 | SOURCE_ONLY |
| `src/mmu/PageTable.h:36` | `static constexpr uint32_t kSptEntries = 1u << 15;` | nvkm/subdev/mmu/vmmgk104.c:41 | SOURCE_ONLY |
| `src/mmu/PageTable.h:37` | `static constexpr uint32_t kLptEntries = 1u << 10;` | nvkm/subdev/mmu/vmmgk104.c:48 | SOURCE_ONLY |
| `src/mmu/PageTable.h:40` | `static constexpr uint64_t kPteUnmapped = 0;` | no source: all-zero is a zero-initialisation convention | SOURCE_ONLY |
| `src/mmu/PageTable.h:43` | `static constexpr uint64_t kLptInvalid = 2;` | nvkm/subdev/mmu/vmmgk104.c:29 | SOURCE_ONLY |

## Open

The following constant lines have no source citation:

- src/fifo/PushBuffer.cpp:33 (no source: 0x7ffc is max 13-bit value aligned to 4; nvc0_winsys.h shifts mthd >> 2)
- src/fifo/PushBuffer.cpp:39 (no source: 0x1fff is max 13-bit value for the count field;    nvc0_winsys.h uses (size << 16) with 13-bit field)
- src/fifo/PushBuffer.cpp:257 (no source: 0xff is just 8-bit mask for address upper bits)
- src/mmu/PageTable.h:40 (no source: all-zero is a zero-initialisation convention)

These constants may be verified by a mmiotrace in task C5.
