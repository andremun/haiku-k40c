# Register Provenance

Every hardware constant (hex ≥2 digits or `constexpr`) in `src/`
(excluding `src/hw/`) is listed below with its source citation.

Statuses: `SOURCE_ONLY` (from source code only, no hardware trace yet).

## src/a7/ArmAuthority.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/a7/ArmAuthority.cpp:8` | `constexpr uint8_t requestMagic[16]={'K','4','0','A','7','R','E','Q',1,0,0,0,0,0,0,0};` | no source: software request framing magic and version. | SOURCE_ONLY |
| `src/a7/ArmAuthority.cpp:9` | `constexpr uint8_t grantMagic[16]={'K','4','0','A','7','A','R','M',1,0,0,0,0,0,0,0};` | no source: software grant framing magic and version. | SOURCE_ONLY |
| `src/a7/ArmAuthority.cpp:15` | `constexpr uint8_t order[32]={0xed,0xd3,0xf5,0x5c,0x1a,0x63,0x12,0x58,0xd6,0x9c,0xf7,0xa2,0xde,0xf9,0xde,0x14,` | no source: RFC 8032 sections 5.1,5.1.7 subgroup order for signature verification. | SOURCE_ONLY |
| `src/a7/ArmAuthority.cpp:16` | `0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x10};` | no source: continuation of the RFC 8032 subgroup order, not a hardware constant. | SOURCE_ONLY |

## src/a7/ArmAuthority.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/a7/ArmAuthority.h:9` | `constexpr size_t requestBytes=128, grantBytes=192;` | no source: software request/grant frame sizes, not hardware packets. | SOURCE_ONLY |

## src/a7/NativePlatform.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/a7/NativePlatform.cpp:33` | `if(info.vendor_id==0x10de && info.device_id==0x1024){card_=info;++matches;}` | no source: software PCI identity comparison; KNOWN capture hardware/record.json:4. | SOURCE_ONLY |
| `src/a7/NativePlatform.cpp:36` | `if(!terminated \|\| matches!=1 \|\| (card_.header_type&0x7f)!=0)return false;` | no source: software type-0-only guard; Haiku PCI.h lines 727,733 define the mask and type. | SOURCE_ONLY |
| `src/a7/NativePlatform.cpp:48` | `if(!physical \|\| physical%B_PAGE_SIZE \|\| bytes_<0x800000 \|\| bytes_>0x1000000` | no source: software mapping ceiling, not a hardware aperture assertion. | SOURCE_ONLY |

