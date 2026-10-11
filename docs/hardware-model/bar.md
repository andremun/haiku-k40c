# bar: Hardware Model

## Purpose
BAR1 and BAR2 address-space setup: initialises both BAR regions by writing base addresses to MMIO 0x1704 (BAR1) and 0x1714 (BAR2), manages VMM partitions for each region, and flushes pending BAR writes via MMIO 0x070000.

## Nouveau files

- Constructor: **gf100_bar_new** (`nvkm/subdev/bar/gf100.c:192`)
- Function table: **gf100_bar_func** (`nvkm/subdev/bar/gf100.c:177`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| dtor | gf100_bar_dtor | teardown | False | 0 |
| oneinit | gf100_bar_oneinit | init | True | 0 |
| bar1.init | gf100_bar_bar1_init | init | True | 1 |
| bar1.fini | gf100_bar_bar1_fini | teardown | False | 1 |
| bar1.wait | gf100_bar_bar1_wait | runtime | True | 0 |
| bar1.vmm | gf100_bar_bar1_vmm | data | True | 0 |
| bar2.init | gf100_bar_bar2_init | init | True | 1 |
| bar2.fini | gf100_bar_bar2_fini | teardown | False | 1 |
| bar2.wait | gf100_bar_bar1_wait | runtime | True | 0 |
| bar2.vmm | gf100_bar_bar2_vmm | data | True | 0 |
| flush | g84_bar_flush | runtime | True | 2 |

## Dependencies
(none identified)

## KNOWN

- **dtor**: Deallocates VMM partitions and instance memory references for BAR0 and BAR1 regions (`nvkm/subdev/bar/gf100.c:149`)
- **oneinit**: Initialises BAR2 address space then calls bar2.init and sets up BAR1 with lock classification (`nvkm/subdev/bar/gf100.c:123`)
- **bar1.init**: Writes BAR1 instance base address shifted by 12 bits into MMIO 0x1704 with bit 31 set (`nvkm/subdev/bar/gf100.c:52`)
- **bar1.fini**: Clears bit 31 in MMIO 0x1704 to disable BAR1 address space mapping (`nvkm/subdev/bar/gf100.c:46`)
- **bar1.wait**: Calls bar flush twice to wait for pending BAR write operations to complete (`nvkm/subdev/bar/gf100.c:38`)
- **bar1.vmm**: Returns the VMM pointer for BAR1 address space region from the bar structure (`nvkm/subdev/bar/gf100.c:32`)
- **bar2.init**: Writes BAR0 instance base address shifted by 12 bits into MMIO 0x1714 with bit 31 set (`nvkm/subdev/bar/gf100.c:73`)
- **bar2.fini**: Clears bit 31 in MMIO 0x1714 to disable BAR2 address space mapping (`nvkm/subdev/bar/gf100.c:67`)
- **bar2.wait**: Calls bar flush twice to wait for pending BAR write operations to complete (`nvkm/subdev/bar/gf100.c:38`)
- **bar2.vmm**: Returns the VMM pointer for BAR0 address space region from the bar structure (`nvkm/subdev/bar/gf100.c:61`)
- **flush**: Sets MMIO 0x070000 bit 0 then waits up to 2ms for bit 1 to confirm flush completed (`nvkm/subdev/bar/g84.c:29`)

## INFERRED

(none)

## UNKNOWN

(none)
