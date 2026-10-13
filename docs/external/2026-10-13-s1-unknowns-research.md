# S1 unknowns: source and documentation research

Research date: 13 October 2026. Scope: the eleven unknowns in your supplied plan. The host NOP is accepted as settled; S3 is excluded.

## Outcome

The strongest new findings concern **8 and 10**. The page-size and flush path can be specified from the selected chip implementation, and a reproducible comparison substantially narrows the upstream 6.8/6.12 mismatch. Unknown **6** also has strong source support. Unknowns **1–4 and 7** still require card-specific evidence, but the required checks and their dependencies can be made more precise.

One dependency may reshape the tracks: Nouveau prepares a DMA-addressed host flush page **before BIOS POST**. If A7 follows that environment, it needs part of B2 before the final merge of tracks. Another correction: a small BAR mapping and access to all physical VRAM are different requirements; S1 need not map the entire VRAM capacity into Haiku.

This is research, not implementation or experiment approval. No GPU, PCI configuration, reset, VM or device node was accessed. The original review packages remain unchanged. The full board ROM and newer local reference tree mentioned in your message were not supplied here; I accept your NOP verification but cannot decode those board tables in this workspace.

**KNOWN / SOURCE_ONLY** below means directly established in source or documentation. **INFERRED** identifies a proposed consequence or test. **UNKNOWN** requires the chosen environment, ROM or hardware result. Downloaded upstream files are preserved with SHA-256 hashes in [the source manifest](research-evidence-s1/SOURCE-MANIFEST.json). Linux release tags are v6.8 and v6.12; Haiku and envytools snapshots follow master and are identified by content hash. The QEMU reference is v8.2.0, not a claim about your installed QEMU.

## Status of each unknown

| # | Research outcome | What still closes it |
|---|---|---|
| 1 | No general proof of scheduling without GR; source identifies runlist and PBDMA dependencies | A controlled card test with GR omissions and fault state recorded |
| 2 | The interpreter is only part of the pre-POST environment | Actual ROM reachability plus selected preinit/helper inventory and reset-state test |
| 3 | No universal independent readiness bit found; staged functional checks are possible | Reviewed scratch-memory test and later translation/FIFO tests |
| 4 | DCB and GPIO helpers provide a concrete classification process | Actual board tables; controller datasheets where tables are insufficient |
| 5 | Default VFIO/QEMU mapping supports guest-physical DMA addresses; Haiku x86 PCI helper is identity | Verify actual virtual-IOMMU configuration, bounds and GPU DMA access |
| 6 | Physical PRAMIN fallback explicitly bootstraps mapped instance memory | Card test after VRAM bring-up, with ownership and publication established |
| 7 | Reset scope can exceed one device; a reset is not proof of a cold board state | Actual method, affected topology and repeatable post-reset observations |
| 8 | GK110 framebuffer defaults, VMM geometry, BAR flush and translation invalidation identified | Implement the selected path and compare with capture/card outcomes |
| 9 | Address fields and several control-word roles can be named | Retain remaining opaque constants with provenance; validate masks and owned addresses |
| 10 | 28 of 31 compared source pairs are byte-identical; important changed sections narrowed | Ubuntu patch/source-package comparison and exact project revision |
| 11 | Haiku provides physical-device mappings; full VRAM mapping is unnecessary for bootstrap | Selected 64-bit guest, BAR placement, mapping and safe access checks |

## 1. Scheduler with GR uninitialised

