# MMU Design (GK110 Address Translation)

## Goal

Configure the GK110 MMU so that the GPU can translate virtual addresses
to physical framebuffer addresses for compute shader buffers — the S1
milestone (MMU ready). Four steps: create the MMU subdevice, build a 256-entry
kind lookup table, set up a 40-bit VMM address space with page-directory
and page-table entries, and write the instance block (PDB and limit) to
instance memory.

## What Nouveau does

1. **MMU constructor** — `gk104_mmu_new` (`nvkm/subdev/mmu/gk104.c:38`) calls
   `nvkm_mmu_new_(&gk104_mmu, device, type, inst, pmmu)` to instantiate the
   MMU subdevice with the GK104 function table.
2. **Function table** — `gk104_mmu` (`nvkm/subdev/mmu/gk104.c:28`) sets
   `.dma_bits = 40`, provides the `.vmm` member (class `NVIF_CLASS_VMM_GF100`
   with constructor `gk104_vmm_new`), and the `.kind` member pointing to
   `gf100_mmu_kind`.
3. **Kind lookup table** — `gf100_mmu_kind` (`nvkm/subdev/mmu/gf100.c:33`)
   returns a 256-entry `u8` array mapping compressed page attributes to
   uncompressed storage-type codes; `*count = ARRAY_SIZE(kind)` (256) and
   `*invalid = 0xff` at line 78–79.
4. **GF100 MMU function table** — `gf100_mmu` (`nvkm/subdev/mmu/gf100.c:82`)
   defines `.dma_bits = 40`, `.vmm` with constructor `gf100_vmm_new`, and
   `.kind` pointing to `gf100_mmu_kind`.
5. **VMM new** — `gf100_vmm_new` (`nvkm/subdev/mmu/vmmgf100.c:370`)
   allocates the VMM structure, sets up page-table descriptors, and
   initializes the address-width fields.
6. **VMM address geometry** — `gk104_vmm_desc_17_12` and
   `gk104_vmm_desc_17_17` (`nvkm/subdev/mmu/vmmgk104.c:40–51`) define
   the 40-bit address layout: PDE (13 bits, 128 MiB), LPT (10 bits,
   128 KiB), SPT (15 bits, 4 KiB).
7. **PTE encoding** — `gf100_vmm_pgt_pte` (`nvkm/subdev/mmu/vmmgf100.c:32`)
   computes `base = (addr >> 8) | map->type` where `addr` is the physical
   address. Each entry is written via `VMM_WO064`.
8. **PTE type fields** — `gf100_vmm_valid` (`nvkm/subdev/mmu/vmmgf100.c:314`)
   sets bit 0 to `BIT(0)` (valid), bit 1 to `(u64)priv << 1` (privileged),
   bit 2 to `(u64)ro << 2` (read-only), bit 32 to `(u64)vol << 32`
   (volatile, HOST only), bit 33 to `(u64)aper << 33` (address space
   target), and bits 36 and up to `(u64)kind << 36` (the storage kind of the memory).
9. **Address-space target** — `gf100_vmm_aper` (`nvkm/subdev/mmu/vmmgf100.c:326`)
   maps `NVKM_MEM_TARGET_VRAM` to 0, `NVKM_MEM_TARGET_HOST` to 2,
   `NVKM_MEM_TARGET_NCOH` to 3.
10. **PDE encoding** — `gf100_vmm_pgd_pde` (`nvkm/subdev/mmu/vmmgf100.c:113`)
    writes one 64-bit entry: for the large-page table a target code in
    bits 0 and 1 (VRAM 1, HOST 2, NCOH 3) or'ed with `addr >> 8`, for the
    small-page table the code shifted to bit 32 or'ed with `addr << 24`;
    a HOST table also sets bit 35 or bit 34. Tested values are in
    `tests/accept/d2_accept.cpp`.
11. **Unmap PTE** — `gf100_vmm_pgt_unmap` (`nvkm/subdev/mmu/vmmgf100.c:94`)
    writes `0ULL` to clear an entry via `VMM_FO064`.
12. **VMM join (instance block)** — `gf100_vmm_join_`
    (`nvkm/subdev/mmu/vmmgf100.c:342`) writes the page-directory address
    to instance offset `0x0200` with target bits (VRAM=0, HOST=2 with
    `BIT_ULL(2)` for VOL), and writes `vmm->limit - 1` to offset `0x0208`
    at line 359.
13. **VMM part (size)** — `gf100_vmm_part` (`nvkm/subdev/mmu/vmmgf100.c:362`)
    fills two 64-bit words at instance offset `0x0200` with zero
    (`nvkm_fo64(inst, 0x0200, 0x00000000, 2)`): it removes the page
    directory address and the limit again.
14. **VMM scratch memory** — `gf100_fb_oneinit`
    (`nvkm/subdev/fb/gf100.c:45`) calls `nvkm_instmem_memory_new` to
    allocate MMU read and write scratch memory from instance memory.
15. **BAR1 init** — `gf100_bar_bar1_init`
    (`nvkm/subdev/bar/gf100.c:52`) writes the BAR1 instance block address
    (shifted right by 12) to MMIO `0x001704` with bit 31 set.
16. **BAR2 init** — `gf100_bar_bar2_init`
    (`nvkm/subdev/bar/gf100.c:73`) writes the BAR2 instance block address
    (shifted right by 12) to MMIO `0x001714` with bit 31 set.
17. **BAR flush** — `g84_bar_flush` (`nvkm/subdev/bar/g84.c:29`) sets bit 0
    of MMIO `0x070000` and waits up to 2ms for bit 1.

## Haiku driver design

1. **Allocate the MMU subdevice** — Create a `Mmu` class that holds the
   kind lookup table (256 bytes) and provides the VMM setup API. The
   constructor stores `dma_bits = 40` (line 38, gk104.c).
