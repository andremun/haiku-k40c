# K40c initialization: documentation and implementation research

Research date: 2026-10-13

## Outcome

Useful public documentation exists. The most important discovery is NVIDIAs official Devinit opcode specification. Together with its BIOS Information Table and Device Control Block specifications, this provides a substantially better foundation than extracting apparent writes from a debug log.

Recommendation: build a bounded, state-aware executor for the actual cards initialization bytecode, cross-checked against the successful Nouveau reference. Keep the Linux capture as corroborating evidence. Do not treat flat write replay as an equivalent initialization procedure.

This is a documentation and source review. No hardware access, reset, VM operation, firmware modification, or script execution was performed. No complete K40c cold-start register recipe was found in the inspected documentation.

## 1. Official NVIDIA Devinit specification

Primary source: [Devinit opcode specification](https://github.com/NVIDIA/open-gpu-doc/blob/master/Devinit/devinit.xml). Alternative: [NVIDIA download directory](https://download.nvidia.com/open-gpu-doc/Devinit/1/).

The specification covers a portable GPU initialization bytecode engine: instruction layouts, execution conditions, register operations, delays, polling, subroutines, GPIO, I2C and memory-selection operations. It says engines should preserve instruction semantics, subject to documented platform adaptations. This supports implementing bytecode semantics instead of captured outcomes.

Some names differ from Nouveau. Match numeric opcodes:

| Opcode | Nouveau log name | NVIDIA specification name |
|---|---|---|
| 0x56 | CONDITION_TIME | INIT_POLL_NV |
| 0x4D | ZM_I2C_BYTE | INIT_ZM_ALTERNATING_I2CREG |
| 0x8F | RAM_RESTRICT_ZM_REG_GROUP | INIT_XMEMSEL_ZM_NV_REG_ARRAY |
| 0xA9 | GPIO_NE | INIT_GPIO_EXCLUDE_ARRAY |
| 0x58 | ZM_REG_SEQUENCE | INIT_REG_ARRAY |

The GPIO operation initializes functions except an exclusion list; the listed functions are not necessarily the functions changed. Polling can change execution state on timeout. Memory-array selection depends on a board memory strap and translation data.

The document is a language specification, not a complete GK110B register manual. Applicability to the actual ROM and helpers still requires verification.

## 2. Official BIOS Information Table specification

Source: [NVIDIA BIOS Information Table specification](https://download.nvidia.com/open-gpu-doc/BIOS-Information-Table/1/BIOS-Information-Table.html).

The BIT describes GPU/board-specific structures. Token I identifies initialization data, including script, macro and condition-table pointers. Token M includes memory strap/translation information and memory-programming pointers. Other tokens cover clocks and I2C-related data.

This provides a documented route from ROM bytes to the inputs needed by an executor. It also describes ROM image handling, checksums and pointer adjustments when UEFI images intervene. A fixed 64-KiB ROM assumption is inadequate as a general parser rule.

Implementation implications:

- Parse lengths, versions, pointer bounds and checksums before decoding scripts.
- Use the table version and available length; do not assume every field in the latest specification exists in the K40c ROM.
- Preserve complete image data and record its hash and acquisition provenance.
- Separate initialization bytecode from unrelated display and performance scripts through the actual call path.

## 3. Official GPIO and I2C board-data specification

Source: [NVIDIA Device Control Block 4.x specification](https://download.nvidia.com/open-gpu-doc/DCB/2/DCB-4.x-Specification.html).

This documents GPIO assignment fields, logical/physical states, initialization behavior, external GPIO controllers, and I2C device descriptions. The I2C device classifications include thermal, fan and power-control devices.

It is useful for the safety questions raised by the supplied logs active GPIO_NE and I2C operations. Decode the actual ROM tables to identify affected functions, controllers and addresses before classifying those operations. These documents alone do not identify the two I2C devices seen in this specific log.

Do not infer a devices function solely from its address, or equate a GPIO function tag with a physical pin number. Apply the cards own board data.

## 4. Nouveau sources matching the reference kernel generation

The package ran Ubuntu kernel 6.8.0-146 and analyzed a separate 6.12 source snapshot. The links below use upstream v6.8, a closer reference than current mainline, but not proof of identity with Ubuntus patched kernel. Compare relevant differences against the projects pinned tree.

| Source | Purpose |
|---|---|
| [devinit/gf100.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/devinit/gf100.c) | POST decision and selected initialization hooks. |
| [devinit/base.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/devinit/base.c) | Lifecycle, preinitialization and POST dispatch. |
| [devinit/nv50.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/devinit/nv50.c) | Additional initialization, including encoder scripts where applicable. |
| [bios/init.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/bios/init.c) | Bytecode execution and hardware helper calls. |
| [bios/ramcfg.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/bios/ramcfg.c) | Board strap and memory-configuration selection. |
| [bios/shadow.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/bios/shadow.c) | VBIOS source selection and usable-image handling. |
| [bios/shadowrom.c](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/bios/shadowrom.c) | PROM acquisition and surrounding ROM-shadow control. |

The gf100 path checks bit 1 of 0x2240c to decide whether to POST. Its comment identifies a devinit marker that clears on suspend. This is not an independent readiness test for an experimental replay.

The lifecycle includes work outside the bytecode stream. Trace the complete selected path and prerequisites; do not implement only bios/init.c and assume its environment exists.

### A concrete specification/implementation difference

Opcode 0x56 is described by NVIDIA with timeout units of 100 milliseconds. Linux v6.8 computes a capped retry count and polls with 20-ms delays; its worst-case sleep budget is two seconds. This follows directly from min(retry * 50, 100) and mdelay(20).

These descriptions are not identical. Record and review discrepancies rather than silently combining the specification with captured timings. The validated Linux implementation and actual board script are essential references.

Nouveaus I2C instruction also converts the encoded address before printing it. A log-derived decoder must distinguish bytecode encoding from the address already displayed by the driver.

## 5. Offline VBIOS analysis with envytools

Sources: [envytools project](https://github.com/envytools/envytools), [nvbios decoder](https://github.com/envytools/envytools/blob/master/nvbios/nvbios.c), [decoder directory](https://github.com/envytools/envytools/tree/master/nvbios).

nvbios takes a saved ROM file. It supports printing scripts, BIT, GPIO, I2C and external-device data, and decoding a script at a specified offset. This offers an independent view of bytecode and tables without operating the GPU.

Examples for a previously acquired, verified ROM file:

```sh
nvbios -p bit k40c.rom
nvbios -p scripts k40c.rom
nvbios -p gpio k40c.rom
nvbios -p i2c k40c.rom
nvbios -p extdev k40c.rom
```

These are proposed offline commands, not executed results. Check the pinned tools help before use. Do not substitute envytools direct hardware-access utilities for the file decoder.

The supplied review archive contains no ROM file. Consequently, this research cannot establish actual script coverage, identify the board controllers, or generate the full initialization dependency inventory.

## 6. A concrete route through the memory bootstrap gap

Source: [Linux v6.8 nv50 instance-memory implementation](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/instmem/nv50.c).

nv50_instobj_wr32_slow and nv50_instobj_rd32_slow implement a physical-memory access window. They select its base with register 0x001700 and access data through BAR0 offsets beginning at 0x700000. The code locks the shared window selection. Its faster path uses BAR2 mappings, and release includes ordering and BAR-flush operations.

This is SOURCE_ONLY evidence for a practical bootstrap design: use the reviewed physical window to populate initial GPU objects, then establish mapped access. It does not prove VRAM is usable before card initialization, and it is not a standalone safe register recipe. Review address masks, allocation ownership, locking and visibility against the exact chip path before use.

Supplementary documentation: [envytools PEEPHOLE](https://envytools.readthedocs.io/en/latest/hw/memory/peephole.html), [memory documentation index](https://envytools.readthedocs.io/en/latest/hw/memory/index.html).

PEEPHOLE describes another indirect memory-access mechanism, including GF100-and-later behavior. Keep it distinct from the PRAMIN window above. Prefer the path used by the successful reference until an alternative is independently justified.

## 7. Useful documentation with limited applicability

[NVIDIA GK104/GK106 graphics power-gating note](https://download.nvidia.com/open-gpu-doc/gk104-disable-graphics-power-gating/1/gk104-disable-graphics-power-gating.txt) explains on-boot graphics power gating, read-modify-write requirements and sequencing. Its explicit scope is GK104/GK106, not GK110B. It is context for investigating the corresponding Nouveau path, not authorization to apply that sequence to the K40c.

The [NVIDIA open documentation index](https://download.nvidia.com/open-gpu-doc/) also lists memory-clock and memory-tweak tables. They are supporting references to investigate when actual ROM contents require them; their presence does not prove every relevant K40c memory-training register is documented.

The [PROM documentation](https://envytools.readthedocs.io/en/latest/hw/io/prom.html) contains useful register-range information but substantial unfinished sections. Use it alongside the actual source rather than as a complete acquisition specification.

## 8. Recommended next investigation

1. Obtain the existing complete ROM capture through the projects authorized evidence process. Hash it and associate it with the development board; do not borrow another K40 variant or modify firmware.
2. Pin NVIDIA documentation, envytools and the exact Nouveau references. Record version differences with the reference kernel.
3. Decode BIT, initialization scripts, macros, condition tables, memory selection, GPIO and I2C data offline.
4. Build a reachable-bytecode inventory including alternative branches, not only instructions active in one log. Reject unsupported operations and malformed bounds explicitly.
5. Correlate script offsets with the supplied dmesg log and matching raw MMIO capture. Include helper effects and work before/after the scripts.
6. Implement a limited executor preserving live reads, masks, copying, branches, delays, polling and audited board operations. Maintain semantics rather than hardcoding the observed branch outcomes.
7. Verify on host models with changing conditions, timeout cases, skipped writes, nested calls and board-policy violations.
8. Review a concrete first hardware experiment with an immutable operation policy, recovery procedure and independent readiness checks. The initialized marker and matching emitted writes are insufficient by themselves.

These are recommendations, not started development tasks. The existing requirement for separately reviewed hardware experiments remains in force.

## Remaining uncertainty

The public material reduces uncertainty about the initialization language and table formats. It does not supply the cards ROM, prove the selected script/helper subset complete, establish safe board-controller operations, or certify initialization from the chosen reset state.

Assessment: a documented interpreter or semantics-preserving executor is now a more concrete option. Blind replay remains unsupported, while the lack of a single complete public GK110B initialization manual makes source and capture correlation necessary.