## src/a7/Owner.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/a7/Owner.cpp:29` | `\|\| identity!=0x0f1240a1 \|\| !arm_.prepare()) {` | no source: software identity comparison; KNOWN capture hardware/record.json:37. | SOURCE_ONLY |
| `src/a7/Owner.cpp:77` | `if(width==1)return phase_==Phase::Crtc && (reg==0x6013d4 \|\| reg==0x6013d5);` | nvkm/engine/disp/vga.c:97 | SOURCE_ONLY |
| `src/a7/Owner.cpp:80` | `case Phase::Identity:return !write && (reg==0 \|\| reg==0x101000);` | nvkm/subdev/bios/ramcfg.c:29 | SOURCE_ONLY |
| `src/a7/Owner.cpp:81` | `case Phase::Interrupts:return (reg==0x140 \|\| reg==0x144) && (write \|\| reg==0x140);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:82` | `case Phase::Decision:return !write && reg==0x02240c;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:83` | `case Phase::Ring:return reg==0x122318 \|\| reg==0x12231c \|\| reg==0x122310 \|\| reg==0x122348 \|\| reg==0x1223b0 \|\| reg==0x122358;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:85` | `case Phase::Arm:return write && reg==0x100c10;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:86` | `case Phase::Fifo:return reg==0x200;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:87` | `case Phase::Readback:return !write && reg==0x100c10;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:89` | `if(!write && (reg==0 \|\| reg==0x100 \|\| reg==0x9400 \|\| reg==0x9410 \|\| reg==0x22438 \|\| reg==0x2243c \|\| reg==0x22554))return true;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:91` | `if(!write && reg>=0x11020c && reg<=0x12f20c && (reg-0x11020c)%0x1000==0)return true;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:92` | `if(reg==0x070000)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:93` | `if(scratchOwned_ && windowLocked_ && reg==0x1700)return write;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:94` | `if(scratchOwned_ && windowLocked_ && selector_==0 && reg>=0x740000 && reg<0x741000)return true;` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:112` | `if(phase_==Phase::Readiness && ((reg==0x1700 && value!=0) \|\| (reg==0x70000 && value!=1)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:115` | `if(!fifoRead_ \|\| fifoWrites_>=2 \|\| value!=((fifoReadValue_&~0x100u)\|(fifoWrites_?0x100u:0)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:120` | `if(phase_==Phase::Readiness && reg==0x1700)selector_=value;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:154` | `if(!read32(0,value) \|\| value!=0x0f1240a1)return false;` | no source: software identity comparison; KNOWN capture hardware/record.json:37. | SOURCE_ONLY |
| `src/a7/Owner.cpp:175` | `i2cPin_=0x00d014+uint32_t(bus.drive)*0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |
| `src/a7/Owner.cpp:199` | `phase_=Phase::Readback;readback_=read32(0x100c10,value);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:208` | `if(!read32(0x9410,high) \|\| !read32(0x9400,low) \|\| !read32(0x9410,again))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:217` | `if(!read32(0x22438,parts) \|\| !read32(0x2243c,units) \|\| !read32(0x22554,disabled)` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:226` | `if(!read32(0x11020c+unit*0x1000,mib) \|\| !mib)return false;` | nvkm/subdev/fb/ramgf100.c:467 | SOURCE_ONLY |
| `src/a7/Owner.cpp:236` | `return activeParts && total==owner_.expectedVram_ && total>0x40000+0x100000+4096;` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:241` | `if(!read32(0,identity) \|\| identity!=0x0f1240a1 \|\| !timer(result.timerBefore)` | no source: software identity comparison; KNOWN capture hardware/record.json:37. | SOURCE_ONLY |
| `src/a7/Owner.cpp:243` | `\|\| !memorySize(result.vramBytes) \|\| !read32(0x100,result.pending) \|\| result.pending)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:250` | `const uint64_t offsets[]={0,0x100,0xffc};` | no source: software scratch sample offsets within our owned page. | SOURCE_ONLY |
| `src/a7/Owner.cpp:251` | `result.scratch=runtime::checkOwnedScratch(*this,{{0x40000},4096},offsets,3,{2000000,100000});` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:252` | `if(!result.scratch \|\| !read32(0x100,result.pending) \|\| result.pending)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:253` | `emit("",0x40000,4096);return diagnosticsHealthy();` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |

## src/a7/PostDiagnostics.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/a7/PostDiagnostics.h:9` | `static constexpr unsigned capacity=2048, pollCapacity=16;` | no source: software record/table bounds. | SOURCE_ONLY |

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

## src/devinit/BoardCore.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/BoardCore.cpp:11` | `if (!rom.contains(0x36, 2)) return false;` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:12` | `const auto dcb = rom.little(0x36, 2);` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:13` | `if (!dcb \|\| !rom.contains(dcb, 12) \|\| rom.data[dcb] < 0x30 \|\| rom.data[dcb] > 0x41` | nvkm/subdev/bios/dcb.c:43 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:14` | `\|\| rom.data[dcb + 1] < 12 \|\| rom.little(dcb + 6, 4) != 0x4edcbdcb)` | nvkm/subdev/bios/dcb.c:48 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:35` | `if (version != 0x41 \|\| header < 4 \|\| stride < 5` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:41` | `if (function == 0xff) continue;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:42` | `const auto line = uint8_t(raw & 0x3f);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:44` | `const bool defaults = raw & 0x80;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:47` | `defaults, uint8_t(raw >> 16), uint8_t((raw >> 24) & 0x1f)};` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:74` | `if (port == 0x03c3 && bytes[4] == 1) {` | nvkm/subdev/bios/init.c:1636 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:76` | `constexpr Step steps[] = {` | no source: software sequence container; each hardware value has its own citation. | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:77` | `{0x614100,0xf0800000,0x00800000,true,false},` | nvkm/subdev/bios/init.c:1640 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:78` | `{0x00e18c,0x00020000,0x00020000,true,false},` | nvkm/subdev/bios/init.c:1641 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:79` | `{0x614900,0xf0800000,0x00800000,true,false},` | nvkm/subdev/bios/init.c:1642 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:80` | `{0x000200,0x40000000,0x00000000,true,true},` | nvkm/subdev/bios/init.c:1643 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:81` | `{0x00e18c,0x00020000,0x00000000,true,false},` | nvkm/subdev/bios/init.c:1645 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:82` | `{0x000200,0x40000000,0x40000000,true,false},` | nvkm/subdev/bios/init.c:1646 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:83` | `{0x614100,0,0x00800018,false,false},` | nvkm/subdev/bios/init.c:1647 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:84` | `{0x614900,0,0x00800018,false,true},` | nvkm/subdev/bios/init.c:1648 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:85` | `{0x614100,0,0x10000018,false,false},` | nvkm/subdev/bios/init.c:1650 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:86` | `{0x614900,0,0x10000018,false,false},` | nvkm/subdev/bios/init.c:1651 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:97` | `const uint32_t address = 0x601000 + port;` | nvkm/engine/disp/vga.c:52 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:111` | `if ((version != 0x40 && version != 0x41) \|\| header < 5 \|\| stride < 4` | nvkm/subdev/bios/i2c.c:32 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:114` | `if (index == 0x80 \|\| index == 0xff) index = rom.data[at + 4] & 0x0f;` | nvkm/subdev/bios/init.c:263 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:115` | `else if (index == 0x81) index = rom.data[at + 4] >> 4;` | nvkm/subdev/bios/init.c:274 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:121` | `if (version == 0x40) {` | nvkm/subdev/bios/i2c.c:79 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:124` | `if (bus.type != 0x05) return false;` | nvkm/subdev/bios/i2c.c:107 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:125` | `bus.drive = raw & 0x0f;` | nvkm/subdev/bios/i2c.c:109 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:126` | `if (raw & 0x100) bus.share = uint8_t((raw >> 9) & 0x7f);` | nvkm/subdev/bios/i2c.c:110 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:129` | `bus.type = 0x80;` | nvkm/subdev/bios/i2c.c:79 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:130` | `bus.drive = raw & 0x1f;` | nvkm/subdev/bios/i2c.c:119 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:131` | `bus.aux = (raw >> 5) & 0x1f;` | nvkm/subdev/bios/i2c.c:122 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:132` | `if (bus.drive == 0x1f) return false;` | nvkm/subdev/bios/i2c.c:120 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:133` | `if (bus.aux == 0x1f) bus.aux = 0xff;` | nvkm/subdev/bios/i2c.c:123 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:161` | `const uint32_t reg = 0x00d610 + uint32_t(pin.line) * 4;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:165` | `if (!masked(reg, 0x00003000, direction \| level)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:166` | `\|\| !masked(0x00d604, 1, 1)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:167` | `\|\| !masked(reg, 0xff, pin.route)) return Error::Io;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:168` | `if (pin.selector && !masked(0x00d740 + uint32_t(pin.selector - 1) * 4, 0xff, pin.line))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:181` | `case 0x69: return length == 5 ? io(bytes, active) : Error::Input;` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:182` | `case 0x53:` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:185` | `if (active && (!ports_.write8(0x6013d4, bytes[1]) \|\| !ports_.write8(0x6013d5, bytes[2])))` | nvkm/engine/disp/vga.c:104 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:188` | `case 0x4d: {` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/BoardCore.cpp:199` | `case 0xa9:` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |

## src/devinit/BoardCore.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/BoardCore.h:17` | `uint8_t index = 0, type = 0, drive = 0xff, share = 0xff, aux = 0xff;` | no source: ambiguous citation | SOURCE_ONLY |

## src/devinit/BoardPolicy.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/BoardPolicy.cpp:7` | `constexpr Digest allowedRom = {` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:8` | `0xae,0xcb,0x0b,0x5f,0xa4,0x66,0xf6,0x4e,0x26,0x51,0xa5,0x51,0xa3,0xca,0xd5,0x7c,` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:9` | `0xcc,0xbd,0xed,0xd9,0x29,0xe3,0x99,0x6f,0x54,0x22,0x01,0xaf,0x06,0xff,0x1f,0x54,` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:11` | `constexpr std::array<BoardRule, 6> rules = {{` | no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:12` | `{0x8506, 0x69, allowedRom}, {0x850b, 0x53, allowedRom},` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:13` | `{0x85e8, 0x53, allowedRom}, {0x862f, 0x4d, allowedRom},` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/BoardPolicy.cpp:14` | `{0x89b7, 0xa9, allowedRom}, {0xab8d, 0x4d, allowedRom},` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |

## src/devinit/BoardPolicy.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/BoardPolicy.h:7` | `inline constexpr uint32_t approvedRomBytes = 181760;` | no source: software exact-image permission size, ADR 004 and reference/vbios/README.md. | SOURCE_ONLY |

## src/devinit/BoundPost.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/BoundPost.cpp:42` | `bool allowed=inI2c_ && active_ && inst && inst->opcode==0x4d && (us==1 \|\| us==5);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:45` | `if (inst->opcode==0x69) allowed=us==10000;` | nvkm/subdev/bios/init.c:1644 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:46` | `if (inst->opcode==0x56) allowed=active_ && us==20000;` | nvkm/subdev/bios/init.c:1246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:47` | `if (inst->opcode==0x74) {` | nvkm/subdev/bios/init.c:1769 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:80` | `if (!inst \|\| inst->opcode!=0x4d \|\| !boardAllowed(approvedRomDigest(),pc_,inst->opcode)) {` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:99` | `const bool sensor=pc_==0xab8d && bytes[1]==0x80 && address==0x4c` | nvkm/subdev/bios/init.c:1033 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:100` | `&& value==0x73 && (reg==0x19 \|\| reg==0x0d);` | no source: exact captured ROM transaction policy. | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:101` | `const unsigned pairBit=reg==0x19?1:2;` | no source: software bitset index for the two captured ROM pairs. | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:139` | `if (inst->opcode!=0x4d \|\| !boardAllowed(approvedRomDigest(),inst->offset,inst->opcode)) continue;` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:146` | `if (!found \|\| bus.type!=0x05 \|\| bus.share!=0xff \|\| bus.drive>15) return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:157` | `pin_=0x00d014+uint32_t(bus.drive)*0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |

## src/devinit/I2c.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/I2c.cpp:12` | `if (bus.type != 0x05 \|\| bus.share != 0xff \|\| bus.drive > 15) {` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/I2c.cpp:15` | `address_ = 0x00d014 + uint32_t(bus.drive) * 0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |
| `src/devinit/I2c.cpp:69` | `if (!delay(1) \|\| !sense(0x10, high)) return false;` | nvkm/subdev/i2c/busgf119.c:53 | SOURCE_ONLY |
| `src/devinit/I2c.cpp:77` | `if (!sense(0x10, scl) \|\| !sense(0x20, sda)) return false;` | nvkm/subdev/i2c/busgf119.c:53 | SOURCE_ONLY |
| `src/devinit/I2c.cpp:100` | `\|\| !sense(0x20, nack) \|\| !drive(1, false) \|\| !delay(5)) return false;` | nvkm/subdev/i2c/busgf119.c:61 | SOURCE_ONLY |

## src/devinit/Interpreter.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/Interpreter.cpp:82` | `case 0x36: case 0x38: case 0x71: case 0x72: case 0x8c: case 0x8d: case 0x8e: length=1; break;` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:83` | `case 0x33: case 0x6f: case 0x75: length=2; break;` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:84` | `case 0x53: case 0x56: case 0x5b: case 0x74: length=3; break;` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:85` | `case 0x69: length=5; break;` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:86` | `case 0x7a: case 0x90: length=9; break;` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:87` | `case 0x6e: case 0x97: length=13; break;` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:88` | `case 0x5f: length=22; break;` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:89` | `case 0x4d:` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:92` | `case 0x58: case 0x91:` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:95` | `case 0x8f:` | nvkm/subdev/bios/init.c:2288 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:99` | `case 0xa9:` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:109` | `case 0x71: return Stop::Done;` | nvkm/subdev/bios/init.c:2274 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:110` | `case 0x36:` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:114` | `case 0x33: {` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:128` | `case 0x5b:` | nvkm/subdev/bios/init.c:2259 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:135` | `case 0x38: flags_^=2; break;` | nvkm/subdev/bios/init.c:2235 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:136` | `case 0x72: flags_ &= ~uint8_t(2); break;` | nvkm/subdev/bios/init.c:2275 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:137` | `case 0x75: {` | nvkm/subdev/bios/init.c:2278 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:140` | `case 0x56:` | nvkm/subdev/bios/init.c:2254 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:155` | `case 0x74:` | nvkm/subdev/bios/init.c:2277 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:162` | `case 0x6e: ok=masked(reg,word(uint64_t(pc)+5,4),word(uint64_t(pc)+9,4)); break;` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:163` | `case 0x7a: {` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:165` | `if (reg==0x000200) value\|=0x00000001;` | nvkm/subdev/bios/init.c:1901 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:168` | `case 0x90: { uint32_t value=0; ok=read(reg,value) && write(word(uint64_t(pc)+5,4),value); break; }` | nvkm/subdev/bios/init.c:2289 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:169` | `case 0x97: {` | nvkm/subdev/bios/init.c:2293 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:173` | `case 0x5f: {` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:175` | `const uint32_t bits=shift<0x80 ? shift : 0x100-shift;` | nvkm/subdev/bios/init.c:531 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:178` | `value=shift<0x80 ? value>>bits : value<<bits;` | nvkm/subdev/bios/init.c:531 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:182` | `case 0x58: case 0x91:` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:185` | `ok=write(reg+(op==0x58 ? 4*i : 0),word(uint64_t(pc)+6+4*i,4));` | nvkm/subdev/bios/init.c:1281 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:188` | `case 0x8f:` | nvkm/subdev/bios/init.c:2288 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:195` | `case 0x6f:` | nvkm/subdev/bios/init.c:2273 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:202` | `case 0x8c: case 0x8d: break;` | nvkm/subdev/bios/init.c:2285 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:203` | `case 0x4d: case 0x53: case 0x69: case 0x8e: case 0xa9:` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/Interpreter.cpp:206` | `if (active() \|\| op==0x69) {` | nvkm/subdev/bios/init.c:1623 | SOURCE_ONLY |

## src/devinit/PostImage.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/devinit/PostImage.cpp:14` | `return !(reg & ~0x00fffffc);` | nvkm/subdev/bios/init.c:144 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:23` | `if (!span(0x36,2)) return false;` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:24` | `const auto dcb = get(0x36,2);` | nvkm/subdev/bios/dcb.c:35 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:25` | `if (!dcb \|\| !span(dcb,12) \|\| get(dcb,1) < 0x30 \|\| get(dcb,1) > 0x41` | nvkm/subdev/bios/dcb.c:43 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:26` | `\|\| get(dcb+1,1) < 12 \|\| get(dcb+6,4) != 0x4edcbdcb) return false;` | nvkm/subdev/bios/dcb.c:48 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:43` | `if (get(i,1)==0xff && get(i+1,1)==0xb8 && get(i+2,1)=='B'` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:70` | `if (get(mt,1)==0x10) {` | nvkm/subdev/bios/M0203.c:41 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:77` | `if (!matched[strap]) { ram_[strap]=get(entry+1,1)&0x0f; matched[strap]=true; }` | nvkm/subdev/bios/M0203.c:96 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:103` | `case 0x36: case 0x38: case 0x71: case 0x72: case 0x8c: case 0x8d: case 0x8e: length=1; break;` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:104` | `case 0x33: case 0x6f: case 0x75: length=2; break;` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:105` | `case 0x53: case 0x56: case 0x5b: case 0x74: length=3; break;` | nvkm/subdev/bios/init.c:2252 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:106` | `case 0x69: length=5; break;` | nvkm/subdev/bios/init.c:2269 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:107` | `case 0x7a: case 0x90: length=9; break;` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:108` | `case 0x6e: case 0x97: length=13; break;` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:109` | `case 0x5f: length=22; break;` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:110` | `case 0x4d: if (!span(pc,4)) return Error::Bounds; length=4+2*get(pc+3,1); break;` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:111` | `case 0x58: case 0x91: if (!span(pc,6)) return Error::Bounds; length=6+4*get(pc+5,1); break;` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:112` | `case 0x8f: if (!span(pc,7)) return Error::Bounds; length=7+4*get(pc+6,1)*groups_; break;` | nvkm/subdev/bios/init.c:2288 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:113` | `case 0xa9: if (!span(pc,2)) return Error::Bounds; length=2+get(pc+1,1); break;` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:121` | `if (op==0x33) { if (!get(pc+1,1)) return Error::Unsupported; ++loops; }` | nvkm/subdev/bios/init.c:2231 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:122` | `if (op==0x36) { if (!loops) return Error::Malformed; --loops; }` | nvkm/subdev/bios/init.c:2233 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:123` | `if (op==0x5b) {` | nvkm/subdev/bios/init.c:2259 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:128` | `if (op==0x71) { if (loops) return Error::Unsupported; break; }` | nvkm/subdev/bios/init.c:2274 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:138` | `if (op==0x56 \|\| op==0x75) {` | nvkm/subdev/bios/init.c:1250 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:144` | `if (op==0x6f && macros_) {` | nvkm/subdev/bios/init.c:1734 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:149` | `case 0x6e: case 0x7a: case 0x97: case 0x90: case 0x5f: case 0x58: case 0x91: case 0x8f:` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:152` | `if (op==0x90 && !reg(pc+5)) return Error::Unsupported;` | nvkm/subdev/bios/init.c:2289 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:153` | `if (op==0x5f) {` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:157` | `if (op==0x58 \|\| op==0x8f) {` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:158` | `const auto base=get(pc+1,4), step=op==0x58?4:get(pc+5,1), count=get(pc+(op==0x58?5:6),1);` | nvkm/subdev/bios/init.c:1281 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:161` | `if (op==0xa9) {` | nvkm/subdev/bios/init.c:2297 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:164` | `if (get(gpio_,1)!=0x41 \|\| header<4 \|\| stride<5 \|\| !span(gpio_,header+count*stride)) return Error::Unsupported;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:170` | `if (op==0x4d) {` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:174` | `if (get(ccb,1)!=0x40 \|\| header<5 \|\| stride<4 \|\| !span(ccb,header+count*stride)) return Error::Unsupported;` | nvkm/subdev/bios/i2c.c:32 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:176` | `if (index==0x80) index=get(ccb+4,1)&15;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:177` | `else if (index==0x81) index=get(ccb+4,1)>>4;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:180` | `if ((raw>>24)!=5 \|\| (raw&0x100)) return Error::Unsupported;` | nvkm/subdev/bios/i2c.c:107 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:187` | `if ((op==0x56 \|\| op==0x75) && conditions_) { at=conditions_+12*get(pc+1,1); length=12; }` | nvkm/subdev/bios/init.c:479 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:188` | `if (op==0x6f && macros_) { at=macros_+8*get(pc+1,1); length=8; }` | nvkm/subdev/bios/init.c:1734 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:207` | `case 0x6e: case 0x97: return reg==get(pc+1,4);` | nvkm/subdev/bios/init.c:2272 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:208` | `case 0x7a: return write && reg==get(pc+1,4);` | nvkm/subdev/bios/init.c:2283 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:209` | `case 0x90: return reg==get(pc+(write?5:1),4);` | nvkm/subdev/bios/init.c:2289 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:210` | `case 0x5f: return (reg==get(pc+14,4)) \|\| (!write && reg==get(pc+1,4));` | nvkm/subdev/bios/init.c:2262 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:211` | `case 0x58: case 0x8f: {` | nvkm/subdev/bios/init.c:2256 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:213` | `const auto base=get(pc+1,4), step=op==0x58?4:get(pc+5,1), count=get(pc+(op==0x58?5:6),1);` | nvkm/subdev/bios/init.c:1281 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:217` | `case 0x91: return write && get(pc+5,1) && reg==get(pc+1,4);` | nvkm/subdev/bios/init.c:2034 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:218` | `case 0x6f: return write && macros_ && reg==get(macros_+8*get(pc+1,1),4);` | nvkm/subdev/bios/init.c:1734 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:219` | `case 0x56: case 0x75: return !write && conditions_ && reg==get(conditions_+12*get(pc+1,1),4);` | nvkm/subdev/bios/init.c:479 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:223` | `if (op==0x4d && width==4) {` | nvkm/subdev/bios/init.c:1037 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:227` | `if (index==0x80) index=get(ccb+4,1)&15;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:228` | `else if (index==0x81) index=get(ccb+4,1)>>4;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:230` | `return reg==0x00d014+(raw&15)*0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:232` | `if (op==0x53) return width==1 && write && (reg==0x6013d4 \|\| reg==0x6013d5);` | nvkm/engine/disp/vga.c:104 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:233` | `if (op==0x69) {` | nvkm/subdev/bios/init.c:1636 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:234` | `if (width==1) return reg==0x601000+get(pc+1,2);` | nvkm/engine/disp/vga.c:49 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:236` | `if (reg==0x000200 \|\| reg==0x00e18c) return true;` | nvkm/subdev/bios/init.c:1641 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:237` | `return (reg==0x614100 \|\| reg==0x614900);` | nvkm/subdev/bios/init.c:1640 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:239` | `if (op==0xa9 && width==4) {` | nvkm/subdev/bios/init.c:2193 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:246` | `if (!excluded && (reg==0x00d610+line*4 \|\| reg==0x00d604` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:247` | `\|\| (selector && reg==0x00d740+(selector-1)*4))) return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:267` | `if (!backend.read32(0x101000,strap)) return Error::Io;` | nvkm/subdev/bios/ramcfg.c:29 | SOURCE_ONLY |
| `src/devinit/PostImage.cpp:268` | `if (!layout_.group(uint8_t((strap&0x3c)>>2),group_)) return Error::Input;` | nvkm/subdev/bios/ramcfg.c:31 | SOURCE_ONLY |

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

## src/gr/Program.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/gr/Program.h:25` | `constexpr uint8_t noSlot=0xff;` | no source: software marker for "". | SOURCE_ONLY |
| `src/gr/Program.h:26` | `constexpr unsigned maxSlots=64;` | no source: software bound; program.py refuses more. | SOURCE_ONLY |
| `src/gr/Program.h:27` | `constexpr uint32_t contextPointerHook=1;` | nvkm/engine/gr/ctxgf100.c:1483 | SOURCE_ONLY |

## src/gr/Runner.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/gr/Runner.cpp:6` | `constexpr uint64_t waitUs=2000000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/gr/Runner.cpp:7` | `constexpr uint32_t maxPolls=20000000;` | no source: software poll-count bound above the time bound. | SOURCE_ONLY |
| `src/gr/Runner.cpp:45` | `if(!read(index,0x400700,unused) \|\| !read(index,0x000200,enable)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/gr/Runner.cpp:46` | `\|\| !read(index,0x002640,status) \|\| !read(index,0x40060c,busy))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/gr/Runner.cpp:47` | `const bool enabled=enable&0x1000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/gr/Runner.cpp:48` | `const bool switching=(status&0x80000000) && (status&0x00008000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/gr/Runner.cpp:51` | `if(now-start>=waitUs)return fail(Error::Idle,index,0x40060c,busy);` | no source: ambiguous citation | SOURCE_ONLY |

## src/memauth/Session.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memauth/Session.cpp:8` | `constexpr uint8_t magic[16]={'K','4','0','M','E','M','R','E','Q',1,0,0,0,0,0,0};` | no source: memory role/version framing. | SOURCE_ONLY |
| `src/memauth/Session.cpp:9` | `constexpr uint8_t grantMagic[16]={'K','4','0','M','E','M','R','U','N',1,0,0,0,0,0,0};` | no source: separate signed role/version framing. | SOURCE_ONLY |
| `src/memauth/Session.cpp:14` | `constexpr uint8_t order[32]={0xed,0xd3,0xf5,0x5c,0x1a,0x63,0x12,0x58,0xd6,0x9c,0xf7,0xa2,0xde,0xf9,0xde,0x14,` | no source: RFC 8032 subgroup order, signature canonicality. | SOURCE_ONLY |
| `src/memauth/Session.cpp:15` | `0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x10};` | no source: RFC 8032 subgroup order continuation. | SOURCE_ONLY |

## src/memauth/Session.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memauth/Session.h:7` | `constexpr size_t requestBytes=256,grantBytes=320;` | no source: distinct software memory-phase frames. | SOURCE_ONLY |

## src/memnative/NativeIo.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memnative/NativeIo.cpp:14` | `if(card.vendor_id==0x10de && card.device_id==0x1024){card_=card;++matches;}` | no source: fixed PCI identity, hardware/record.json. | SOURCE_ONLY |
| `src/memnative/NativeIo.cpp:17` | `if(!ended \|\| matches!=1 \|\| (card_.header_type&0x7f))return B_BAD_DATA;` | no source: type-0-only software profile, Haiku PCI.h lines 727,733. | SOURCE_ONLY |

## src/memnative/Policy.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memnative/Policy.cpp:12` | `if(selected_==UINT64_MAX \|\| reg<0x700000 \|\| reg>=0x800000 \|\| (reg&3))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:13` | `const uint64_t address=selected_+reg-0x700000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:22` | `if(reg==0x100 \|\| reg==0x2100 \|\| reg==0x259c \|\| reg==0x120058 \|\| reg==0x12005c` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:23` | `\|\| reg==0x120070 \|\| reg==0x120074 \|\| reg==0x120078)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:24` | `if(reg==0x1704 \|\| reg==0x100c80 \|\| reg==0x70000)return true;` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:25` | `if(reg==0x22438 \|\| reg==0x2243c \|\| reg==0x22554)return true;` | nvkm/subdev/fb/ramgf108.c:30 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:26` | `if(reg>=0x11020c && reg<=0x12f20c && (reg-0x11020c)%0x1000==0) {` | nvkm/subdev/fb/ramgf100.c:467 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:27` | `const auto unit=(reg-0x11020c)/0x1000;return unit<units_ && !(disabled_&(uint32_t(1)<<unit));` | nvkm/subdev/fb/ramgf100.c:467 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:29` | `if(reg>=0x22700 && reg<0x22800)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:30` | `if(reg>=0x2800 && reg<0x2a00)return (pending_&(uint32_t(1)<<((reg-0x2800)/16)))!=0;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:31` | `const uint32_t bases[]={0x122120,0x124120,0x128120};` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:38` | `const auto base=bases[group]+i*0x800;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:48` | `case 0x259c:pending_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:49` | `case 0x120058:priv0_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:50` | `case 0x12005c:priv1_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:51` | `case 0x120070:hubs_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:52` | `case 0x120074:rops_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:53` | `case 0x120078:gpcs_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:54` | `case 0x2243c:units_=value<=32?value:0;break;` | nvkm/subdev/fb/ramgf108.c:31 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:55` | `case 0x22554:disabled_=value;break;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:56` | `case 0x100c80:status_=value;if(commands_ && (value&0x8000))queued_=true;break;` | nvkm/subdev/mmu/vmmgf100.c:224 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:57` | `case 0x1704:context_=value;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:61` | `if(reg==0x100c80 && waitQueued_ && (value&0x8000))chanQueued_=true;` | nvkm/subdev/mmu/vmmgf100.c:224 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:62` | `if(reg==0x000204 && step_==8){mask_=value;probed_=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:63` | `if(reg>=0x002390 && reg<0x0023b0)runm_[(reg-0x002390)/4]=value;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:64` | `if(reg==0x002a04 && step_==9){value2a04_=value;read2a04_=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:65` | `if(reg>=0x04013c && reg<0x04013c+8*0x2000 && (reg-0x04013c)%0x2000==0 && step_==10){control_=value;readControl_=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:66` | `if(reg==0x800004+chid*8){state_=value;readState_=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:67` | `if(reg==0x800000+chid*8){inst_=value;readInst_=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:68` | `if(reg>=0x002284 && reg<0x002284+16*8 && (reg-0x002284)%8==0)runlistClear_=!(value&0x00100000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:69` | `if(reg==0x002634)preemptClear_=!(value&0x00100000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:106` | `if(offset>=0x200 && offset<0x208)encoded=base;` | nvkm/subdev/mmu/vmmgf100.c:358 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:107` | `else if(offset>=0x208 && offset<0x210)encoded=limit;` | nvkm/subdev/mmu/vmmgf100.c:359 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:115` | `if(channelActive() && reg!=0x1700 && reg!=0x70000 && (reg<0x700000 \|\| reg>=0x800000))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:118` | `if(reg==0x1700) {` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:121` | `if(selected&0xfffff)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:127` | `if(reg==0x70000)return window && value==1;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:129` | `if(reg>=0x700000 && reg<0x800000)return window && physical(reg,r,offset) && dataValue(r,offset,value);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:132` | `if(reg==0x100c80) {` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:136` | `if(reg==0x100cb8) {` | nvkm/subdev/mmu/vmmgf100.c:185 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:137` | `if(!mode_ \|\| pdb_ \|\| phase>=3 \|\| commands_!=phase \|\| !(status_&0x00ff0000)` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:142` | `if(reg==0x100cbc) {` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:143` | `if(!pdb_ \|\| phase>=3 \|\| commands_!=phase \|\| value!=0x80000005)return false;` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:146` | `if(reg==0x1704) {` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:147` | `if(value&0x80000000) {` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:148` | `if(expectedContext_ \|\| context_&0x80000000 \|\| phase!=0 \|\| commands_!=1 \|\| !queued_` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:150` | `\|\| value!=(0x80000000\|uint32_t(r.physical.value>>12)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:154` | `&& context_==expectedContext_ && value==(expectedContext_&0x7fffffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:210` | `if(reg==0x000200 \|\| reg==0x000204 \|\| reg==0x002a04 \|\| reg==0x002634 \|\| reg==0x800000+chid*8 \|\| reg==0x800004+chid*8)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:211` | `if(reg>=0x002390 && reg<0x0023b0)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:212` | `if(reg>=0x002284 && reg<0x002284+16*8 && (reg-0x002284)%8==0)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:214` | `const auto base=p*0x2000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:215` | `if(reg==0x04013c+base \|\| reg==0x040108+base \|\| reg==0x040148+base)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:219` | `if(reg==0x104908 \|\| reg==0x104f14)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:220` | `if(engine(id) && reg==0x002640+id*8)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:253` | `const auto chanState=0x800004+chid*8,chanReg=0x800000+chid*8;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:258` | `if(step_>=13 && step_<=17 && reg==chanState && readState_ && value==(state_\|0x800))step_=18;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:259` | `if(step_>=6 && step_<=12 && reg==0x001704)step_=23;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:262` | `case 0: ok=reg==0x100cb8 && (status_&0x00ff0000) && value==uint32_t((roles[0].physical.value>>12)<<4);` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:264` | `case 1: ok=reg==0x100cbc && value==0x80000001;` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:269` | `ok=reg==0x100cb8 && (status_&0x00ff0000) && record(Role::Directory,bar)` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:273` | `case 4: ok=reg==0x100cbc && value==0x80000005;` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memnative/Policy.cpp:276` | `case 5: ok=reg==0x001704 && chanQueued_ && expectedContext_ && context_==(expectedContext_&0x7fffffff)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:279` | `case 6: ok=reg==0x000200 && value==0xffffffff;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:280` | `case 7: ok=reg==0x000204 && value==0xffffffff;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:281` | `case 8: ok=reg==0x000204 && probed_ && mask_ && mask_<=0xff && value==mask_;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:282` | `case 9: ok=reg==0x002a04 && read2a04_ && value==(value2a04_\|0xbfffffff);break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:283` | `case 10: ok=pbdma(p) && reg==0x04013c+p*0x2000 && readControl_ && value==(control_&~0x10000100u);break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:284` | `case 11: ok=reg==0x002254 && value==0x10000000;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:286` | `&& value==((state_&~0x000f0000u)\|(rl<<16));break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:287` | `case 13: ok=reg==chanReg && value==(0x80000000\|uint32_t(roles[2].physical.value>>12));` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:290` | `case 14: ok=reg==chanState && readState_ && value==(state_\|0x400);break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:291` | `case 15: ok=reg==0x002270 && value==runlistBase;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:292` | `case 16: ok=reg==0x002274 && value==((rl<<20)\|1);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:295` | `case 18: ok=reg==chanState && readState_ && value==(state_\|0x800);break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:296` | `case 19: ok=reg==0x002634 && value==chid;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:299` | `case 20: ok=reg==0x002270 && preemptClear_ && value==runlistBase;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:300` | `case 21: ok=reg==0x002274 && value==(rl<<20);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:304` | `case 23: ok=reg==0x001704 && expectedContext_ && context_==expectedContext_` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memnative/Policy.cpp:305` | `&& value==(expectedContext_&0x7fffffff);break;` | no source: ambiguous citation | SOURCE_ONLY |

## src/memnative/Policy.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memnative/Policy.h:8` | `constexpr uint32_t bar0View=16777216;` | no source: ambiguous citation | SOURCE_ONLY |

## src/memory/VramArena.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memory/VramArena.h:23` | `static constexpr unsigned capacity=16;` | no source: software ledger capacity. | SOURCE_ONLY |

## src/memstage/Channel.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Channel.cpp:8` | `constexpr uint32_t chanReg=0x800000+chid*8,chanState=0x800004+chid*8;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:10` | `constexpr Role roles[9]={Role::ChanDirectory,Role::ChanSmall,Role::ChanInstance,Role::Userd,Role::Gpfifo,Role::Push,Role::Runlist,` | no source: software allocation order of the channel roles. | SOURCE_ONLY |
| `src/memstage/Channel.cpp:101` | `if(i>=100000 \|\| !read(0x100c80,status))return fail(Error::Invalidate);` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:102` | `if(status&0x00ff0000)break;` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:105` | `if(!write(0x100cb8,uint32_t((addresses_.directory>>12)<<4))` | nvkm/subdev/mmu/vmmgf100.c:216 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:106` | `\|\| !write(0x100cbc,0x80000001))return false;` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:109` | `if(i>=100000 \|\| !read(0x100c80,status))return fail(Error::Invalidate);` | nvkm/subdev/mmu/vmmgf100.c:224 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:110` | `if(status&0x00008000)return true;` | nvkm/subdev/mmu/vmmgf100.c:224 | SOURCE_ONLY |
| `src/memstage/Channel.cpp:121` | `if(!write(0x000200,0xffffffff) \|\| !read(0x000200,value))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:123` | `if(!read(0x000204,value) \|\| !write(0x000204,0xffffffff) \|\| !read(0x000204,mask))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:124` | `if(!mask \|\| mask>0xff)return fail(Error::Routing,0x000204,mask);` | no source: software unit bound. | SOURCE_ONLY |
| `src/memstage/Channel.cpp:125` | `if(!write(0x000204,mask))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:129` | `if(!read(0x002390+p*4,runm))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:132` | `if(matches!=1)return fail(Error::Routing,0x002390,matches);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:133` | `if(!read(0x002a04,value) \|\| !write(0x002a04,value\|0xbfffffff))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:134` | `const auto control=0x04013c+report_.pbdma*0x2000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:135` | `if(!read(control,value) \|\| !write(control,value&~0x10000100u))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:136` | `return write(0x002254,0x10000000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:147` | `if(!write(chanState,(state&~0x000f0000u)\|(report_.runlist<<16))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:148` | `\|\| !write(chanReg,0x80000000\|uint32_t(addresses_.instance>>12))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:149` | `\|\| !read(chanState,state) \|\| !write(chanState,state\|0x400)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:150` | `\|\| !write(0x002270,uint32_t(addresses_.runlist>>12))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:151` | `\|\| !write(0x002274,(report_.runlist<<20)\|1))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:152` | `return waitClear(0x002284+report_.runlist*8,0x00100000,Error::Runlist);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:199` | `const auto status=0x002640+report_.engine*8;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:205` | `if(!(report_.engineStatus&0x80000000) \|\| report_.idleUs>=2000000)break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:209` | `return read(0x104908,report_.ceIntr) && read(0x104f14,report_.ceLaunchErr);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:221` | `const auto pb=report_.pbdma*0x2000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:222` | `return read(0x000100,report_.mc) && read(0x002100,report_.fifoIntr) && read(0x00259c,report_.mmuPending)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:223` | `&& read(0x040108+pb,report_.pbdmaIntr) && read(0x040148+pb,report_.pbdmaHce)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:233` | `if(!read(chanState,state) \|\| !write(chanState,state\|0x800)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:234` | `\|\| !write(0x002634,chid) \|\| !waitClear(0x002634,0x00100000,Error::Preempt)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:235` | `\|\| !write(0x002270,uint32_t(addresses_.runlist>>12)) \|\| !write(0x002274,report_.runlist<<20)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:236` | `\|\| !waitClear(0x002284+report_.runlist*8,0x00100000,Error::Runlist)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:263` | `&& !report_.pbdmaIntr && !report_.pbdmaHce && !(report_.fifoIntr&0x3fffffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Channel.cpp:267` | `return s1 && report_.copyGet==2 && report_.copyPut==2 && !(report_.engineStatus&0x80000000)` | no source: ambiguous citation | SOURCE_ONLY |

## src/memstage/ChannelImage.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/ChannelImage.cpp:60` | `add(0x08,userd);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:61` | `add(0x10,0x0000face);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:62` | `add(0x30,0xfffff902);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:64` | `add(0x48,(gpfifoVa&0xffffffff)\|((uint64_t(gpfifoVa>>32)\|(limit2<<16))<<32));` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:65` | `add(0x80,uint64_t(0x20400000)<<32);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:66` | `add(0x90,uint64_t(0x30000001)<<32);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:67` | `add(0x98,uint64_t(0x00000100)<<32);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:68` | `add(0xa8,uint64_t(0x0000001f)<<32);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:69` | `add(0xb8,0xf8000000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:70` | `add(0xe0,uint64_t(0x00000020)<<32);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:71` | `add(0xe8,chid);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:72` | `add(0xf8,0x10003080\|(uint64_t(0x10000010)<<32));` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:74` | `add(0x200,base);add(0x208,limit);break;` | nvkm/subdev/mmu/vmmgf100.c:346 | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:77` | `add(0,(pushVa&0xffffffff)\|((uint64_t(pushVa>>32)\|(8u<<8))<<32));` | nouveau_dma.c:83 | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:80` | `add(8,(va&0xffffffff)\|((uint64_t(va>>32)\|(copyPushBytes<<8))<<32));` | nouveau_dma.c:83 | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:89` | `add(16,pair(methodHeader(1,8,copySubchannel,copyOffsetIn),uint32_t(sourceVa>>32)&0xff));` | include/nvhw/class/cla0b5.h:95 | SOURCE_ONLY |
| `src/memstage/ChannelImage.cpp:90` | `add(24,pair(uint32_t(sourceVa),uint32_t(destVa>>32)&0xff));` | include/nvhw/class/cla0b5.h:96 | SOURCE_ONLY |

## src/memstage/ChannelImage.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/ChannelImage.h:8` | `constexpr uint32_t chid=1;` | no source: software choice, the ID of the Linux CE channel (mmiotrace line 562290). | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:9` | `constexpr uint64_t gpfifoVa=0x10000000;` | no source: software channel VA, distinct from physical and BAR VA. | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:10` | `constexpr uint64_t pushVa=0x10001000;` | no source: next small page in the same SPT. | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:11` | `constexpr uint32_t gpfifoBytes=4096;` | no source: one small page of 8-byte entries. | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:12` | `constexpr uint32_t userdSlot=chid*0x200;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:13` | `constexpr uint32_t gpGet=userdSlot+0x88,gpPut=userdSlot+0x8c;` | nouveau_dma.c:92 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:14` | `constexpr uint32_t nopHeader=0x20010002;` | no source: in the checked trees; envytools dma-pusher.rst line 417 header, open-gpu-doc cla16f.h line 74 NOP 0x08. | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:16` | `constexpr uint64_t sourceVa=0x10002000,destVa=0x10003000;` | nouveau_boa0b5.c:37 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:17` | `constexpr uint32_t copyBytes=4096;` | nouveau_boa0b5.c:57 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:18` | `constexpr uint32_t copySubchannel=4;` | include/nvif/push906f.h:19 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:19` | `constexpr uint32_t copyClass=0xa0b5;` | nouveau_bo.c:937 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:20` | `constexpr uint32_t copyOffsetIn=0x400;` | include/nvhw/class/cla0b5.h:94 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:21` | `constexpr uint32_t copyLaunchMethod=0x300;` | include/nvhw/class/cla0b5.h:37 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:24` | `constexpr uint32_t copyLaunch=0x00000386;` | include/nvhw/class/cla0b5.h:38 | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:25` | `constexpr uint32_t copyPushOffset=8,copyPushBytes=48;` | no source: after the NOP; 12 words, see image(). | SOURCE_ONLY |
| `src/memstage/ChannelImage.h:28` | `constexpr uint32_t methodHeader(uint32_t op,uint32_t count,uint32_t subchannel,uint32_t method)` | include/nvif/push906f.h:22 | SOURCE_ONLY |

## src/memstage/Experiment.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Experiment.cpp:8` | `if(!io_.read32(0x22438,probe_.parts))return false;` | nvkm/subdev/fb/ramgf108.c:30 | SOURCE_ONLY |
| `src/memstage/Experiment.cpp:10` | `if(!io_.read32(0x2243c,probe_.units))return false;` | nvkm/subdev/fb/ramgf108.c:31 | SOURCE_ONLY |
| `src/memstage/Experiment.cpp:12` | `if(!io_.read32(0x22554,probe_.disabled))return false;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/memstage/Experiment.cpp:16` | `if(!io_.read32(0x11020c+unit*0x1000,probe_.mib[unit]))return false;` | nvkm/subdev/fb/ramgf100.c:467 | SOURCE_ONLY |

## src/memstage/Faults.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Faults.cpp:33` | `if(!read(base+i*0x800+word*4,value))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:43` | `if(!read(0x022700+i*4,word))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:47` | `current.instance=(word&0x3c000000)>>26;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:48` | `current.address=word&0x00fff000;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:49` | `if(word&4){current.fault=(word&0x000003f8)>>3;current.hasFault=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:52` | `if(word&0x20){current.engine=(word&0x3c000000)>>26;current.hasEngine=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:53` | `if(word&0x10){current.runlist=(word&0x01e00000)>>21;current.hasRunlist=true;}` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:55` | `case 3:current.type=(word&0x7ffffffc)>>2;hasType=true;break;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:57` | `continuation=(word&0x80000000)!=0;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:75` | `if(!read(0x000100,mc))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:81` | `if(!read(0x002100,fifo) \|\| !read(0x00259c,mask))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:85` | `if(!read(0x002800+unit*16+word*4,value))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:89` | `if(!read(0x120058,priv0) \|\| !read(0x12005c,priv1)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:90` | `\|\| !read(0x120070,hubs) \|\| !read(0x120074,rops) \|\| !read(0x120078,gpcs))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:93` | `if(!details(priv0,0x122120,hubs,8) \|\| !details(priv0,0x124120,rops,16)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Faults.cpp:94` | `\|\| !details(priv1,0x128120,gpcs,0))return false;` | no source: ambiguous citation | SOURCE_ONLY |

## src/memstage/Mapper.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Mapper.cpp:43` | `if(!read(0x001704,context))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:44` | `if(context&0x80000000)return fail(Error::Dirty,0x001704,context);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:58` | `if(!read(0x100c80,value))return false;` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:61` | `if(!journal_.append({phase_,Error::None,0x100c80,value,i+1,last_-start,Operation::Poll}))return fail(Error::Overflow);` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:73` | `if(!poll(0x00ff0000))return false;` | nvkm/subdev/mmu/vmmgf100.c:199 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:74` | `return write(0x100cb8,uint32_t(selector))` | nvkm/subdev/mmu/vmmgf100.c:185 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:75` | `&& write(0x100cbc,0x80000005)` | nvkm/subdev/mmu/vmmgf100.c:221 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:76` | `&& poll(0x00008000);` | nvkm/subdev/mmu/vmmgf100.c:224 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:84` | `uint64_t fingerprint=0xcbf29ce484222325ULL;` | no source: software FNV-1a evidence checksum. | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:116` | `if(!read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:117` | `if(current!=(enabled_&0x7fffffff))return fail(Error::Dirty,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:119` | `if(!write(0x001704,enabled_) \|\| !upload_.flush() \|\| !upload_.flush())return fail(upload_.error()==Error::None?Error::Write:upload_.error());` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:129` | `if(!read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:130` | `if(current!=enabled_)return fail(Error::Dirty,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:131` | `if(!write(0x001704,enabled_&0x7fffffff) \|\| !read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:132` | `if(current!=(enabled_&0x7fffffff))return fail(Error::Compare,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:146` | `if(!read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:147` | `if(current&0x80000000)return fail(Error::Dirty,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:164` | `\|\| !upload_.patch(instance_,0x200,base) \|\| !upload_.patch(instance_,0x208,limit))return fail(upload_.error());` | nvkm/subdev/mmu/vmmgf100.c:358 | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:169` | `if(!read(0x100c80,mode) \|\| !write(0x100c80,mode&~uint32_t(1)) \|\| !read(0x100c80,mode))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:170` | `if(mode&1)return fail(Error::Profile,0x100c80,mode);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:174` | `enabled_=0x80000000\|uint32_t(inst);closure_=Closure::RetainedUnknown;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:175` | `if(!write(0x001704,enabled_) \|\| !upload_.flush() \|\| !upload_.flush())return fail(upload_.error()==Error::None?Error::Write:upload_.error());` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:182` | `if(!read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:183` | `if(current!=enabled_)return fail(Error::Dirty,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:184` | `if(!write(0x001704,enabled_&0x7fffffff) \|\| !read(0x001704,current))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Mapper.cpp:185` | `if(current!=(enabled_&0x7fffffff))return fail(Error::Compare,0x001704,current);` | no source: ambiguous citation | SOURCE_ONLY |

## src/memstage/Port.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Port.h:26` | `static constexpr unsigned capacity=4096;` | no source: resident diagnostic capacity. | SOURCE_ONLY |

## src/memstage/Upload.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/memstage/Upload.cpp:37` | `const auto word=uint32_t(physical>>2)^uint32_t(physical>>32)^0xa53c9e71;` | no source: software address-dependent test pattern. | SOURCE_ONLY |
| `src/memstage/Upload.cpp:48` | `const auto base=physical&~uint64_t(0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:50` | `if(!io_.write32(0x001700,uint32_t(base>>16)))return fail(Error::Write,0x001700);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:52` | `return journal_.append({phase_,Error::None,0x001700,uint32_t(base>>16),0,last_-start_,Operation::Write}) \|\| fail(Error::Overflow);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:57` | `if(!io_.write32(0x070000,1))return fail(Error::Write,0x070000,1);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:58` | `if(!journal_.append({phase_,Error::None,0x070000,1,0,last_-start_,Operation::Write}))return fail(Error::Overflow);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:66` | `if(!io_.read32(0x070000,value))return fail(Error::Read,0x070000);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:71` | `if(!journal_.append({phase_,Error::None,0x070000,value,poll+1,last_-start,Operation::Poll}))return fail(Error::Overflow);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:96` | `const auto reg=0x700000+uint32_t(physical&0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:174` | `const auto reg=0x700000+uint32_t(physical&0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/memstage/Upload.cpp:182` | `const auto reg=0x700000+uint32_t(physical&0xfffff);` | no source: ambiguous citation | SOURCE_ONLY |

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

## src/os/HaikuMemory.h

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/os/HaikuMemory.h:39` | `static constexpr size_t capacity = 16;` | no source: software ownership-record capacity, not a GPU limit. | SOURCE_ONLY |

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
| `src/runtime/Bootstrap.cpp:112` | `if(!port.executionAllowed() \|\| id>15 \|\| address>=(1ULL<<40) \|\| (address&0xfff)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:113` | `\|\| entries>0xfffff \|\| !limits.timeoutUs \|\| !limits.attempts)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:117` | `return port.write32(0x002270,(aperture<<28)\|uint32_t(address>>12))` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:118` | `&& port.write32(0x002274,(id<<20)\|entries)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/Bootstrap.cpp:119` | `&& poll(port,0x002284+id*8,0x00100000,limits);` | no source: ambiguous citation | SOURCE_ONLY |

## src/runtime/PreStart.cpp

| Line | Code | Source | Status |
|------|------|--------|--------|
| `src/runtime/PreStart.cpp:69` | `if (!registers_.write32(0x000140 + leaf * 4, 0)) return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:71` | `return registers_.read32(0x000140, drain);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:77` | `if (!allowed() \|\| !registers_.read32(0x02240c, state)) return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:86` | `return bytes_.write8(0x6013d4, 0x1f)` | nvkm/engine/disp/vga.c:130 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:87` | `&& bytes_.read8(0x6013d5, oldLock)` | nvkm/engine/disp/vga.c:100 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:88` | `&& bytes_.write8(0x6013d4, 0x3f)` | nvkm/engine/disp/vga.c:135 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:89` | `&& bytes_.write8(0x6013d5, 0x57);` | nvkm/engine/disp/vga.c:131 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:96` | `{0x122318,0x1000},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:97` | `{0x12231c,0x0200},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:98` | `{0x122310,0x0800},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:99` | `{0x122348,0x0100},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:100` | `{0x1223b0,0x0fff},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:101` | `{0x122348,0x0200},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:102` | `{0x122358,0x2880},` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:105` | `if (!masked(setting.reg, 0x0003ffff, setting.value)) return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:111` | `if (!allowed() \|\| bus.type != 0x05 \|\| bus.share != 0xff \|\| bus.drive > 15) return false;` | nvkm/subdev/i2c/padgf119.c:42 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:112` | `return registers_.write32(0x00d014 + uint32_t(bus.drive) * 0x20, 7);` | nvkm/subdev/i2c/busgf119.c:69 | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:118` | `return registers_.write32(0x100c10, uint32_t(address.value >> 8));` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:125` | `return masked(0x000200, 0x00000100, 0)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:126` | `&& masked(0x000200, 0x00000100, 0x00000100)` | no source: ambiguous citation | SOURCE_ONLY |
| `src/runtime/PreStart.cpp:127` | `&& registers_.read32(0x000200, drain);` | no source: ambiguous citation | SOURCE_ONLY |

## Open

The following constant lines have no source citation:

- src/a7/ArmAuthority.cpp:8 (no source: software request framing magic and version.)
- src/a7/ArmAuthority.cpp:9 (no source: software grant framing magic and version.)
- src/a7/ArmAuthority.cpp:15 (no source: RFC 8032 sections 5.1,5.1.7 subgroup order for signature verification.)
- src/a7/ArmAuthority.cpp:16 (no source: continuation of the RFC 8032 subgroup order, not a hardware constant.)
- src/a7/ArmAuthority.h:9 (no source: software request/grant frame sizes, not hardware packets.)
- src/a7/NativePlatform.cpp:33 (no source: software PCI identity comparison; KNOWN capture hardware/record.json:4.)
- src/a7/NativePlatform.cpp:36 (no source: software type-0-only guard; Haiku PCI.h lines 727,733 define the mask and type.)
- src/a7/NativePlatform.cpp:48 (no source: software mapping ceiling, not a hardware aperture assertion.)
- src/a7/Owner.cpp:29 (no source: software identity comparison; KNOWN capture hardware/record.json:37.)
- src/a7/Owner.cpp:81 (no source: ambiguous citation)
- src/a7/Owner.cpp:82 (no source: ambiguous citation)
- src/a7/Owner.cpp:83 (no source: ambiguous citation)
- src/a7/Owner.cpp:85 (no source: ambiguous citation)
- src/a7/Owner.cpp:86 (no source: ambiguous citation)
- src/a7/Owner.cpp:87 (no source: ambiguous citation)
- src/a7/Owner.cpp:92 (no source: ambiguous citation)
- src/a7/Owner.cpp:93 (no source: ambiguous citation)
- src/a7/Owner.cpp:112 (no source: ambiguous citation)
- src/a7/Owner.cpp:115 (no source: ambiguous citation)
- src/a7/Owner.cpp:120 (no source: ambiguous citation)
- src/a7/Owner.cpp:154 (no source: software identity comparison; KNOWN capture hardware/record.json:37.)
- src/a7/Owner.cpp:199 (no source: ambiguous citation)
- src/a7/Owner.cpp:208 (no source: ambiguous citation)
- src/a7/Owner.cpp:241 (no source: software identity comparison; KNOWN capture hardware/record.json:37.)
- src/a7/Owner.cpp:243 (no source: ambiguous citation)
- src/a7/Owner.cpp:250 (no source: software scratch sample offsets within our owned page.)
- src/a7/Owner.cpp:252 (no source: ambiguous citation)
- src/a7/PostDiagnostics.h:9 (no source: software record/table bounds.)
- src/compute/LaunchDesc.h:23 (no source: derived)
- src/devinit/BoardCore.cpp:35 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:41 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:42 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:44 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:47 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:76 (no source: software sequence container; each hardware value has its own citation.)
- src/devinit/BoardCore.cpp:161 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:165 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:166 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:167 (no source: ambiguous citation)
- src/devinit/BoardCore.cpp:168 (no source: ambiguous citation)
- src/devinit/BoardCore.h:17 (no source: ambiguous citation)
- src/devinit/BoardPolicy.cpp:7 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/BoardPolicy.cpp:8 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/BoardPolicy.cpp:9 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/BoardPolicy.cpp:11 (no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.)
- src/devinit/BoardPolicy.h:7 (no source: software exact-image permission size, ADR 004 and reference/vbios/README.md.)
- src/devinit/BoundPost.cpp:42 (no source: ambiguous citation)
- src/devinit/BoundPost.cpp:100 (no source: exact captured ROM transaction policy.)
- src/devinit/BoundPost.cpp:101 (no source: software bitset index for the two captured ROM pairs.)
- src/devinit/BoundPost.cpp:146 (no source: ambiguous citation)
- src/devinit/I2c.cpp:12 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:43 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:164 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:176 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:177 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:227 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:228 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:246 (no source: ambiguous citation)
- src/devinit/PostImage.cpp:247 (no source: ambiguous citation)
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
- src/gr/Program.h:25 (no source: software marker for "".)
- src/gr/Program.h:26 (no source: software bound; program.py refuses more.)
- src/gr/Runner.cpp:6 (no source: ambiguous citation)
- src/gr/Runner.cpp:7 (no source: software poll-count bound above the time bound.)
- src/gr/Runner.cpp:45 (no source: ambiguous citation)
- src/gr/Runner.cpp:46 (no source: ambiguous citation)
- src/gr/Runner.cpp:47 (no source: ambiguous citation)
- src/gr/Runner.cpp:48 (no source: ambiguous citation)
- src/gr/Runner.cpp:51 (no source: ambiguous citation)
- src/memauth/Session.cpp:8 (no source: memory role/version framing.)
- src/memauth/Session.cpp:9 (no source: separate signed role/version framing.)
- src/memauth/Session.cpp:14 (no source: RFC 8032 subgroup order, signature canonicality.)
- src/memauth/Session.cpp:15 (no source: RFC 8032 subgroup order continuation.)
- src/memauth/Session.h:7 (no source: distinct software memory-phase frames.)
- src/memnative/NativeIo.cpp:14 (no source: fixed PCI identity, hardware/record.json.)
- src/memnative/NativeIo.cpp:17 (no source: type-0-only software profile, Haiku PCI.h lines 727,733.)
- src/memnative/Policy.cpp:12 (no source: ambiguous citation)
- src/memnative/Policy.cpp:13 (no source: ambiguous citation)
- src/memnative/Policy.cpp:22 (no source: ambiguous citation)
- src/memnative/Policy.cpp:23 (no source: ambiguous citation)
- src/memnative/Policy.cpp:29 (no source: ambiguous citation)
- src/memnative/Policy.cpp:30 (no source: ambiguous citation)
- src/memnative/Policy.cpp:31 (no source: ambiguous citation)
- src/memnative/Policy.cpp:38 (no source: ambiguous citation)
- src/memnative/Policy.cpp:48 (no source: ambiguous citation)
- src/memnative/Policy.cpp:49 (no source: ambiguous citation)
- src/memnative/Policy.cpp:50 (no source: ambiguous citation)
- src/memnative/Policy.cpp:51 (no source: ambiguous citation)
- src/memnative/Policy.cpp:52 (no source: ambiguous citation)
- src/memnative/Policy.cpp:53 (no source: ambiguous citation)
- src/memnative/Policy.cpp:57 (no source: ambiguous citation)
- src/memnative/Policy.cpp:62 (no source: ambiguous citation)
- src/memnative/Policy.cpp:63 (no source: ambiguous citation)
- src/memnative/Policy.cpp:64 (no source: ambiguous citation)
- src/memnative/Policy.cpp:65 (no source: ambiguous citation)
- src/memnative/Policy.cpp:66 (no source: ambiguous citation)
- src/memnative/Policy.cpp:67 (no source: ambiguous citation)
- src/memnative/Policy.cpp:68 (no source: ambiguous citation)
- src/memnative/Policy.cpp:69 (no source: ambiguous citation)
- src/memnative/Policy.cpp:115 (no source: ambiguous citation)
- src/memnative/Policy.cpp:118 (no source: ambiguous citation)
- src/memnative/Policy.cpp:121 (no source: ambiguous citation)
- src/memnative/Policy.cpp:127 (no source: ambiguous citation)
- src/memnative/Policy.cpp:129 (no source: ambiguous citation)
- src/memnative/Policy.cpp:132 (no source: ambiguous citation)
- src/memnative/Policy.cpp:146 (no source: ambiguous citation)
- src/memnative/Policy.cpp:147 (no source: ambiguous citation)
- src/memnative/Policy.cpp:148 (no source: ambiguous citation)
- src/memnative/Policy.cpp:150 (no source: ambiguous citation)
- src/memnative/Policy.cpp:154 (no source: ambiguous citation)
- src/memnative/Policy.cpp:210 (no source: ambiguous citation)
- src/memnative/Policy.cpp:211 (no source: ambiguous citation)
- src/memnative/Policy.cpp:212 (no source: ambiguous citation)
- src/memnative/Policy.cpp:214 (no source: ambiguous citation)
- src/memnative/Policy.cpp:215 (no source: ambiguous citation)
- src/memnative/Policy.cpp:219 (no source: ambiguous citation)
- src/memnative/Policy.cpp:220 (no source: ambiguous citation)
- src/memnative/Policy.cpp:253 (no source: ambiguous citation)
- src/memnative/Policy.cpp:258 (no source: ambiguous citation)
- src/memnative/Policy.cpp:259 (no source: ambiguous citation)
- src/memnative/Policy.cpp:276 (no source: ambiguous citation)
- src/memnative/Policy.cpp:279 (no source: ambiguous citation)
- src/memnative/Policy.cpp:280 (no source: ambiguous citation)
- src/memnative/Policy.cpp:281 (no source: ambiguous citation)
- src/memnative/Policy.cpp:282 (no source: ambiguous citation)
- src/memnative/Policy.cpp:283 (no source: ambiguous citation)
- src/memnative/Policy.cpp:284 (no source: ambiguous citation)
- src/memnative/Policy.cpp:286 (no source: ambiguous citation)
- src/memnative/Policy.cpp:287 (no source: ambiguous citation)
- src/memnative/Policy.cpp:290 (no source: ambiguous citation)
- src/memnative/Policy.cpp:291 (no source: ambiguous citation)
- src/memnative/Policy.cpp:292 (no source: ambiguous citation)
- src/memnative/Policy.cpp:295 (no source: ambiguous citation)
- src/memnative/Policy.cpp:296 (no source: ambiguous citation)
- src/memnative/Policy.cpp:299 (no source: ambiguous citation)
- src/memnative/Policy.cpp:300 (no source: ambiguous citation)
- src/memnative/Policy.cpp:304 (no source: ambiguous citation)
- src/memnative/Policy.cpp:305 (no source: ambiguous citation)
- src/memnative/Policy.h:8 (no source: ambiguous citation)
- src/memory/VramArena.h:23 (no source: software ledger capacity.)
- src/memstage/Channel.cpp:8 (no source: ambiguous citation)
- src/memstage/Channel.cpp:10 (no source: software allocation order of the channel roles.)
- src/memstage/Channel.cpp:121 (no source: ambiguous citation)
- src/memstage/Channel.cpp:123 (no source: ambiguous citation)
- src/memstage/Channel.cpp:124 (no source: software unit bound.)
- src/memstage/Channel.cpp:125 (no source: ambiguous citation)
- src/memstage/Channel.cpp:129 (no source: ambiguous citation)
- src/memstage/Channel.cpp:132 (no source: ambiguous citation)
- src/memstage/Channel.cpp:133 (no source: ambiguous citation)
- src/memstage/Channel.cpp:134 (no source: ambiguous citation)
- src/memstage/Channel.cpp:135 (no source: ambiguous citation)
- src/memstage/Channel.cpp:136 (no source: ambiguous citation)
- src/memstage/Channel.cpp:147 (no source: ambiguous citation)
- src/memstage/Channel.cpp:148 (no source: ambiguous citation)
- src/memstage/Channel.cpp:149 (no source: ambiguous citation)
- src/memstage/Channel.cpp:150 (no source: ambiguous citation)
- src/memstage/Channel.cpp:151 (no source: ambiguous citation)
- src/memstage/Channel.cpp:152 (no source: ambiguous citation)
- src/memstage/Channel.cpp:199 (no source: ambiguous citation)
- src/memstage/Channel.cpp:205 (no source: ambiguous citation)
- src/memstage/Channel.cpp:209 (no source: ambiguous citation)
- src/memstage/Channel.cpp:221 (no source: ambiguous citation)
- src/memstage/Channel.cpp:222 (no source: ambiguous citation)
- src/memstage/Channel.cpp:223 (no source: ambiguous citation)
- src/memstage/Channel.cpp:233 (no source: ambiguous citation)
- src/memstage/Channel.cpp:234 (no source: ambiguous citation)
- src/memstage/Channel.cpp:235 (no source: ambiguous citation)
- src/memstage/Channel.cpp:236 (no source: ambiguous citation)
- src/memstage/Channel.cpp:263 (no source: ambiguous citation)
- src/memstage/Channel.cpp:267 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:60 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:61 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:62 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:64 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:65 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:66 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:67 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:68 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:69 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:70 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:71 (no source: ambiguous citation)
- src/memstage/ChannelImage.cpp:72 (no source: ambiguous citation)
- src/memstage/ChannelImage.h:8 (no source: software choice, the ID of the Linux CE channel (mmiotrace line 562290).)
- src/memstage/ChannelImage.h:9 (no source: software channel VA, distinct from physical and BAR VA.)
- src/memstage/ChannelImage.h:10 (no source: next small page in the same SPT.)
- src/memstage/ChannelImage.h:11 (no source: one small page of 8-byte entries.)
- src/memstage/ChannelImage.h:12 (no source: ambiguous citation)
- src/memstage/ChannelImage.h:14 (no source: in the checked trees; envytools dma-pusher.rst line 417 header, open-gpu-doc cla16f.h line 74 NOP 0x08.)
- src/memstage/ChannelImage.h:25 (no source: after the NOP; 12 words, see image().)
- src/memstage/Faults.cpp:33 (no source: ambiguous citation)
- src/memstage/Faults.cpp:43 (no source: ambiguous citation)
- src/memstage/Faults.cpp:47 (no source: ambiguous citation)
- src/memstage/Faults.cpp:48 (no source: ambiguous citation)
- src/memstage/Faults.cpp:49 (no source: ambiguous citation)
- src/memstage/Faults.cpp:52 (no source: ambiguous citation)
- src/memstage/Faults.cpp:53 (no source: ambiguous citation)
- src/memstage/Faults.cpp:55 (no source: ambiguous citation)
- src/memstage/Faults.cpp:57 (no source: ambiguous citation)
- src/memstage/Faults.cpp:75 (no source: ambiguous citation)
- src/memstage/Faults.cpp:81 (no source: ambiguous citation)
- src/memstage/Faults.cpp:85 (no source: ambiguous citation)
- src/memstage/Faults.cpp:89 (no source: ambiguous citation)
- src/memstage/Faults.cpp:90 (no source: ambiguous citation)
- src/memstage/Faults.cpp:93 (no source: ambiguous citation)
- src/memstage/Faults.cpp:94 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:43 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:44 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:84 (no source: software FNV-1a evidence checksum.)
- src/memstage/Mapper.cpp:116 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:117 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:119 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:129 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:130 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:131 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:132 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:146 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:147 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:169 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:170 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:174 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:175 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:182 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:183 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:184 (no source: ambiguous citation)
- src/memstage/Mapper.cpp:185 (no source: ambiguous citation)
- src/memstage/Port.h:26 (no source: resident diagnostic capacity.)
- src/memstage/Upload.cpp:37 (no source: software address-dependent test pattern.)
- src/memstage/Upload.cpp:48 (no source: ambiguous citation)
- src/memstage/Upload.cpp:50 (no source: ambiguous citation)
- src/memstage/Upload.cpp:52 (no source: ambiguous citation)
- src/memstage/Upload.cpp:57 (no source: ambiguous citation)
- src/memstage/Upload.cpp:58 (no source: ambiguous citation)
- src/memstage/Upload.cpp:66 (no source: ambiguous citation)
- src/memstage/Upload.cpp:71 (no source: ambiguous citation)
- src/memstage/Upload.cpp:96 (no source: ambiguous citation)
- src/memstage/Upload.cpp:174 (no source: ambiguous citation)
- src/memstage/Upload.cpp:182 (no source: ambiguous citation)
- src/os/HaikuMemory.h:39 (no source: software ownership-record capacity, not a GPU limit.)
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
- src/runtime/PreStart.cpp:69 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:71 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:77 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:96 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:97 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:98 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:99 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:100 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:101 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:102 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:105 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:118 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:125 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:126 (no source: ambiguous citation)
- src/runtime/PreStart.cpp:127 (no source: ambiguous citation)

These constants may be verified by a mmiotrace in task C5.
