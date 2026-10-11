# GK104 Page-Table Encoding (Task D2)

## Address-space geometry

The K40c (GK110B) uses a 40-bit virtual address space split across three
table levels. The layout comes from `vmmgk104.c` (lines 40–51).

```
Virtual address (40 bits)

  [39:27]  [26:17]  [16:0]
   PDE       LPT       SPT
  13 bits   10 bits   12 bits  (page offset)

  13 bits   10 bits   15 bits  (PTE index)

┌──────────┬──────────┬──────────────────┐
│ PDE idx  │ LPT idx  │ SPT idx / offset │
│[27:39]   │[17:26]   │ [0:11] / [12:26] │
└──────────┴──────────┴──────────────────┘

Page-directory: 8192 entries (1 << 13), each covering 128 MiB (1 << 27)
Large-page table: 1024 entries (1 << 10), each covering 128 KiB (1 << 17)
Small-page table: 32768 entries (1 << 15), each covering 4 KiB (1 << 12)
```

## PTE (Page-Table Entry) encoding

Each 64-bit PTE encodes a physical address and mapping attributes:

```
pte = (phys_addr >> 8) | type
```

Source: `vmmgf100.c:32` (`gf100_vmm_pgt_pte`)

### `type` field

| Bits     | Field   | Source                | Values                      |
|----------|---------|-----------------------|-----------------------------|
| 0        | valid   | vmmgf100.c:314        | Always 1                    |
| 1        | priv    | vmmgf100.c:315        | 0 = user, 1 = privileged    |
| 2        | readOnly| vmmgf100.c:316        | 0 = write, 1 = read-only    |
| 32       | vol     | vmmgf100.c:317        | 0 = non-volatile, 1 = vol   |
| 33–35    | aper    | vmmgf100.c:318, 326-332| 0 = VRAM, 2 = HOST, 3 = NCOH |
| 36–43    | kind    | vmmgf100.c:319        | 0–255 (compression tag)     |

### Worked example

Map `phys = 0x7654000` in VRAM with no flags, page shift 12, VA `0x10000`:

```
phys >> 8 = 0x76540
type = 1 | (0 << 33) = 1
pte = 0x76540 | 1 = 0x76541

splitVa(0x10000): pde = 0, lpte = 0, spte = 16
→ pte at index 16 in the small-page table under PDE 0
```

Map `phys = 0x80000000` in HOST with `readOnly=1, vol=1`, page shift 17, at VA `0x40000`
(the page that holds `0x41234`):

```
phys >> 8 = 0x800000
type = 1 | 4 (readOnly) | (1 << 32) (vol) | (2 << 33) (HOST)
     = 0x500000005
pte = 0x800000 | 0x500000005 = 0x500800005

splitVa(0x41234): pde = 0, lpte = 2, spte = 65
→ pte at index 2 in the large-page table under PDE 0
```

## PDE (Page-Directory Entry) encoding

Each 64-bit PDE references up to two page tables (one large, one small)
under the same 128 MiB region:

```
  Upper 32 bits              Lower 32 bits
┌─────────────────────────┬─────────────────────────┐
│ small-page table info   │ large-page table info   │
│ vmmgf100.c:127-138      │ vmmgf100.c:113-125      │
└─────────────────────────┴─────────────────────────┘
```

**Lower 32 bits** (large-page table, `pt[0]`):
- Bit 0–2: `aper` (1 = VRAM, 2 = HOST, 3 = NCOH) — vmmgf100.c:115-119
- Bit 35: HOST extra bit — vmmgf100.c:117
- Bits 8+: `table_addr >> 8` — vmmgf100.c:124

**Upper 32 bits** (small-page table, `pt[1]`):
- Bits 32–34: `aper` (1 = VRAM, 2 = HOST, 3 = NCOH) — vmmgf100.c:129-133
- Bit 34: HOST extra bit — vmmgf100.c:131
- Bits 56+: `table_addr << 24` — vmmgf100.c:138

### Worked example

Large-page table at `0x31000` (VRAM), small-page table at `0x20000` (VRAM):

```
Large (lower): aper=1, addr>>8 = 0x31000>>8 = 0x310
  → lower 32 = 1 | 0x310 = 0x311

Small (upper): aper=1, addr<<24 = 0x20000<<24 = 0x20000000000
  → upper part = 1<<32 | 0x20000000000 = 0x20100000000

PDE = 0x20100000000 | 0x311 = 0x20100000311
```

## Instance-block encoding

At offset `0x200` of the instance block:

```
pdb = target_bits | page_directory_addr
```

- vmmgf100.c:342-359
- HOST target adds the value 2 (bit 1) and bit 2 (VOL): `addr | 6`

At offset `0x208`:

```
limit = vaLimit - 1
```

- vmmgf100.c:360

## AddressSpace model

The `AddressSpace` class simulates the GPU's page-table memory:

- **Page directory**: one zeroed block of 64 KiB (8192 × 8 bytes).
- **Page tables**: allocated on demand when a mapping needs a new entry.
- **map(va, phys, size, pageShift, target, flags)**: walks the range,
  allocates tables, writes encoded PTEs and PDEs.
- **unmap(va, size, pageShift)**: clears PTEs in the affected range.
- **translate(va)**: walks PDE → PTE, decodes the physical address.

## Not covered in this task

| Item | Why not covered | Nouveau function |
|------|----------------|------------------|
| Compression tags (`ctag`) | Not needed for basic compute job buffers | `gf100_vmm_map` (between lines 246–307) |
| Sparse mappings | Only used for partially populated tables | `gf100_vmm_pgd_pde` (line 106+) |
| MMU flush registers | Host-side write after mapping changes | Not in this task |
| Large-page entry with small pages below | When both tables share a PDE, the large-page PTE must encode a pointer to the small-page infrastructure | `gf100_vmm_pgd_pde` (lines 106–143, the case where both `pt[0]` and `pt[1]` are non-null) |
