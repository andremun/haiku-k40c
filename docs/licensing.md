# Licensing record

This project is under the MIT License (`LICENSE`). New source files carry:

    Copyright 2026 <author>. Distributed under the terms of the MIT License.

Why MIT: Haiku is MIT-licensed and asks for MIT for code that may be
merged, and the Nouveau code that this project studies is MIT-licensed.

| Source | License | Consequence |
|---|---|---|
| Haiku (`reference/haiku`) | MIT | Headers and interfaces may be used. Same license as this project. |
| Nouveau (`reference/nouveau`, Linux v6.12) | MIT in 403 file headers; one file `GPL-2.0 OR MIT`; one file `GPL-2.0-only` (`Kconfig`, not code); 54 files with neither an SPDX line nor the MIT text | Study and reimplement. Check the header of each consulted file and record it below. Take nothing from a file without a license notice. |
| Mesa (`reference/mesa`, nouveau driver and codegen) | MIT (check each file header) | Study and reimplement, as for Nouveau. A shader binary that Mesa generates for our own source is our output, not Mesa code. |
| envytools `rnndb` | MIT | Register names and bit fields may be used with the source cited. |
| NVIDIA open-gpu-doc | MIT (check each file) | As for envytools. |
| NVIDIA firmware and the proprietary driver | Proprietary | Never copy into this repository. Firmware is loaded from the user's system at run time (see phase C2). |

Reimplement, do not copy. A short constant table or register offset is a
fact and needs a source citation, not a license. A copied function or
block keeps its original notice and is listed in the last column below.

| Source file consulted | License (from header) | Used for | Copied material |
|---|---|---|---|

## V2 decoder build/reproduction (2026-10-16)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/envytools/nvbios/nvbios.c` | MIT notice in file | Decoder flags, separate initialization-pointer/script paths | None; compiled unchanged outside Git |
| `reference/envytools/envydis/core.c` | MIT notice in file | Decoder library linkage | None; compiled unchanged outside Git |
| `reference/envytools/easm/easm_lex.l`, `easm_parse.y` | Upstream license notices retained in external sources/generated build files | Lexer/parser generation | None in project source |
| envytools root and util/easm/envydis/nvbios `CMakeLists.txt` | Build metadata; upstream project licenses retained | Source-list extraction for an isolated decoder build | Filenames/build dependencies only |

No Nouveau or NVIDIA implementation was ported during V2. Firmware-derived
decoder text stays under ignored build/ or the user's external mediaflux mount.

## ABC1 independent cardless implementation (2026-10-16)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nvkm/subdev/bios/init.c` | MIT notice retained in source | Opcode lengths/control state, repeat/call/condition/mask behavior; GPIO/I2C/IO helper gates | Constants/semantic facts with citations; no function bodies copied |
| `reference/nouveau/nvkm/subdev/bios/bit.c`, `ramcfg.c`, `base.c` | MIT notices retained | BIT-I/M root/table metadata and cached RAM selection | Format facts only |
| `reference/envytools/nvbios/nvbios.c`, `print.c` | MIT notices retained | Listing presentation, split instruction explanation | Format facts only |
| `reference/open-gpu-doc/Devinit/devinit.xml` | Upstream license retained | Specification identifiers/condition attributes for cross-reference | Attribute metadata only |
| `reference/nouveau/nvkm/subdev/instmem/nv50.c`, `subdev/bar/g84.c`, `subdev/fb/gf100.c` | MIT notices retained | Slow-window, flush and pre-POST page facts | Constants/algorithm facts; no copied functions |
| `reference/nouveau/nvkm/engine/fifo/gk104.c`, `gf100.c`, `gk110.c` | MIT notices retained | Runlist commit vs preempt, channel sequencing | Constants/format facts only |
| `reference/nouveau/nvkm/subdev/mmu/vmmgf100.c` | MIT notice retained | Invalidation dependencies for design checklist | No code copied |
| `reference/haiku/headers/os/drivers/PCI.h`, `KernelExport.h`, `headers/os/kernel/OS.h`, `src/add-ons/kernel/drivers/graphics/nvidia/driver.c` | Haiku MIT license | Native PCI mapping/allocation/timing/module API and high BAR word handling | API/format facts, own implementation |

