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
| `src/a7/Owner.cpp:70` | `if(width==1)return phase_==Phase::Crtc && (reg==0x6013d4 \|\| reg==0x6013d5);` | nvkm/engine/disp/vga.c:97 | SOURCE_ONLY |
| `src/a7/Owner.cpp:73` | `case Phase::Identity:return !write && (reg==0 \|\| reg==0x101000);` | nvkm/subdev/bios/ramcfg.c:29 | SOURCE_ONLY |
| `src/a7/Owner.cpp:74` | `case Phase::Interrupts:return (reg==0x140 \|\| reg==0x144) && (write \|\| reg==0x140);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:75` | `case Phase::Decision:return !write && reg==0x02240c;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:76` | `case Phase::Ring:return reg==0x122318 \|\| reg==0x12231c \|\| reg==0x122310 \|\| reg==0x122348 \|\| reg==0x1223b0 \|\| reg==0x122358;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:78` | `case Phase::Arm:return write && reg==0x100c10;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:79` | `case Phase::Fifo:return reg==0x200;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:80` | `case Phase::Readback:return !write && reg==0x100c10;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:82` | `if(!write && (reg==0 \|\| reg==0x100 \|\| reg==0x9400 \|\| reg==0x9410 \|\| reg==0x22438 \|\| reg==0x2243c \|\| reg==0x22554))return true;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:84` | `if(!write && reg>=0x11020c && reg<=0x12f20c && (reg-0x11020c)%0x1000==0)return true;` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:85` | `if(reg==0x070000)return true;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:86` | `if(scratchOwned_ && windowLocked_ && reg==0x1700)return write;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:87` | `if(scratchOwned_ && windowLocked_ && selector_==0 && reg>=0x740000 && reg<0x741000)return true;` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:103` | `if(phase_==Phase::Readiness && ((reg==0x1700 && value!=0) \|\| (reg==0x70000 && value!=1)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:106` | `if(!fifoRead_ \|\| fifoWrites_>=2 \|\| value!=((fifoReadValue_&~0x100u)\|(fifoWrites_?0x100u:0)))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:110` | `if(phase_==Phase::Readiness && reg==0x1700)selector_=value;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:125` | `if(!read32(0,value) \|\| value!=0x0f1240a1)return false;` | no source: software identity comparison; KNOWN capture hardware/record.json:37. | SOURCE_ONLY |
| `src/a7/Owner.cpp:146` | `i2cPin_=0x00d014+uint32_t(bus.drive)*0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |
| `src/a7/Owner.cpp:169` | `phase_=Phase::Readback;readback_=read32(0x100c10,value);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:178` | `if(!read32(0x9410,high) \|\| !read32(0x9400,low) \|\| !read32(0x9410,again))return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:187` | `if(!read32(0x22438,parts) \|\| !read32(0x2243c,units) \|\| !read32(0x22554,disabled)` | nvkm/subdev/fb/ramgf100.c:477 | SOURCE_ONLY |
| `src/a7/Owner.cpp:196` | `if(!read32(0x11020c+unit*0x1000,mib) \|\| !mib)return false;` | nvkm/subdev/fb/ramgf100.c:467 | SOURCE_ONLY |
| `src/a7/Owner.cpp:206` | `return activeParts && total==owner_.expectedVram_ && total>0x40000+0x100000+4096;` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:211` | `if(!read32(0,identity) \|\| identity!=0x0f1240a1 \|\| !timer(result.timerBefore)` | no source: software identity comparison; KNOWN capture hardware/record.json:37. | SOURCE_ONLY |
| `src/a7/Owner.cpp:213` | `\|\| !memorySize(result.vramBytes) \|\| !read32(0x100,result.pending) \|\| result.pending)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:220` | `const uint64_t offsets[]={0,0x100,0xffc};` | no source: software scratch sample offsets within our owned page. | SOURCE_ONLY |
| `src/a7/Owner.cpp:221` | `result.scratch=runtime::checkOwnedScratch(*this,{{0x40000},4096},offsets,3,{2000000,100000});` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |
| `src/a7/Owner.cpp:222` | `if(!result.scratch \|\| !read32(0x100,result.pending) \|\| result.pending)return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/a7/Owner.cpp:223` | `owner_.platform_.log("",0x40000,4096);return true;` | nvkm/subdev/fb/ramgf100.c:497 | SOURCE_ONLY |

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
| `src/devinit/BoundPost.cpp:41` | `bool allowed=inI2c_ && active_ && inst && inst->opcode==0x4d && (us==1 \|\| us==5);` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:44` | `if (inst->opcode==0x69) allowed=us==10000;` | nvkm/subdev/bios/init.c:1644 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:45` | `if (inst->opcode==0x56) allowed=active_ && us==20000;` | nvkm/subdev/bios/init.c:1246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:46` | `if (inst->opcode==0x74) {` | nvkm/subdev/bios/init.c:1769 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:79` | `if (!inst \|\| inst->opcode!=0x4d \|\| !boardAllowed(approvedRomDigest(),pc_,inst->opcode)) {` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:98` | `const bool sensor=pc_==0xab8d && bytes[1]==0x80 && address==0x4c` | nvkm/subdev/bios/init.c:1033 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:99` | `&& value==0x73 && (reg==0x19 \|\| reg==0x0d);` | no source: exact captured ROM transaction policy. | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:100` | `const unsigned pairBit=reg==0x19?1:2;` | no source: software bitset index for the two captured ROM pairs. | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:138` | `if (inst->opcode!=0x4d \|\| !boardAllowed(approvedRomDigest(),inst->offset,inst->opcode)) continue;` | nvkm/subdev/bios/init.c:2246 | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:145` | `if (!found \|\| bus.type!=0x05 \|\| bus.share!=0xff \|\| bus.drive>15) return false;` | no source: ambiguous citation | SOURCE_ONLY |
| `src/devinit/BoundPost.cpp:156` | `pin_=0x00d014+uint32_t(bus.drive)*0x20;` | nvkm/subdev/i2c/busgf119.c:93 | SOURCE_ONLY |

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
- src/a7/Owner.cpp:74 (no source: ambiguous citation)
- src/a7/Owner.cpp:75 (no source: ambiguous citation)
- src/a7/Owner.cpp:76 (no source: ambiguous citation)
- src/a7/Owner.cpp:78 (no source: ambiguous citation)
- src/a7/Owner.cpp:79 (no source: ambiguous citation)
- src/a7/Owner.cpp:80 (no source: ambiguous citation)
- src/a7/Owner.cpp:85 (no source: ambiguous citation)
- src/a7/Owner.cpp:86 (no source: ambiguous citation)
- src/a7/Owner.cpp:103 (no source: ambiguous citation)
- src/a7/Owner.cpp:106 (no source: ambiguous citation)
- src/a7/Owner.cpp:110 (no source: ambiguous citation)
- src/a7/Owner.cpp:125 (no source: software identity comparison; KNOWN capture hardware/record.json:37.)
- src/a7/Owner.cpp:169 (no source: ambiguous citation)
- src/a7/Owner.cpp:178 (no source: ambiguous citation)
- src/a7/Owner.cpp:211 (no source: software identity comparison; KNOWN capture hardware/record.json:37.)
- src/a7/Owner.cpp:213 (no source: ambiguous citation)
- src/a7/Owner.cpp:220 (no source: software scratch sample offsets within our owned page.)
- src/a7/Owner.cpp:222 (no source: ambiguous citation)
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
- src/devinit/BoundPost.cpp:41 (no source: ambiguous citation)
- src/devinit/BoundPost.cpp:99 (no source: exact captured ROM transaction policy.)
- src/devinit/BoundPost.cpp:100 (no source: software bitset index for the two captured ROM pairs.)
- src/devinit/BoundPost.cpp:145 (no source: ambiguous citation)
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
