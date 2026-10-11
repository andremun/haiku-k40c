# mmu: Hardware Model

## Purpose
Manages the GPU memory management unit: sets the DMA address width to 40 bits, provides PTE page kind lookups via a 256-entry table mapping page attributes to hardware kind codes, and configures VMM and memory structures for address translation.

## Nouveau files

- Constructor: **gk104_mmu_new** (`nvkm/subdev/mmu/gk104.c:38`)
- Function table: **gk104_mmu** (`nvkm/subdev/mmu/gk104.c:28`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| dma_bits | 40 | data | True | 0 |
| kind | gf100_mmu_kind | data | True | 0 |
| kind_sys | true | data | True | 0 |

## Dependencies
(none identified)

## KNOWN

- **dma_bits**: Sets DMA address width to 40 bits for page table address encoding
- **kind**: Returns 256-entry lookup table mapping PTE attributes to hardware page kind codes (`nvkm/subdev/mmu/gf100.c:33`)

## INFERRED

- **kind_sys**: Flags that the kind lookup table is used for system memory page allocation

## UNKNOWN

(none)