Host test shims are expressly not Haiku ABI evidence; actual native headers are
used independently in cross builds. Firmware payloads/complete decoded listings
are never embedded in source or committed. The offline simulator reads the
user-provided image at runtime and records only aggregate results.

## S1C documentation correction (2026-10-27)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nvkm/engine/disp/vga.c` | MIT notice in file | NV50+ byte-wide VGA MMIO routing | Semantic facts only |
| `reference/nouveau/nvkm/subdev/bios/init.c` | MIT notice in file | INIT_IO helper effects and unconditional waits | Semantic facts only |

## S1BOARD host-only policy and helpers (2026-10-27)

Every file below has an MIT notice. No Nouveau function body was copied.
The new implementation uses semantic facts and cited hardware constants only.

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nvkm/subdev/bios/init.c` | MIT notice | IO waits/side effects, I2C byte addressing, GPIO_NE exclusions | Constants and semantic facts only |
| `reference/nouveau/nvkm/engine/disp/vga.c` | MIT notice | NV50+ byte MMIO and CRTC index/data order | Constants and semantic facts only |
| `reference/nouveau/nvkm/subdev/gpio/base.c` | MIT notice | First matching function/line and GPIO logic levels | Semantic facts only |
| `reference/nouveau/nvkm/subdev/gpio/gf119.c` | MIT notice | GPIO drive, latch, and reset routing | Constants and semantic facts only |
| `reference/nouveau/nvkm/subdev/gpio/gk104.c` | MIT notice | 32 lines and inherited GF119 helpers | Semantic facts only |
| `reference/nouveau/nvkm/subdev/bios/dcb.c` | MIT notice | DCB pointer and signature | Format facts only |
| `reference/nouveau/nvkm/subdev/bios/gpio.c` | MIT notice | GPIO 4.1 layout and duplicate matching | Format facts only |
| `reference/nouveau/nvkm/subdev/bios/i2c.c` | MIT notice | CCB 4.0/4.1 layout and bus descriptors | Format facts only |
| `reference/nouveau/nvkm/subdev/i2c/base.c` | MIT notice | Default bus lookup | Semantic facts only |
| `reference/nouveau/include/nvkm/subdev/i2c.h` | SPDX MIT | CCB indices and primary/secondary meanings | Constants only |
| `reference/nouveau/include/nvkm/subdev/bios/gpio.h` | SPDX MIT | Unused function and GPIO logic bits | Constants only |
| `reference/nouveau/include/nvkm/subdev/bios/i2c.h` | SPDX MIT | NVIO and PMGR bus identifiers | Constants only |
| `reference/nouveau/nvkm/engine/device/base.c` | MIT notice | GK110B GPIO/I2C dispatch | Semantic facts only |
| `reference/haiku/headers/os/drivers/PCI.h` | Haiku MIT | Meaning of bus-master bit in the recorded B5 command word | Constant only |

SHA-256 uses algorithm facts from NIST FIPS 180-4, sections 4.1.2, 4.2.2,
5.1.1, 5.3.3, and 6.2. No library implementation was copied.
Source: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf.

## S1B2 native allocation adapter (2026-10-27)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/haiku/src/add-ons/kernel/drivers/graphics/nvidia/driver.c` | Haiku MIT | Contiguous DMA32 allocation choice and physical alignment | API and semantic facts only |
| `reference/haiku/headers/os/kernel/OS.h` | Haiku MIT | B_32_BIT_CONTIGUOUS meaning | API constant only |
| `reference/haiku/headers/os/drivers/PCI.h` | Haiku MIT | Native adapter type inclusion and existing PCI interface | API declarations only |

The adapter introduces no GPU register constants or Nouveau-derived implementation.

## Host-flush-page and pre-start dependency research (S1B2/S1A4 batch)

All files below carry MIT notices. No implementation was copied.
The source facts explain the mapping and pre-start obligations that remain gated.

