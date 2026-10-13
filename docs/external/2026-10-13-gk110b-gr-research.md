# GK110B GR: further research

Research date: 13 October 2026. Scope: the updated K40c review package, with particular attention to (1) S1 without GR and (2) firmware and context setup for S3.

## Outcome

**S1 has a credible FIFO-only command to test. S3 has an existing open implementation of firmware loading and context generation to study and port.** Neither conclusion establishes that the proposed Haiku driver works on the card.

This investigation closes two documentary gaps in `docs/06-gr-design.md`: where FECS reset is called, and how generated register state becomes a saved context image. It also identifies an important distinction between Nouveau's built-in and external firmware paths.

Evidence labels: **KNOWN / SOURCE_ONLY** means directly visible in the consulted source or specification; **INFERRED** means a proposed consequence; **UNKNOWN** requires additional evidence. No GPU access, driver loading, reset, or hardware experiment was performed. Online Linux sources below are moving `master` references; their line numbers differ from the package's cited source. Pin and compare a complete revision before implementation. This report does not claim equivalence to the package's unavailable pinned tree.

## 1. Can S1 run without GR?

### A concrete host command

**KNOWN / SOURCE_ONLY:** NVIDIA's official `KEPLER_CHANNEL_GPFIFO_B` header, class `0xA16F`, defines `NVA16F_NOP` at byte method address `0x00000008`. This supplies an exact Kepler-B host-method candidate. [NVIDIA Kepler-B FIFO class header](https://github.com/NVIDIA/open-gpu-doc/blob/master/classes/host/cla16f.h).

The envytools hardware documentation explains that methods below `0x100` execute in the FIFO puller; engine methods start at `0x100`. It specifically identifies method `0x08` as a GF100-and-later NOP. The page acknowledges incomplete GF100 documentation, so the exact NVIDIA class header is the stronger authority for this method's existence. [Envytools FIFO puller](https://envytools.readthedocs.io/en/latest/hw/fifo/puller.html).

**INFERRED:** submit one ordinary GPFIFO entry pointing at an eight-byte pushbuffer containing an increasing-method packet for this host NOP. Using the project's packet convention, the derived words are:

```text
0x20010002   # increasing packet, count 1, subchannel 0, method 0x08 / 4
0x00000000   # NOP argument
```

This is a candidate for host-side encoding verification, not a complete card-initialisation recipe. It avoids a compute-class bind and a GR-dispatched method. Prefer this regular entry over importing a special zero-length GPFIFO opcode from another class header.

Nouveau also separates basic channel activation from engine-object/context construction: `nvkm_uchan_init` binds, allows and inserts the channel; engine classes are enumerated separately. This supports the architectural separation, but does not prove scheduling works with GR entirely uninitialised. [Nouveau FIFO channel interface](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/nouveau/nvkm/engine/fifo/uchan.c).

### What remains to prove

**UNKNOWN:** whether the selected GK110B runlist and channel configuration can schedule and consume this packet with GR register initialisation, FECS/GPCCS startup and channel GR-context creation all omitted. A host NOP cannot resolve dependencies in scheduling, engine masks, clocks or power state.

For the eventual authorised S1 experiment, record exactly which GR stages were omitted. Establish an initial GET, publish a different PUT, and require GET to advance to that new value within a timeout, with fault status recorded. Initial GET == PUT is not success. Pointer advancement proves the stated FIFO milestone; it does not prove shader execution or S3 completion.

## 2. What is available for S3 GR startup?

### Firmware is already present in Nouveau

**KNOWN / SOURCE_ONLY:** the GK110B function table selects GK110 FECS and GPCCS microcode, `gf100_gr_fecs_reset`, and the GK110B context generator. It also contains GK110B-specific L1 and SM initialisation tables. Use this exact chip path rather than a generic Kepler recipe. [Nouveau GK110B GR implementation](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/nouveau/nvkm/engine/gr/gk110b.c).

The GK110 implementation associates those controllers with generated `hubgk110.fuc3.h` and `gpcgk110.fuc3.h` code/data arrays. The firmware directory contains the assembly sources and chip wrappers as well. Thus obtaining a proprietary firmware dump or inventing new controller firmware is not a prerequisite for investigating the built-in path. Preserve the applicable copyright and licence notices when incorporating firmware. [GK110 firmware definitions](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/nouveau/nvkm/engine/gr/gk110.c), [Nouveau firmware source directory](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/nouveau/nvkm/engine/gr/fuc).

### Loader and per-channel binding