2. **Store the kind lookup table** — Copy the 256-entry `u8` array from
   `gf100_mmu_kind` (`nvkm/subdev/mmu/gf100.c:33`) into a `uint8_t kind[256]`
   member. This replaces the static array in the Nouveau source.
3. **Set up the VMM address geometry** — Use the `AddressSpace` class
   (from `src/mmu/PageTable.h`) to model the 40-bit address space with
   PDE (13 bits), LPT (10 bits), and SPT (15 bits). The constants
   `kVaBits`, `kSmallShift`, `kLargeShift`, `kPdeShift` from
   `vmmgk104.c:40–51` are already encoded in `PageTable.h`.
4. **Build page-directory and page-table entries** — Call
   `encodePde()` and `encodePte()` from `PageTable.h` to construct PDEs
   (line 113, vmmgf100.c) and PTEs (line 32, vmmgf100.c) with the
   correct type fields (valid, priv, readOnly, vol, aper, kind) as set
   at line 314–320 of vmmgf100.c.
5. **Map compute buffers** — Use `AddressSpace::map(va, phys, size,
   pageShift, target, flags)` to populate the page tables. For compute
   shader buffers, use target `VRAM` (aper=0) with no flags.
6. **Write the instance block PDB** — Write the page-directory base
   address with target bits (`encodeInstPdb`) to offset `0x200` of the
   instance block. The instance block is GPU memory, not a register:
   how the Haiku driver writes instance memory is in "Not known". Following
   `gf100_vmm_join_` at lines 342–359 of vmmgf100.c.
7. **Write the instance block limit** — Write `vaLimit - 1` to instance
   memory offset `0x208` (`encodeInstLimit`), following line 360
   of vmmgf100.c.
8. **Unmap entries** — Use `AddressSpace::unmap(va, size, pageShift)` to
   clear PTEs by writing `0ULL`, following `gf100_vmm_pgt_unmap` at
   line 94 of vmmgf100.c.
9. **BAR address setup** — Write the BAR1 instance block address
   (shifted right by 12, bit 31 set) to MMIO `0x001704`, and the BAR2
   address to `0x001714` with bit 31 set, using `RegisterIO::write32()`.
   These are from `gf100_bar_bar1_init` (line 52) and
   `gf100_bar_bar2_init` (line 73) of gf100.c.
10. **BAR flush** — After BAR writes, set bit 0 of MMIO `0x070000` and
    poll bit 1 until clear, with a 2ms timeout, following
    `g84_bar_flush` at line 29 of g84.c.
11. **Skip the scratch memory allocation** — `gf100_fb_oneinit`
    (`nvkm/subdev/fb/gf100.c:45`) allocates MMU read/write scratch
    memory from instance memory; for S1 this is not needed for compute.
    It will be addressed in S3 when the GR engine needs scratch buffers.

## Haiku interfaces

1. `` `create_area()` `` — `headers/os/kernel/OS.h`: memory for the
   driver's copies of page tables and other buffers that must be locked
   and have a known physical address (see "Not known" for which memory
   the tables live in).
2. `` `get_memory_map()` `` — `headers/os/drivers/KernelExport.h`: the
   physical address of locked memory, for a mapping with target HOST;
   it replaces `dma_map_page` (`analysis/linux_deps.md`).
3. `` `map_physical_memory()` `` — `headers/os/drivers/KernelExport.h`:
   maps the PCI memory regions of the card (BAR0 for registers, BAR1 and
   BAR2 for GPU memory).
4. `` `malloc()` `` and `` `free()` `` — the kernel heap, for the driver's
   own structures; they replace `kzalloc` and `kfree`.

The functions were checked to exist in the headers. Their use here is a
proposal: no Haiku code has been written or run.

## Host tests

`tests/test_pagetable.cpp` covers the core page-table encoding logic:
`encodePte`, `encodePde`, `splitVa`, `encodeInstPdb`, and
`encodeInstLimit` are each exercised with 31 CHECK assertions.
The `AddressSpace::map`/`unmap`/`translate` methods are tested with
74 CHECK assertions in `d2_accept`. These tests cover PTE/PDE encoding
(formula `(phys >> 8) | type` from line 32 of vmmgf100.c), the
address-space geometry (13/10/15 bit splits from vmmgk104.c:40–51),
and the instance-block PDB/limit encoding (lines 342–360 of vmmgf100.c).
A test for the BAR setup sequence (write 0x001704, 0x001714, flush
0x070000) would need to wrap `RegisterIO` with `MockMMIO` and verify
the access log.

## Not known

- The exact contents of the MMU read and write scratch buffers that
  `gf100_fb_oneinit` allocates from instance memory at
  `nvkm/subdev/fb/gf100.c:45` — their size, purpose, and how the GR
  engine accesses them are not established.
- The MMU flush is not in this design. Nouveau has one:
  `gf100_vmm_invalidate` (`nvkm/subdev/mmu/vmmgf100.c:188`) waits on
  register `0x100c80` and writes `0x100cb8` and `0x100cbc`
  (`hardware/registers/mmu.yaml`). When it must be called (after every
  map and unmap, or only after a change of the directory) was not
  analysed.
- How the Haiku driver writes instance memory and page tables. They are
  GPU memory. Nouveau reaches them through BAR2 or a window in BAR0
  (`docs/hardware-model/imem.md`); the design above does not choose.
- Whether the kind lookup table values (0x00–0xfe) have a fixed mapping
  to hardware compression formats documented in the GK110 PRM, or
  if they are driver-internal tags only. The 256-entry array is fully
  populated in `nvkm/subdev/mmu/gf100.c:33` but the PRM naming is not
  traced.