| Source files consulted | Used for |
|---|---|
| `reference/nouveau/nvkm/subdev/devinit/gf100.c`, `base.c`, `nv04.c`, `nv50.c` | Selected POST callback, preinit decision, CRTC unlock, and script roots |
| `reference/nouveau/nvkm/core/subdev.c` | Difference between preinit, oneinit, and normal init |
| `reference/nouveau/nvkm/subdev/fb/base.c`, `gf100.c` | Flush-page allocation, DMA mapping, pre-POST programming, and lifetime |
| `reference/nouveau/nvkm/engine/device/pci.c` | Resume-only PCI preinit branch |
| `reference/nouveau/nvkm/subdev/i2c/gk110.c`, `padgf119.c`, `busgf119.c`, `pad.c`, `bus.c` | Selected pad/bus constructors and early bus initialization |
| `reference/nouveau/nvkm/subdev/mc/base.c`, `bus/base.c`, `timer/base.c` | Check which lifecycle callbacks exist before POST |

## S1A4 selected pre-start lifecycle

Source facts only; no implementation blocks copied.

- `reference/nouveau/nvkm/subdev/i2c/padg94.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/i2c/bit.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/privring/gk104.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/engine/fifo/base.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/pci/base.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/mc/gk104.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/mc/nv04.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/mc/gt215.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/core/intr.c`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/include/nvkm/core/layout.h`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/include/nvkm/core/device.h`: MIT; selected lifecycle, register semantics, or callback dispatch.
- `reference/nouveau/nvkm/subdev/fb/gk110.c`: MIT; selected lifecycle, register semantics, or callback dispatch.

## S1C2 integration choices

MIT sources; semantic and constant facts only. No implementation blocks copied.

- `reference/nouveau/nvkm/subdev/mmu/gk104.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/subdev/mmu/vmmgk104.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/subdev/mmu/vmmgf100.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/subdev/bar/gf100.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/subdev/bar/g84.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/subdev/top/gk104.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/gk110.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/gk104.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/gf100.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/nv50.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/chan.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/cgrp.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/runl.c`: selected geometry, publication, routing, or teardown semantics.
- `reference/nouveau/nvkm/engine/fifo/uchan.c`: selected geometry, publication, routing, or teardown semantics.

## S1A6 POST inputs and dedicated I2C candidate

Source facts and constants only. No implementation blocks copied.

| Source consulted | License | Purpose |
|---|---|---|
| `reference/nouveau/nvkm/subdev/bios/init.c` | MIT | POST roots, tables, encoded registers, conditions, macros and write framing |
| `reference/nouveau/nvkm/subdev/bios/ramcfg.c` | MIT | Group count, strap cache input and translation fallback |
| `reference/nouveau/nvkm/subdev/bios/M0203.c` | MIT | First-match strap/group table |
| `reference/nouveau/include/nvkm/subdev/bios/M0203.h` | SPDX MIT | Reviewed RAMCFG table type |
| `reference/nouveau/nvkm/subdev/bios/dcb.c`, `gpio.c`, `i2c.c` | MIT | Board-table versions, entries and bounds |
| `reference/nouveau/nvkm/subdev/devinit/base.c`, `gf100.c` | MIT | Selected MMIO dispatch boundary |
| `reference/nouveau/nvkm/subdev/i2c/bit.c` | MIT | Optional internal START/STOP, byte/ACK and bounded stretch semantics |
| `reference/nouveau/nvkm/subdev/i2c/busgf119.c` | MIT | Dedicated pin drive/sense and initialization |

The internal algorithm is a SOURCE_ONLY candidate. Capture configuration remains UNKNOWN.

## S1NATIVE module lifetime and DMA boundary

Haiku MIT sources only. API declarations and semantic facts, no implementation
blocks copied. Nouveau was not consulted for this task.

- `reference/haiku/headers/os/drivers/module.h`: module_info, standard operations,
  KEEP_LOADED flag, and get_module/put_module interface.
- `reference/haiku/headers/private/kernel/kmodule.h`: distinction between raw
  image loading and module acquisition.
- Haiku commit `49a0af9585d80e42240af63ab66e31e9873f59b8`,
  `src/system/kernel/module.cpp`: permanent reference and initialized-state lifetime.
