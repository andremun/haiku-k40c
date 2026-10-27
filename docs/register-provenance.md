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

## src/devinit/Board.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/Board.cpp:10` | `constexpr Digest allowedRom = {` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/Board.cpp:11` | `0xae,0xcb,0x0b,0x5f,0xa4,0x66,0xf6,0x4e,0x26,0x51,0xa5,0x51,0xa3,0xca,0xd5,0x7c,` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/Board.cpp:12` | `0xcc,0xbd,0xed,0xd9,0x29,0xe3,0x99,0x6f,0x54,0x22,0x01,0xaf,0x06,0xff,0x1f,0x54,` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/Board.cpp:14` | `constexpr uint32_t allowedSize = 181760;` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/Board.cpp:15` | `constexpr std::array<BoardRule, 6> rules = {{` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/Board.cpp:16` | `{0x8506, 0x69, allowedRom}, {0x850b, 0x53, allowedRom},` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/Board.cpp:17` | `{0x85e8, 0x53, allowedRom}, {0x862f, 0x4d, allowedRom},` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/Board.cpp:18` | `{0x89b7, 0xa9, allowedRom}, {0xab8d, 0x4d, allowedRom},` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |
| `src/devinit/Board.cpp:25` | `if (!rom.contains(0x36, 2)) return false;` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/Board.cpp:26` | `const auto dcb = rom.little(0x36, 2);` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/Board.cpp:27` | `if (!dcb \|\| !rom.contains(dcb, 12) \|\| rom.data[dcb] < 0x30 \|\| rom.data[dcb] > 0x41` | nvkm/subdev/bios/dcb.c:43 | SOURCE_ONLY |
| `src/devinit/Board.cpp:28` | `\|\| rom.data[dcb + 1] < 12 \|\| rom.little(dcb + 6, 4) != 0x4edcbdcb)` | nvkm/subdev/bios/dcb.c:48 | SOURCE_ONLY |
| `src/devinit/Board.cpp:47` | `if (version != 0x41 \|\| header < 4 \|\| stride < 5` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:53` | `if (function == 0xff) continue;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:54` | `const auto line = uint8_t(raw & 0x3f);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:56` | `const bool defaults = raw & 0x80;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:59` | `defaults, uint8_t(raw >> 16), uint8_t((raw >> 24) & 0x1f)});` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:94` | `if (port == 0x03c3 && bytes[4] == 1) {` | nvkm/subdev/bios/init.c:1636 | SOURCE_ONLY |
| `src/devinit/Board.cpp:96` | `constexpr Step steps[] = {` | no source: software sequence container; each hardware value has its own citation. | SOURCE_ONLY |
| `src/devinit/Board.cpp:97` | `{0x614100,0xf0800000,0x00800000,true,false},` | nvkm/subdev/bios/init.c:1640 | SOURCE_ONLY |
| `src/devinit/Board.cpp:98` | `{0x00e18c,0x00020000,0x00020000,true,false},` | nvkm/subdev/bios/init.c:1641 | SOURCE_ONLY |
| `src/devinit/Board.cpp:99` | `{0x614900,0xf0800000,0x00800000,true,false},` | nvkm/subdev/bios/init.c:1642 | SOURCE_ONLY |
| `src/devinit/Board.cpp:100` | `{0x000200,0x40000000,0x00000000,true,true},` | nvkm/subdev/bios/init.c:1643 | SOURCE_ONLY |
| `src/devinit/Board.cpp:101` | `{0x00e18c,0x00020000,0x00000000,true,false},` | nvkm/subdev/bios/init.c:1645 | SOURCE_ONLY |
| `src/devinit/Board.cpp:102` | `{0x000200,0x40000000,0x40000000,true,false},` | nvkm/subdev/bios/init.c:1646 | SOURCE_ONLY |
| `src/devinit/Board.cpp:103` | `{0x614100,0,0x00800018,false,false},` | nvkm/subdev/bios/init.c:1647 | SOURCE_ONLY |
| `src/devinit/Board.cpp:104` | `{0x614900,0,0x00800018,false,true},` | nvkm/subdev/bios/init.c:1648 | SOURCE_ONLY |
| `src/devinit/Board.cpp:105` | `{0x614100,0,0x10000018,false,false},` | nvkm/subdev/bios/init.c:1650 | SOURCE_ONLY |
| `src/devinit/Board.cpp:106` | `{0x614900,0,0x10000018,false,false},` | nvkm/subdev/bios/init.c:1651 | SOURCE_ONLY |
| `src/devinit/Board.cpp:117` | `const uint32_t address = 0x601000 + port;` | nvkm/engine/disp/vga.c:52 | SOURCE_ONLY |
| `src/devinit/Board.cpp:131` | `if ((version != 0x40 && version != 0x41) \|\| header < 5 \|\| stride < 4` | nvkm/subdev/bios/i2c.c:32 | SOURCE_ONLY |
| `src/devinit/Board.cpp:134` | `if (index == 0x80 \|\| index == 0xff) index = rom.data[at + 4] & 0x0f;` | nvkm/subdev/bios/init.c:263 | SOURCE_ONLY |
| `src/devinit/Board.cpp:135` | `else if (index == 0x81) index = rom.data[at + 4] >> 4;` | nvkm/subdev/bios/init.c:274 | SOURCE_ONLY |
| `src/devinit/Board.cpp:141` | `if (version == 0x40) {` | nvkm/subdev/bios/i2c.c:79 | SOURCE_ONLY |
| `src/devinit/Board.cpp:144` | `if (bus.type != 0x05) return false;` | nvkm/subdev/bios/i2c.c:107 | SOURCE_ONLY |
| `src/devinit/Board.cpp:145` | `bus.drive = raw & 0x0f;` | nvkm/subdev/bios/i2c.c:109 | SOURCE_ONLY |
| `src/devinit/Board.cpp:146` | `if (raw & 0x100) bus.share = uint8_t((raw >> 9) & 0x7f);` | nvkm/subdev/bios/i2c.c:110 | SOURCE_ONLY |
| `src/devinit/Board.cpp:149` | `bus.type = 0x80;` | nvkm/subdev/bios/i2c.c:79 | SOURCE_ONLY |
| `src/devinit/Board.cpp:150` | `bus.drive = raw & 0x1f;` | nvkm/subdev/bios/i2c.c:119 | SOURCE_ONLY |
| `src/devinit/Board.cpp:151` | `bus.aux = (raw >> 5) & 0x1f;` | nvkm/subdev/bios/i2c.c:122 | SOURCE_ONLY |
| `src/devinit/Board.cpp:152` | `if (bus.drive == 0x1f) return false;` | nvkm/subdev/bios/i2c.c:120 | SOURCE_ONLY |
| `src/devinit/Board.cpp:153` | `if (bus.aux == 0x1f) bus.aux = 0xff;` | nvkm/subdev/bios/i2c.c:123 | SOURCE_ONLY |
| `src/devinit/Board.cpp:176` | `const uint32_t reg = 0x00d610 + uint32_t(pin.line) * 4;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:180` | `if (!masked(reg, 0x00003000, direction \| level)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:181` | `\|\| !masked(0x00d604, 1, 1)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:182` | `\|\| !masked(reg, 0xff, pin.route)) return Error::Io;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:183` | `if (pin.selector && !masked(0x00d740 + uint32_t(pin.selector - 1) * 4, 0xff, pin.line))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/Board.cpp:195` | `case 0x69: return length == 5 ? io(bytes, active) : Error::Input;` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/Board.cpp:196` | `case 0x53:` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/Board.cpp:199` | `if (active && (!ports_.write8(0x6013d4, bytes[1]) \|\| !ports_.write8(0x6013d5, bytes[2])))` | nvkm/engine/disp/vga.c:104 | SOURCE_ONLY |
| `src/devinit/Board.cpp:202` | `case 0x4d: {` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/Board.cpp:213` | `case 0xa9:` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |

## src/devinit/Board.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/Board.h:21` | `uint8_t index = 0, type = 0, drive = 0xff, share = 0xff, aux = 0xff;` | no source: ambiguous citation | SOURCE_ONLY |

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

