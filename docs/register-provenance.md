# Register Provenance

Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`
(excluding `src/hw/`) is listed below with its source citation.

Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).

## src/compute/LaunchDesc.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/compute/LaunchDesc.cpp:68` | `uint64_t aligned = (j.sharedMemSize + 0xFF) & ~0xFFULL;` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:600 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:69` | `if (aligned > 0x3FFFF)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:139 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:96` | `{1535,1528, 0x30},` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:216 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:105` | `{1463,1440, j.localMemLow & 0xfffff0ULL},` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:210 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:107` | `{1527,1504, 0x800ULL},` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:215 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:124` | `if (address & 0xFF)` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:542 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:128` | `if (size > 0x1FFFF)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:209 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:134` | `q.set(base_addr + 31, base_addr, address & 0xFFFFFFFF);` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:203 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:147` | `if (descGpuAddr & 0xFF)` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:542 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:155` | `pb.begin(kComputeSubchannel, 0x02b4, 1);` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:165 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:157` | `pb.begin(kComputeSubchannel, 0x02bc, 1);` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:170 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:159` | `pb.begin(kComputeSubchannel, 0x0110, 1);` | src/gallium/drivers/nouveau/nv_object.xml.h:284 | SOURCE_ONLY |

## src/compute/LaunchDesc.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/compute/LaunchDesc.h:21` | `constexpr unsigned kComputeClass        = 0xa1c0;` | src/gallium/drivers/nouveau/nv_object.xml.h:209 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:22` | `constexpr unsigned kComputeSubchannel   = 1;` | src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h:45 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:23` | `constexpr unsigned kQmdBytes            = 256;` | no source: derived | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:66` | `*   SASS_VERSION                      (1535:1528) = 0x30` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:216 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:74` | `*   SHARED_MEMORY_SIZE                (561:544) = align(sharedMemSize, 0x100)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:139 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:77` | `*   SHADER_LOCAL_MEMORY_CRS_SIZE      (1527:1504) = 0x800` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:215 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:104` | `*   LAUNCH_DESC_ADDRESS (0x02b4): value = descGpuAddr >> 8` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:165 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:105` | `*   LAUNCH              (0x02bc): value = 3` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:170 | SOURCE_ONLY |
| `src/compute/LaunchDesc.h:106` | `*   NV50_GRAPH_SERIALIZE(0x0110): value = 0` | src/gallium/drivers/nouveau/nv_object.xml.h:284 | SOURCE_ONLY |

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
| `src/fifo/PushBuffer.h:27` | `constexpr unsigned kUserdGpPut = 0x8c;` | nouveau_dma.c:92 | SOURCE_ONLY |
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
| `src/mmu/PageTable.h:40` | `static constexpr uint64_t kPteUnmapped = 0;` | nvkm/subdev/mmu/vmmgf100.c:94 | SOURCE_ONLY |
| `src/mmu/PageTable.h:43` | `static constexpr uint64_t kLptInvalid = 2;` | nvkm/subdev/mmu/vmmgk104.c:29 | SOURCE_ONLY |

## Open

The following constant lines have no source citation:

- src/compute/LaunchDesc.h:23 (no source: derived)
- src/fifo/PushBuffer.cpp:33 (no source: 0x7ffc is max 13-bit value aligned to 4; nvc0_winsys.h shifts mthd >> 2)
- src/fifo/PushBuffer.cpp:39 (no source: 0x1fff is max 13-bit value for the count field;    nvc0_winsys.h uses (size << 16) with 13-bit field)
- src/fifo/PushBuffer.cpp:257 (no source: 0xff is just 8-bit mask for address upper bits)

These constants may be verified by a mmiotrace in task C5.