- Same commit, `src/system/kernel/device_manager/legacy_drivers.cpp`: driver
  uninitialization and add-on unload. These two sparse-omitted files were retrieved
  from official raw.githubusercontent URLs into /tmp, not added to reference/.
- `reference/haiku/src/add-ons/kernel/drivers/graphics/nvidia/driver.c`:
  existing module reference use. Only relevant get/put ranges were consulted.

Source URLs and hash record are in docs/NATIVE-OWNER.md and
work/S1NATIVE/source-hashes.log. The cross-source module.cpp is byte-identical.

## S1OWNERTEST cardless staging and reload

Haiku MIT semantic/API facts only. No implementation blocks copied.
Consulted pinned commit 49a0af9585d80e42240af63ab66e31e9873f59b8:

- src/system/kernel/module.cpp:336-343,632-654: user/nonpackaged module paths.
- src/system/kernel/device_manager/legacy_drivers.cpp:259-264,300-355,463-476:
  driver paths, empty-node unload, and uninit lifecycle.
- src/system/kernel/fs/vfs.cpp:4426-4494: module path resolution stops at the image file.
- src/system/libroot/os/find_directory.cpp:148-181: user config/nonpackaged add-ons.
- Existing module.h and Drivers.h API declarations used through the matching cross headers.

Sparse-omitted sources were read from exact official raw.githubusercontent URLs
into /tmp. Source hashes are saved in work/S1OWNERTEST/source-hashes.log.

## S1POST immutable binding and per-instruction policy

All consulted Nouveau files carry MIT notices. Constants and semantic facts only;
no implementation blocks copied. Source paths below are under reference/nouveau/.

- nvkm/subdev/bios/init.c: selected POST dispatch, table lookup, opcode lengths,
  register wrapper, condition/macro operands, IO helper, and GPIO_NE exclusion.
- nvkm/subdev/bios/base.c: BIT signature discovery.
- nvkm/subdev/bios/bit.c: BIT entry fields and stride.
- nvkm/subdev/bios/ramcfg.c and M0203.c: cached strap selection and group lookup.
- nvkm/subdev/bios/dcb.c, gpio.c and i2c.c: reviewed board-table fields.
- nvkm/subdev/gpio/gf119.c: GPIO drive/latch/routing access addresses.
- nvkm/subdev/i2c/base.c and busgf119.c: default bus and dedicated pin register.
- nvkm/engine/disp/vga.c: indexed byte MMIO addresses, via existing reviewed helpers.

Board permission identity/size remain software decisions from ADR 004 and the
existing VBIOS record. They were moved, not expanded. SHA-256 uses the previously
recorded NIST algorithm facts. No new external algorithm implementation was copied.

## S1HELPERS freestanding board helpers

Independent refactor of the existing MIT implementation. No source blocks copied.
Reconsulted only the existing pinned Nouveau semantic ranges:

- nvkm/subdev/bios/gpio.c:28-64,103-110: byte-sized count and GPIO 4.1 records.
- nvkm/subdev/i2c/busgf119.c:27-93: dedicated pins, sense fields and init value.
- nvkm/subdev/i2c/bit.c:90-150: START/STOP and bit delay/ACK behavior.

Existing cited helper/CCB semantics remain unchanged. No firmware bytes were added.

## S1OWNERPOST resident binding and host simulation

No new external implementation or hardware source was consulted. This task uses
the already recorded Haiku module lifetime and bound-interpreter source facts.
Resident storage and host fixture code are original MIT work. No firmware bytes
were added. The native module ABI and board permissions remain unchanged.

## S1DMACONTRACT address/visibility source audit

Source/API facts only. No external implementation blocks or files were copied
into the driver. Additional source copies remain outside reference/ and the repo.
Content hashes and exact URLs are in work/S1DMACONTRACT/evidence.json.

- QEMU upstream v6.2.0 and exact Ubuntu 1:6.2+dfsg-2ubuntu6.31 source:
  hw/vfio/common.c, hw/vfio/pci.c, hw/pci/pci.c, hw/vfio/trace-events.
  VFIO C files carry GPL version 2 notices. The PCI bus manager has an MIT notice.
  Only mapping facts and trace-event metadata were used.
  The package patch-series metadata was recorded for reconstruction.