## src/devinit/Sha256.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/Sha256.cpp:9` | `constexpr uint32_t rounds[] = {` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:10` | `0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:11` | `0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:12` | `0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:13` | `0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:14` | `0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:15` | `0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:16` | `0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:17` | `0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:25` | `uint32_t state[] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:26` | `0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |
| `src/devinit/Sha256.cpp:34` | `else if (at == size) byte = 0x80;` | no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3. | SOURCE_ONLY |

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
- src/devinit/Board.cpp:10 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/Board.cpp:11 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/Board.cpp:12 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/Board.cpp:14 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/Board.cpp:15 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/Board.cpp:47 (no source: ambiguous citation)
- src/devinit/Board.cpp:53 (no source: ambiguous citation)
- src/devinit/Board.cpp:54 (no source: ambiguous citation)
- src/devinit/Board.cpp:56 (no source: ambiguous citation)
- src/devinit/Board.cpp:59 (no source: ambiguous citation)
- src/devinit/Board.cpp:96 (no source: software sequence container; each hardware value has its own citation.)
- src/devinit/Board.cpp:176 (no source: ambiguous citation)
- src/devinit/Board.cpp:180 (no source: ambiguous citation)
- src/devinit/Board.cpp:181 (no source: ambiguous citation)
- src/devinit/Board.cpp:182 (no source: ambiguous citation)
- src/devinit/Board.cpp:183 (no source: ambiguous citation)
- src/devinit/Board.h:21 (no source: ambiguous citation)
- src/devinit/Sha256.cpp:9 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:10 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:11 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:12 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:13 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:14 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:15 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:16 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:17 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:25 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:26 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
- src/devinit/Sha256.cpp:34 (no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.)
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