**KNOWN / SOURCE_ONLY:** GK110 uses the shared GK104 FIFO setup and Kepler-B channel class. Runlists are assembled from TOP descriptors, and PBDMA/runlist associations come from hardware masks. The GR-associated runlist also receives a software-engine entry. These are real scheduling dependencies, even though the NOP itself is a host method. [GK110 FIFO selection](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/gk110.c), [GK104 runlist construction](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/gk104.c#L756).

**UNKNOWN:** whether that configuration runs with GR register setup, controller firmware and channel GR context omitted. Source separation is not a demonstrated hardware mode.

**INFERRED:** the C2 recipe should record the selected runlist, PBDMA routing and channel-group mode explicitly. On a timeout, collect channel/runlist/PBDMA and engine-switch state before deciding that GR is required. Memory faults, a disabled channel or a pending runlist update can produce the same visible lack of GET progress. A failed NOP test alone would not identify which GR startup subset to add.

## 2. Executor environment before and after scripts

**KNOWN / SOURCE_ONLY:** device preinit disarms interrupts, runs the device hook and every constructed subdevice's preinit, then POST, TOP parsing and framebuffer memory unlock. Thus a script-only trace omits surrounding work. The GK110B selection includes separate bus, GPIO, I2C, framebuffer, timer, MC and private-ring implementations. [Device preinit and chip selection](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/device/base.c#L2890).

The selected framebuffer constructor allocates and DMA-maps a host page, and framebuffer preinit programs its flush address. This occurs before POST. Its lifetime must cover the relevant hardware operations. [Framebuffer lifecycle](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/fb/base.c#L225).

The BIOS POST dispatcher walks the ordinary script table and an additional script pointer. `CONDITION_TIME` can turn execution off on timeout; interpreter state also includes forced execution, so a single Boolean “skip writes” model is insufficient. [BIOS interpreter and POST](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/bios/init.c#L2322).

**INFERRED:** A3/A4 should produce two inventories: reachable bytecode and helper/preinit effects. Give each helper its prerequisites, address domain, failure semantics and ordering. Your rule that Nouveau wins resolves compatibility choices, but should not conceal a tolerated I2C failure or timeout: record it and decide whether that dependency is required. Keep caller-context-dependent display scripts conditional on the actual board tables.

## 3. Independent evidence that bring-up worked

The devinit marker remains a POST-decision hint, not a success criterion for this executor. [Selected POST decision](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/devinit/gf100.c#L91).

**INFERRED: use a ladder of checks, each proving a limited property.**

| Check | Evidence it supplies | Limit |
|---|---|---|
| Stable identity and permitted MMIO reads; timer advances where applicable | Register path and some clock activity are alive | Does not show VRAM training or scheduler readiness |
| Baseline then post-operation bus/private-ring fault snapshot | Detects certain invalid or timed-out MMIO transactions | Absence of faults does not prove successful work |
| Reserved VRAM scratch patterns read back through PRAMIN | Tested storage locations and the physical access path work | Not a whole-VRAM or GPU-translation test |
| After mapping, read the same owned data through a second reviewed aperture | Exercises that mapping and catches some address-domain mistakes | Still does not prove channel DMA |
| New GET reaches new PUT without fault | The stated S1 milestone | Requires separate teardown proof |

For the reviewed A7 scratch test, use uncached device access, distinct address-dependent patterns and complements, repeat reads after changing the window selection, and compare multiple owned locations to detect aliases. Include window/page boundaries only where the scratch allocation owns both sides. Keep expected data in host memory. Passing this test says “these regions are usable,” not “all memory partitions are trained.” Use the host monotonic clock for timeouts; do not depend on a potentially broken GPU timer to enforce them.

**KNOWN / SOURCE_ONLY:** Nouveau's bus handler distinguishes engine, private-ring and timeout faults using status `0x001100`, with details at `0x009084/0x009088`; handling also acknowledges status. Read the raw baseline and outcome before any acknowledgement. [Bus fault decoding](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/bus/gf100.c#L35). The timer implementation uses high/low/high sampling to avoid a torn counter. [Timer read](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/timer/nv04.c#L43).

## 4. GPIO and I2C targets

**KNOWN / SOURCE_ONLY:** NVIDIA's DCB specification describes voltage-select, thermal, power-sense, fan, mux and generic-initialisation functions, plus external GPIO controllers. An unidentified function or address is not enough to classify an operation. [NVIDIA DCB specification](https://nvidia.github.io/open-gpu-doc/DCB/DCB-4.x-Specification.html).

GK104's GPIO implementation selects `gf119_gpio_reset`. That helper applies board defaults and changes routing/mux registers as well as calling the logical GPIO setter. Its effects exceed one output-bit write. [GK104 GPIO selection](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/gpio/gk104.c), [GPIO reset helper, v6.8 inspected](https://github.com/torvalds/linux/blob/v6.8/drivers/gpu/drm/nouveau/nvkm/subdev/gpio/gf119.c#L27).

The interpreter's `GPIO_NE` resets defined functions **outside** the exclusion list. I2C bus selectors can name default buses; encoded slave addresses are shifted right by one. Therefore classify the resolved physical bus and 7-bit address, not a raw instruction operand. [Interpreter board operations](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/bios/init.c#L2186).

**INFERRED:** A5's review table should contain script offset, reachable branch, operation, resolved bus/controller/line, function, direction/polarity/default, register and mask, and helper side effects. Where the ROM names a device type but not a part number or register meaning, obtain its actual datasheet or board evidence. Classify power, voltage, cooling and protection controls separately; unresolved targets remain unresolved. A register allow-list alone is insufficient when a GPIO helper can route the pin to another function. No board-operation approval is issued by this report.

## 5. Guest host-memory addresses

**KNOWN / SOURCE_ONLY:** in the inspected QEMU VFIO implementation, ordinary RAM mappings derive the device IOVA from the memory region's offset in the device address space; with the ordinary system-memory address space and no virtual IOMMU, this corresponds to the guest physical address. A virtual IOMMU uses a separate notifier/translation path. [QEMU v8.2 VFIO mappings](https://github.com/qemu/qemu/blob/v8.2.0/hw/vfio/common.c#L541). VFIO maps IOVAs to host memory through the host IOMMU; host physical addresses are not what the guest driver should invent. [Linux VFIO documentation](https://www.kernel.org/doc/html/v6.8/driver-api/vfio.html).

Haiku's `get_memory_map` reports physical segments; the x86 implementation of `pci_ram_address` returns its input. That PCI helper is not an IOMMU mapping operation and is also used in BAR address translation. [Haiku physical-memory interfaces](https://github.com/haiku/haiku/blob/master/headers/os/drivers/KernelExport.h#L193), [Haiku PCI address helper](https://github.com/haiku/haiku/blob/master/src/add-ons/kernel/bus_managers/pci/pci.cpp#L129).

The selected GK104 MMU declares a **40-bit DMA width**. Validate complete DMA ranges against it; do not merely truncate encoded high bits. [Selected MMU](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/mmu/gk104.c#L27).

**INFERRED:** B2 can start with pinned, explicitly bounded guest-physical segments if the actual VM uses that default mapping. Record virtual-IOMMU and VFIO backend configuration. Keep CPU virtual, guest physical/device IOVA, GPU virtual, VRAM physical and BAR-aperture addresses as separate types. CPU readback of a host allocation does not prove the GPU can DMA it; later controlled GPU consumption/readback must test that direction. A virtual IOMMU or device-address remapping changes this conclusion.

## 6. Slow window before GPU translation

**KNOWN / SOURCE_ONLY:** Nouveau's slow instance-memory access uses the VRAM address, selects a 1-MiB window with `0x001700`, and accesses BAR0 at `0x700000 + low-offset`. It serialises window selection and access together. The acquisition path selects slow access when a BAR2 mapping is unavailable, explicitly supporting bootstrap. Release uses a CPU write barrier followed by BAR flush. [Physical PRAMIN fallback](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/instmem/nv50.c#L57).

**INFERRED:** unknown 6 is substantially narrowed: channel page tables need not already exist to populate them. VRAM readiness, master-control state and memory ownership remain prerequisites. “Before translation” here means before the GPU mappings this path bootstraps, not before the guest CPU maps BAR0. Do not assume a window selector cached before reset is still valid afterward; re-establish it and serialize all users.

## 7. Reset state and collateral effects

**KNOWN / SOURCE_ONLY:** Linux exposes the supported/enabled function-reset methods and ordering through `reset_method` where available. Its presence does not describe the resulting GPU memory or board-controller state. [PCI sysfs ABI](https://github.com/torvalds/linux/blob/v6.8/Documentation/ABI/testing/sysfs-bus-pci#L139).

VFIO hot-reset code explicitly notes that bus reset affects all devices on the bus and checks the affected device set. Reset scope and IOMMU-group isolation are different properties. [VFIO reset implementation](https://github.com/torvalds/linux/blob/v6.8/drivers/vfio/pci/vfio_pci_core.c#L2408).

**UNKNOWN:** your host's actual topology, available reset method, method selected on start/stop, and which GPU/board state persists. Guest startup alone is not evidence of a known reset state.

**INFERRED:** B4 should retain a host-side record of the reset method, bridge/slot scope, affected functions and reset result. B5 should compare permitted post-reset observations across repeated starts. Separate cold host boot, reset after Linux Nouveau use and reset after a failed experiment; matching one path does not certify the others. Do not clear all master-control bits to manufacture a reset: the selected MC table has shared/subdevice-specific enable mappings, and reset handling also uses TOP information. [GK104 MC mapping](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/mc/gk104.c).

## 8. Page size and visibility operations

**KNOWN / SOURCE_ONLY:** GK110 framebuffer selects `default_bigpage = 17` (128 KiB), with `NvFbBigPage` as an override. Shared framebuffer setup sets bit 0 of `0x100c80` for 64 KiB and clears it for 128 KiB; its host flush-page address is programmed at `0x100c10` in 256-byte units. [GK110 framebuffer](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/fb/gk110.c#L59), [Framebuffer helpers](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/fb/gf100.c#L68).

Both selected GK104 VMM variants support 4-KiB small pages, but their directory geometry differs: small-table index width is 15 bits in 128-KiB mode and 14 in 64-KiB mode. Using only 4-KiB pages does not remove the global mode decision. [GK104 VMM descriptors](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/mmu/vmmgk104.c#L39).

The selected BAR implementation uses `g84_bar_flush`: trigger at `0x070000`, then bounded polling of bit 1. [BAR selection](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/bar/gf100.c#L178), [BAR flush](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/bar/g84.c#L28).

Translation invalidation uses `0x100cb8/0x100cbc` with status at `0x100c80`. The source identifies its second wait only tentatively as flush queued; do not rename it proven completion. The request includes the page-directory target/address and uses a BAR-specific HUB_ONLY flag where selected. [VMM invalidation](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/mmu/vmmgf100.c#L181).

**INFERRED:** adopt the reference's 128-KiB global mode unless capture/configuration establishes otherwise; use uncompressed 4-KiB mappings for initial objects where the selected path permits them. Preserve separate operations for CPU publication, instance/BAR write visibility, translation invalidation and submission notification. Check every timeout explicitly, even where the Linux helper has no returned error. This is a dependency outline, not an executable register sequence or evidence that an LTC/cache prerequisite can be omitted.

## 9. Channel control block: addresses and opaque words

The source establishes the following fields without borrowing any Linux allocation's address:

| Instance/RAMFC offset | Meaning or required provenance |
|---|---|
| `0x08/0x0c` | USERD backing-memory address plus channel offset; separate from the global USERD BAR1 mapping |
| `0x48/0x4c` | GPFIFO GPU address and log2(entry count), where count = byte length / 8 |
| `0xe4`, `0xe8` | Selected privilege flag and allocated channel ID |
| `0x200`, `0x208` | Page-directory address/target attributes and GPU virtual limit minus one |

[RAMFC writes](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/gk104.c#L77), [VMM attachment](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/mmu/vmmgf100.c#L342).

**KNOWN / SOURCE_ONLY:** Nouveau allocates USERD storage and maps it into the BAR1 GPU address space. Its global FIFO USERD-base register and RAMFC USERD address therefore refer to different domains. C2 must include that mapping even if CPU access uses PRAMIN. [USERD allocation/mapping](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/base.c#L305).

**INFERRED from envytools names:** `0x10` is the signature; `0x30` semaphore configuration; `0x84` initial DMA parser state; `0x94` SLI/subdevice selection; `0x9c` feature enable. Several fields remain explicitly unknown or have older-chip variant restrictions. `0xac`, `0xb8`, `0xf8` and `0xfc` should retain exact chip-path provenance rather than invented names. In particular, the `devm` value at `0x94` is not established here as a GR-engine scheduling mask. [Envytools FIFO/PBDMA definitions](https://github.com/envytools/envytools/blob/master/rnndb/fifo/gf100_pfifo.xml).

**INFERRED:** fixed opaque defaults need not block S1 if preserved from the selected implementation and validated. Treat dynamic addresses, limits, IDs and target flags differently: derive them from your allocations, range-check before shifting, reject overlap, and verify encoded readback. Do not use later-generation NVIDIA RAMFC manuals as proof of GK110 bit layouts.

## 10. Reproducible version comparison

**KNOWN / SOURCE_ONLY:** 31 complete Nouveau file pairs were fetched from upstream v6.8 and v6.12. **28 are byte-identical.** The three changed files are:

| File | Observed difference relevant to this research |
|---|---|
| `subdev/instmem/nv50.c` | v6.12 adds acquire/release CPU barriers around publishing/reusing mapped accessors; slow-window and release-flush code are unchanged |
| `subdev/bios/init.c` | Only block-comment edits; text outside block comments is identical |
| `engine/device/base.c` | Whole file changed; the GK110B selection table and device-preinit function are byte-identical |

This includes the selected FIFO, BAR, framebuffer, VMM, MC and TOP files listed by the verifier. It does **not** establish that Ubuntu `6.8.0-146` has no downstream changes, that every helper was compared, or that your pinned 6.12 checkout equals upstream v6.12. Three requested v6.12 helper fetches were rate-limited; two incorrect exploratory paths returned 404. These failures are recorded rather than counted as comparisons.

Run from this report's directory:

```sh
python3 research-evidence-s1/verify_sources.py
```

The verifier reads only local files, checks all 76 successful source hashes, prints the 31 comparisons and checks the narrower changed-file conclusions. Retain the actual Ubuntu source-package version/build identity, QEMU machine/version and Haiku build revision next to future captures. For S1, rely on these versioned paths rather than carrying newer GR research into the recipe.

## 11. Haiku mapping of card regions

**KNOWN / SOURCE_ONLY:** Haiku's mapping interface takes `phys_addr_t` for physical addresses. The kernel implementation creates a device cache, page-aligns the region and defaults to uncached access unless overridden. Allocation/mapping can fail and must be checked. [Haiku physical mapping implementation](https://github.com/haiku/haiku/blob/master/src/system/kernel/vm/vm.cpp#L1936).

**INFERRED:** B3/B5 should initially map only required BAR spans in the chosen 64-bit image. Keep 64-bit BAR addresses and sizes intact and distinguish PCI BAR register indices from Nouveau's logical labels: the inspected instance-memory fast path calls logical BAR2 through PCI resource index 3. A successful CPU mapping does not prove that the GPU's BAR translation has been initialised or that the aperture covers all VRAM.

The BAR0 slow window gives an S1 bootstrap route without mapping the card's entire physical VRAM capacity. BAR1 USERD mapping still belongs in C2. Read-only-stage access must use permitted registers: mapping a region is not permission to read every register, and copied driver initialisation routines may contain writes. Confirm actual guest BAR placement and resource lengths; this source review is not a successful Haiku mapping test.

## Amendments suggested for the plan

1. Add the host flush-page dependency to A4/C2, with DMA address and lifetime supplied by B2 when required before A7.
2. Make A7's independent checks explicit: fault baselines and a bounded owned-scratch test; keep translation and scheduler readiness as later proofs.
3. Make B4 record reset scope separately from IOMMU groups and preserve the actual method/result per run.
4. Fix the global big-page mode and all address domains in C2, including USERD's BAR1 mapping; list each publication/flush/invalidation separately.
5. Require C3 teardown to prove channel quiescence and removal, not just GET == PUT. Nouveau removes/preempts and updates the runlist with waits. A timeout must not be followed by freeing buffers the card might still access. [Channel removal](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/chan.c#L182), [Runlist waits](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/engine/fifo/runl.c#L249).
6. Include the source manifest and verifier in housekeeping. The actual ROM, board-target classification and raw trace correlation remain the next essential evidence for A2–A5.

The plan remains credible for S1. The research resolves several specification choices and exposes prerequisites; it does not close the hardware-dependent gates or justify removing the reviewed-experiment stages.