- Linux upstream v6.8 drivers/vfio/vfio_iommu_type1.c: GPL-2.0 source facts.
  This was not asserted to be the exact running Ubuntu -138 implementation.
- Haiku pin 49a0af9585d80e42240af63ab66e31e9873f59b8: vm.cpp, VMArea.cpp,
  VMArea.h, X86VMTranslationMap64Bit.cpp, X86PagingMethod64Bit.h and the existing
  x86/64/atomic.h. MIT/NewOS notices remain with the consulted originals.
- Nouveau nvkm/subdev/fb/base.c, gf100.c, gk110.c and bar/g84.c: existing MIT
  source ranges for DMA-mapped flush storage, hook selection and BAR completion.

No physical protocol or sentinel semantics were imported from an unverified source.

## S1DMAMODEL unmap observation semantics

Reconsulted Linux v6.8 drivers/vfio/vfio_iommu_type1.c:1279-1426 under the already
recorded content pin. GPL-2.0-only source facts about Type1/V2 whole-map removal
and returned size were reimplemented as an original host diagnostic model. No
implementation blocks were copied. No native provider or hardware API was added.

## S1D0OBSERVER userspace decoder

Exact Ubuntu strace 5.16-0ubuntu3 source was reconstructed outside reference/.
Consulted src/ioctl.c: ioctl dispatch, entry/exit return flags and generic output;
src/pathtrace.c: descriptor/path filtering; src/nsfs.c: API usage example only.
These files carry LGPL-2.1-or-later notices. No implementation block was copied.
The original MIT decoder include and build helper produce a separate userspace
observer, not code linked into the MIT driver. Upstream notices remain in the
ignored external build tree. Installed Linux userspace vfio.h API facts use its
GPL-2.0 WITH Linux-syscall-note UAPI terms. Exact hashes and package versions are
recorded in work/S1D0OBSERVER/. No proprietary firmware or device data was copied.

## S1D0PACKAGE observation and topology

Reconsulted exact Ubuntu QEMU 6.2+dfsg-2ubuntu6.31 source facts:
`hw/vfio/common.c` group/container/device association and mapping;
`softmmu/memory.c:3188-3255` FlatView formatting;
`softmmu/physmem.c:1300-1320` ramblock formatting;
`monitor/qmp-cmds.c` and `hmp-commands-info.hx` read-only query names;
`softmmu/qdev-monitor.c` qtree formatting;
`hw/core/qdev-properties-system.c:801-825` full host BDF property;
`util/osdep.c:292-307` close-on-exec open behavior.
The existing source pin set is in `work/S1DMACONTRACT/evidence.json`.
Consulted strace `src/defs.h` and `src/util.c` bounded NUL-terminated string
printing, and reconsulted `src/pathtrace.c`. Existing upstream license notices
remain in the external trees. Original helpers decode API facts and text formats.
No implementation blocks or new Nouveau code were copied.

## S1D0THREAD task and file-table proof

Reconsulted exact Ubuntu strace 5.16-0ubuntu3 `src/ioctl.c`, `src/pathtrace.c`
and `src/desc.c` (LGPL-2.1-or-later). The added helper and parser are original MIT
code. The close hook is one original helper call. No upstream implementation
block was copied. The private build retains upstream notices and is not linked
into the driver. The exact desc.c hash and fixture pins are recorded by
`tools/observer/task_pins.py`. Linux `kcmp.h` and `sys/syscall.h` supply public
syscall constants. The consulted kcmp(2) man page documents KCMP_FILES equality
and read-access checks. No additional Nouveau source or device protocol was used.

## S1A7NATIVE prerequisite audit

Reconsulted pinned Nouveau `nvkm/subdev/fb/base.c`, `fb/gf100.c`, `fb/gk110.c`,
`devinit/base.c`, `devinit/gf100.c`, `engine/device/base.c` and
`include/nvkm/core/layout.h` for constructor, preinit and POST ordering. These
are existing MIT reference sources. No source blocks were copied and no new
hardware constant was introduced. ESC-002 records the source-only findings.

