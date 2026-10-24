# Register Provenance

Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`
(excluding `src/hw/`) is listed below with its source citation.

Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).

## src/compute/LaunchDesc.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/compute/LaunchDesc.cpp:70` | `uint64_t aligned = ((uint64_t)j.sharedMemSize + 0xFF) & ~0xFFULL;` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:600 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:71` | `if (aligned > 0x3FFFF)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:139 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:79` | `if (j.localMemLow > 0xfffff0ULL)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:210 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:81` | `return j.localMemLow & 0xfffff0ULL;` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:210 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:106` | `{1535,1528, 0x30},` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:216 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:117` | `{1527,1504, 0x800ULL},` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:215 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:134` | `if (address & 0xFF)` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:542 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:138` | `if (size > 0x1FFFF)` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:209 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:144` | `q.set(base_addr + 31, base_addr, address & 0xFFFFFFFF);` | src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h:203 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:157` | `if (descGpuAddr & 0xFF)` | src/gallium/drivers/nouveau/nvc0/nve4_compute.c:542 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:165` | `pb.begin(kComputeSubchannel, 0x02b4, 1);` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:165 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:167` | `pb.begin(kComputeSubchannel, 0x02bc, 1);` | src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h:170 | SOURCE_ONLY |
| `src/compute/LaunchDesc.cpp:169` | `pb.begin(kComputeSubchannel, 0x0110, 1);` | src/gallium/drivers/nouveau/nv_object.xml.h:284 | SOURCE_ONLY |

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

## src/devinit/Interpreter.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/Interpreter.cpp:80` | `case 0x36: case 0x38: case 0x71: case 0x72: case 0x8c: case 0x8d: case 0x8e: length=1; break;` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:81` | `case 0x33: case 0x6f: case 0x75: length=2; break;` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:82` | `case 0x53: case 0x56: case 0x5b: case 0x74: length=3; break;` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:83` | `case 0x69: length=5; break;` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:84` | `case 0x7a: case 0x90: length=9; break;` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:85` | `case 0x6e: case 0x97: length=13; break;` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:86` | `case 0x5f: length=22; break;` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:87` | `case 0x4d:` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:90` | `case 0x58: case 0x91:` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:93` | `case 0x8f:` | nvkm/subdev/bios/init.c:2288 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:97` | `case 0xa9:` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:107` | `case 0x71: return Stop::Done;` | nvkm/subdev/bios/init.c:2274 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:108` | `case 0x36:` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:112` | `case 0x33: {` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:126` | `case 0x5b:` | nvkm/subdev/bios/init.c:2259 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:133` | `case 0x38: flags_^=2; break;` | nvkm/subdev/bios/init.c:2235 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:134` | `case 0x72: flags_ &= ~uint8_t(2); break;` | nvkm/subdev/bios/init.c:2275 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:135` | `case 0x75: {` | nvkm/subdev/bios/init.c:2278 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:138` | `case 0x56:` | nvkm/subdev/bios/init.c:2254 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:151` | `case 0x74:` | nvkm/subdev/bios/init.c:2277 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:158` | `case 0x6e: ok=masked(reg,word(uint64_t(pc)+5,4),word(uint64_t(pc)+9,4)); break;` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:159` | `case 0x7a: {` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:161` | `if (reg==0x000200) value\|=0x00000001;` | nvkm/subdev/bios/init.c:1901 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:164` | `case 0x90: { uint32_t value=0; ok=read(reg,value) && write(word(uint64_t(pc)+5,4),value); break; }` | nvkm/subdev/bios/init.c:2289 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:165` | `case 0x97: {` | nvkm/subdev/bios/init.c:2293 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:169` | `case 0x5f: {` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:171` | `const uint32_t bits=shift<0x80 ? shift : 0x100-shift;` | nvkm/subdev/bios/init.c:531 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:174` | `value=shift<0x80 ? value>>bits : value<<bits;` | nvkm/subdev/bios/init.c:531 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:178` | `case 0x58: case 0x91:` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:181` | `ok=write(reg+(op==0x58 ? 4*i : 0),word(uint64_t(pc)+6+4*i,4));` | nvkm/subdev/bios/init.c:1281 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:184` | `case 0x8f:` | nvkm/subdev/bios/init.c:2288 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:191` | `case 0x6f:` | nvkm/subdev/bios/init.c:2273 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:198` | `case 0x8c: case 0x8d: break;` | nvkm/subdev/bios/init.c:2285 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:199` | `case 0x4d: case 0x53: case 0x69: case 0x8e: case 0xa9:` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:202` | `if (active() \|\| op==0x69) {` | nvkm/subdev/bios/init.c:1623 | SOURCE_ONLY |

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
| `src/fifo/PushBuffer.cpp:256` | `e.word0 = static_cast<uint32_t>(addr & 0xffffffffULL);` | nouveau_dma.c:82 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:258` | `e.word1 = static_cast<uint32_t>((addr >> 32) & 0xffffffffULL) \|` | nouveau_dma.c:83 | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:269` | `info.addr = static_cast<uint64_t>(e.word1 & 0xff) << 32 \| e.word0;` | no source: 0xff is just 8-bit mask for address upper bits | SOURCE_ONLY |
| `src/fifo/PushBuffer.cpp:271` | `info.lengthBytes = (e.word1 >> 8) & 0x7fffff;` | nouveau_dma.h:50 | SOURCE_ONLY |

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
| `src/mmu/PageTable.cpp:412` | `uint64_t phys = (pte & 0xfffffff0ULL) << 8;` | nvkm/subdev/mmu/vmmgf100.c:35 | SOURCE_ONLY |

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

## src/runtime/Bootstrap.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/runtime/Bootstrap.cpp:45` | `uint64_t window=address&~uint64_t(0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:47` | `if(!port.write32(0x001700,uint32_t(window>>16)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:50` | `if(!port.write32(0x700000+uint32_t(address&0xfffff),data[i]))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:61` | `uint64_t window=address&~uint64_t(0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:63` | `if(!port.write32(0x001700,uint32_t(window>>16)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:66` | `if(!port.read32(0x700000+uint32_t(address&0xfffff),data[i]))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:74` | `return port.write32(0x070000,1) && poll(port,0x070000,2,limits);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:83` | `patterns[i]=uint32_t((address>>2)^(address>>34))*0x9e3779b9u;` | no source: software test pattern | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:112` | `if(!port.hostSimulation() \|\| id>15 \|\| address>=(1ULL<<40) \|\| (address&0xfff)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:113` | `\|\| entries>0xfffff \|\| !limits.timeoutUs \|\| !limits.attempts)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:117` | `return port.write32(0x002270,(aperture<<28)\|uint32_t(address>>12))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:118` | `&& port.write32(0x002274,(id<<20)\|entries)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:119` | `&& poll(port,0x002284+id*8,0x00100000,limits);` | no source: ambiguous citation | SOURCE_ONLY |

## Open

The following constant lines have no source citation:

- src/compute/LaunchDesc.h:23 (no source: derived)
- src/fifo/PushBuffer.cpp:33 (no source: 0x7ffc is max 13-bit value aligned to 4; nvc0_winsys.h shifts mthd >> 2)
- src/fifo/PushBuffer.cpp:39 (no source: 0x1fff is max 13-bit value for the count field;    nvc0_winsys.h uses (size << 16) with 13-bit field)
- src/fifo/PushBuffer.cpp:269 (no source: 0xff is just 8-bit mask for address upper bits)
- src/runtime/Bootstrap.cpp:45 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:47 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:50 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:61 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:63 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:66 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:74 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:83 (no source: software test pattern)
- src/runtime/Bootstrap.cpp:112 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:113 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:117 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:118 (no source: ambiguous citation)
- src/runtime/Bootstrap.cpp:119 (no source: ambiguous citation)

These constants may be verified by a mmiotrace in task C5.