**KNOWN / SOURCE_ONLY:** `gf100_gr_nofw` selects built-in microcode by setting `gr->firmware` false; it does not mean firmware-free operation. The internal loader uploads controller data/code, installs context-transfer register lists, starts the hub, waits for readiness and obtains the context size.

`gf100_gr_init_csdata` encodes register-address ranges in Falcon DMEM, not register/value initialisation pairs. It groups up to 32 adjacent addresses and encodes a relative address with `(count - 1) << 26`. These transfer lists and the GR initialisation packs have different purposes.

For channel binding, Nouveau copies the generated template and patches the built-in image at offsets `0x00` (MMIO-pair count) and `0x04` (MMIO-list GPU address shifted by eight). External firmware uses a different layout. Template generation is conditional on the absence of `gr->data`, rather than performed for every job. [Nouveau common GR implementation: `gf100_gr_nofw`, `gf100_gr_init_ctxctl_int`, `gf100_gr_init_csdata`, `gf100_gr_chan_bind`](https://codebrowser.dev/linux/linux/drivers/gpu/drm/nouveau/nvkm/engine/gr/gf100.c.html).

### The missing context-save sequence

**KNOWN / SOURCE_ONLY:** `gf100_grctx_generate`, not just `gf100_grctx_generate_main`, supplies the surrounding lifecycle:

1. Force the front end on, call the selected FECS reset, restore automatic power mode and initialise SCC RAM.
2. Allocate/map temporary storage with a `0x80000` reserved prefix; install the context address in instance offsets `0x210/0x214`.
3. For built-in firmware, issue command `1` through `0x409500/0x409504` and wait on `0x409800` bit 31 to make the temporary channel current.
4. Run the selected context-main generator.
5. Clear next-channel-valid at `0x409b04` bit 31, write `0x100` to `0x409000` to emulate a context-switch interrupt, and wait for current-channel-valid at `0x409b00` bit 31 to clear.
6. Copy the saved GPU image into `gr->data`, clear temporary instance pointers and release the mappings.

External firmware instead invokes `gf100_gr_fecs_wfi_golden_save`. That function is not the missing save operation for the built-in path. [Nouveau context generator, especially `gf100_grctx_generate`](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/nouveau/nvkm/engine/gr/ctxgf100.c).

The open hub assembly also exposes its channel and context-transfer command handling, providing a second source for interpreting this protocol. Command numbers belong to the selected firmware implementation and should not be assumed universal. [Nouveau hub firmware assembly](https://github.com/torvalds/linux/blob/master/drivers/gpu/drm/nouveau/nvkm/engine/gr/fuc/hub.fuc).

## Remaining gaps and recommended work

| Gap | Revised assessment | Next evidence needed |
|---|---|---|
| S1 without GR | INFERRED: a suitable host NOP exists | Card result showing advancement with explicitly recorded GR omissions |
| Where FECS reset is called | KNOWN / SOURCE_ONLY: context generation calls it | Verify the chosen pinned revision and capture its ordering |
| How a context image is saved | KNOWN / SOURCE_ONLY: built-in unload sequence is explicit | Context-save completion and image readback on the development card |
| Complete context binary meaning | UNKNOWN; less obstructive because firmware produces the image | Validate size, mapping, save/load and address patches |
| Omitting graphics-labelled hooks | UNKNOWN; names do not demonstrate dispensability | Keep the selected full init path initially; later controlled experiments |
| Power, topology and memory visibility | UNKNOWN for the proposed Haiku implementation | Card-specific topology, bounded polling, mapped buffer and coherency evidence |

Recommended order: pin the source and firmware pair; extract the selected tables; add meaningful host tests for transfer-list encoding and channel-address patches; then prove firmware readiness/context size, template generation, per-channel binding, and finally the add-one kernel with completion and readback. Keep pagepool, bundle, attribute and MMIO-list allocations visible in the appropriate GPU address space. A captured template containing another channel's addresses is not a substitute for this lifecycle.

No full official GK110B GR-bootstrap/context-format manual was found in this research. NVIDIA's public compute class header helps with launch methods, but does not replace engine initialisation or context generation. [NVIDIA Kepler compute class](https://github.com/NVIDIA/open-gpu-doc/blob/master/classes/compute/cla1c0.h).

The feasibility implication is favourable but limited: these gaps are now more clearly bounded source-porting and validation tasks. The previous overall **7/10** judgement remains reasonable; source discovery alone does not warrant treating GR startup as demonstrated.