## S1A7NATIVE arm-only implementation

Reconsulted pinned Nouveau `fb/base.c`, `fb/gf100.c`, `fb/gk110.c`,
`fb/ramgf100.c`, `fb/ramgf108.c`, `fb/ramgk104.c`, `timer/nv04.c`,
`timer/nv41.c`, `timer/regsnv04.h`, and the previously listed preinit/board
sources for original arm, topology and readiness code. No source blocks copied.
Reconsulted Haiku nvidia driver BAR mechanics and `util/Random.h`/`Random.cpp`
for the exported instance-challenge function, not an entropy guarantee.

The verification-only dependency is orlp/ed25519 at the exact revision recorded
by tools/a7/crypto_sources.py. Its original zlib notice stays in the external
checkout. It is not attributed to this project's author. No key generation or
signing source is linked into the native module. RFC 8032 supplies the canonical
signature-scalar rule. Original wrapper, memory and stage code remain MIT.

A7 also consults Haiku `headers/os/drivers/PCI.h:159-164,240,686` for
cooperative reservation and read-only command-register interpretation. The
read-only upstream Linux v6.8 VFIO teardown baseline is separately pinned in
`work/S1A7NATIVE/teardown-sources.json` (GPL-2.0 kernel sources, not linked or
copied). It is not represented as exact running Ubuntu source. The original
ed25519 zlib notice is also copied into the private build package.

## S1A7NITS source audit

Reconsulted `nvkm/subdev/i2c/base.c`, `busgf119.c`, `pad.c`, `padg94.c`,
`padgf119.c`, `gk104.c`, `gf119.c`, `nvkm/subdev/bios/i2c.c`, `dcb.c`,
`shadowrom.c`, `shadowpci.c`, and `nvkm/subdev/pci/base.c`, `nv40.c`,
`gf100.c`, `gk104.c` for the omission table and source-selected register path.
The original board/table parser was refactored, not copied from Nouveau.
No Linux pad, bus or shadow implementation block was copied or executed.
The same zlib Ed25519 revision now lives in a persistent pinned external checkout.

## S1A7INSTALL publication diagnosis

Consulted Haiku `src/system/kernel/device_manager/devfs.cpp`,
`device_manager/legacy_drivers.cpp` and `fs/vfs.cpp` at the project's pinned
revision, captured outside reference/ by tools/a7/install_sources.py.
Also inspected the same source paths in the existing b42b90f5 cross checkout
as a baseline before obtaining the exact reference revision. Source records
separate that evidence from the unestablished running-kernel source identity.
The new shell installation and publication-wait functions are original code.
No Haiku implementation blocks were copied. No additional Nouveau file was used.


## S1A7I2C diagnosis (2026-10-29)

Consulted pinned Nouveau nvkm/subdev/bios/init.c:1033-1056 (unchecked I2C return),
i2c/bit.c (internal bit framing and STOP), i2c/busgf119.c:37-69 (drive/sense),
i2c/bus.c:138-150,230-245 (bus acquisition and algorithm selection),
i2c/pad.c:27-33,55-70 (mode logging/callback dispatch),
i2c/padgf119.c:43-48 and i2c/base.c:285-295 (dedicated-pad selection).
All carry the existing MIT notices. Only semantic facts were used. No function
bodies were copied. Response decoder, telemetry and scoped policy are original.

## S1A7STARTUP diagnosis (2026-10-29)

Consulted Haiku Book driver introduction/functions and pinned Haiku
49a0af9585d80e42240af63ab66e31e9873f59b8 KernelExport.dox, OS.h,
kernel debug.cpp, arch_debug_console.cpp, timer.cpp, thread.cpp,
legacy_drivers.cpp, PCI pci.cpp and graphics/nvidia/driver.c.
Consulted QEMU v6.2.0 serial.c, char-fd.c, channel-file.c and kvm-all.c as an
explicit upstream baseline, and the existing strace primary manual's
seccomp-BPF/filter description. Source URLs and SHA-256 records are saved in
work/S1A7STARTUP/source-pins.json; external files stay in ignored build cache.
Haiku MIT and QEMU/strace GPL sources were used for semantic diagnosis only.
No implementation bodies were copied. Host benchmark and analysis are original.
No additional Nouveau source was used beyond the already recorded interpreter
and I2C references.

