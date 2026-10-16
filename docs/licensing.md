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