## S1MEMCONTRACT source study (2026-10-29)

Reconsulted Nouveau engine/device/base.c; core/memory.c;
subdev/instmem/base.c,nv50.c; subdev/fb/base.c,gf100.c,gk110.c,ram.c,ramgf100.c;
subdev/bar/gf100.c,g84.c; subdev/mmu/gf100.c,gk104.c,vmmgf100.c,vmmgk104.c;
engine/fifo/gf100.c,gk104.c; and subdev/privring/gk104.c.
Used semantic facts, formats and register references only; no implementation
body was copied. Haiku KernelExport.h and x86 atomic.h at the project pin,
plus separately pinned vm.cpp/arch_vm.cpp, define the candidate explicit UC
mapping and CPU-ordering API. Full running source identity remains unestablished.
The new combined stage is not a modification of run7's A7 source.

## S1MEMARENA source study (2026-10-29)

Reconsulted Nouveau subdev/fb/ramgf108.c:30-44 for per-FBP amount grouping
and its one-LTC-per-FBP result, and ramgf100.c for the normal-heap test and
head/tail reservations. The ledger and independent interval oracle are original.

## S1MEMFAULTS source study (2026-10-29)

Reconsulted Nouveau engine/fifo/gf100.c:699-729, gk104.c:634-703;
subdev/privring/gk104.c:28-94; fb/gf100.c:37; and top/gk104.c:37-106.
Raw-read formats and bounded topology semantics only; no source bodies copied.
No interrupt acknowledgement, fault clear, PBDMA probe or scheduler write added.

## S1MEMMMU source study (2026-10-29)

Reconsulted Nouveau subdev/mmu/gk104.c:29, vmmgk104.c:39-78,
vmmgf100.c:35,105-143,180-233,314-360; bar/gf100.c:38-58,93-109;
fb/gf100.c:66-77; and fb/ramgk104.c:1703 for the selected RAM probe chain.
Pure field encoders, scoped invalidation and BAR1 sequencing are original.
The slow-window 44-bit mask is not a 44-bit PTE address claim; selected PTE
addresses are restricted to 40 bits below VOL/target fields.

## S1MEMPACKAGE source study (2026-10-30)

Reconsulted the selected Nouveau slow-window, BAR, FB and gk104 MMU sources
listed by the five memory tasks. New resident authority, value policy, controller
and host composition are original. The unchanged A7 implementation is reused.
Consulted Haiku KernelExport.h, PCI.h, module.h, Drivers.h, Errors.h, Random.h and
x86/64/atomic.h for the exported APIs, raw status and explicit UC/ordering request.
Local build/header hashes are recorded; full running kernel source identity is
not established. Consulted QEMU v6.2.0 qapi/pci.json for fixed read-only query-pci
fields and bridge nesting. Its content pin is in work/S1MEMPACKAGE/qmp-pci-source.json;
it is an upstream schema baseline, not an exact Ubuntu source identity claim.
No Nouveau/Haiku/QEMU implementation body was copied. The pinned verification-only
orlp Ed25519 code remains unchanged under its separate zlib notice, included in
the new package. No signing code or private key is included in a guest artifact.

## S1BATCH2PLAN source study (2026-10-30)

Consulted Nouveau engine/device/base.c:1777-1805; engine/fifo/gk110.c:35-128;
gk104.c:40-165,180-465,735-810; gf100.c:35-165,310-395,910-955;
base.c:136-160,306-324; chan.c:135-192,350-485; runl.c:70-105;
subdev/mmu/gk104.c:23-41, vmmgk104.c:23-78 and
vmmgf100.c:180-235,310-375; nouveau_dma.c:35-125;
nouveau_dma.h PUT definitions and nouveau_chan.c:295-315,430-460;
engine/fifo/uchan.c:259-270 and include/nvif/if0020.h:1-24;
include/nvif/class.h channel class definition. Reconsulted
subdev/mc/gk104.c and nv04.c reset/interrupt definitions.
Consulted open-gpu-doc classes/host/cla16f.h:24-215 and cla06f.h NOP/packet
fields, and envytools rnndb/fifo/nv_object.xml NOP entries.
Only source anchors, field facts and design consequences enter this package.
No Nouveau implementation body was copied and no runtime code changed.

## S1CHANNEL (2026-10-31)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nvkm/engine/fifo/gk104.c` | MIT notice in file | Channel bind/start/stop, RAMFC, runlist, PBDMA init, USERD BAR1 base, interrupt bits | Semantic facts only |
| `reference/nouveau/nvkm/engine/fifo/gf100.c` | MIT notice in file | PBDMA discovery, runq init, preempt | Semantic facts only |
| `reference/nouveau/nvkm/engine/fifo/gk110.c` | MIT notice in file | GK110 channel/preempt selection | Semantic facts only |
| `reference/nouveau/nvkm/subdev/top/gk104.c` | MIT notice in file | TOP engine types | Semantic facts only |
| `reference/nouveau/nvkm/subdev/mmu/vmmgf100.c` | MIT notice in file | PTE bits, invalidate type | Semantic facts only |
| `reference/nouveau/nouveau_dma.c` | MIT notice in file | GPFIFO entry, GP_PUT | Semantic facts only |
| `reference/open-gpu-doc/classes/host/cla16f.h` | MIT notice in file | USERD layout, NOP method | Facts only |
| `reference/envytools/docs/hw/fifo/dma-pusher.rst`, `rnndb/fifo/gf100_pfifo.xml` | MIT | Method header format, BAR1_BASE | Facts only |

## S2COPY (2026-11-12)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nouveau_boa0b5.c` | MIT notice in file | Copy method sequence and launch flags | Semantic facts only |
| `reference/nouveau/nouveau_bo.c` | MIT notice in file | Copy class, subchannel and object handle | Semantic facts only |
| `reference/nouveau/include/nvhw/class/cla0b5.h` | MIT notice in file (NVIDIA) | Method offsets and LAUNCH_DMA fields | Facts only |
| `reference/nouveau/include/nvhw/class/cl906f.h` | MIT notice in file (NVIDIA) | Method header fields | Facts only |
| `reference/nouveau/include/nvif/push906f.h` | MIT | Subchannel of the copy class, header macros | Facts only |
| `reference/nouveau/nvkm/engine/ce/gk104.c` | MIT notice in file | Interrupt status, launch error code | Semantic facts only |
| `reference/nouveau/nvkm/engine/fifo/gk104.c` | MIT notice in file | Engine status register, copy-engine functions without context | Semantic facts only |

## S3GR (2026-11-12)

| Source file consulted | License | Used for | Copied material |
|---|---|---|---|
| `reference/nouveau/nvkm/engine/gr/gf100.c`, `gf100.h` | MIT notice in file | Order of engine start, hooks, ZBC, context-control start, unit address macros | Semantic facts only |
| `reference/nouveau/nvkm/engine/gr/gk104.c`, `gk110.c`, `gk110b.c`, `gf117.c` | MIT notice in file | GK110B hook functions and function table | Semantic facts only |
| `reference/nouveau/nvkm/engine/gr/*.c` register tables | MIT notice in files | Register address and value tables, read at run time by `tools/gr/tables.py` | None in this repository: the tool reads the pinned tree |
| `reference/nouveau/nvkm/engine/gr/fuc/hubgk110.fuc3.h`, `gpcgk110.fuc3.h` | MIT (Red Hat) | The four microcode arrays, read at run time by `tools/gr/model.py` | None yet; the native build will embed them with their notice |
| `reference/nouveau/nvkm/falcon/v1.c` | MIT notice in file | Data and code load protocol | Semantic facts only |
| `reference/nouveau/nvkm/subdev/ltc/gf100.c` | MIT notice in file | ZBC table registers | Semantic facts only |

