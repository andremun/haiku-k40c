# ltc: Hardware Model

## Purpose
The L2 cache (LTC) subsystem manages the L2 cache that sits in front of framebuffer memory on GK110. It counts active L2 partition instances during oneinit by reading hardware IDs, then configures tag RAM base and the number of LTC units during init by writing to MMIO registers 0x17e8d8, 0x17e000 and 0x17e8d4. It handles colour buffer clear (CBC) and depth buffer clear (ZBC) operations used during framebuffer initialization, and provides cache invalidate and flush operations that wait for completion. The Haiku driver must replicate the init sequence, support clear/flush operations and handle LTC interrupts.

## Nouveau files

- Constructor: **gk104_ltc_new** (`nvkm/subdev/ltc/gk104.c:54`)
- Function table: **gk104_ltc** (`nvkm/subdev/ltc/gk104.c:39`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| oneinit | gf100_ltc_oneinit | init | True | 3 |
| init | gk104_ltc_init | init | True | 5 |
| intr | gf100_ltc_intr | interrupt | False | 1 |
| cbc_clear | gf100_ltc_cbc_clear | runtime | True | 3 |
| cbc_wait | gf100_ltc_cbc_wait | runtime | True | 1 |
| zbc_color | 16 | data | False | 0 |
| zbc_depth | 16 | data | False | 0 |
| zbc_clear_color | gf100_ltc_zbc_clear_color | runtime | True | 5 |
| zbc_clear_depth | gf100_ltc_zbc_clear_depth | runtime | True | 2 |
| invalidate | gf100_ltc_invalidate | runtime | True | 1 |
| flush | gf100_ltc_flush | runtime | True | 1 |

## Dependencies
fb

## KNOWN

- **oneinit**: Reads hardware ID registers to count active L2 partitions and slice count then calls tag RAM initialization (`nvkm/subdev/ltc/gf100.c:208`)
- **init**: Writes the number of L2 cache units and tag base address to MMIO registers and configures the LP128 mask bit (`nvkm/subdev/ltc/gk104.c:27`)
- **intr**: Reads the interrupt mask register then iterates over enabled L2 channels and slices calling the per-lane interrupt handler for each (`nvkm/subdev/ltc/gf100.c:111`)
- **cbc_wait**: Polls the clear status register of every L2 cache part and slice until the tag clear has finished (`nvkm/subdev/ltc/gf100.c:40`)
- **zbc_clear_color**: Selects entry i of the colour clear-value table (0x17ea44) and writes its four colour words (`nvkm/subdev/ltc/gf100.c:56`)
- **zbc_clear_depth**: Selects entry i of the depth clear-value table (0x17ea44) and writes its depth word (`nvkm/subdev/ltc/gf100.c:67`)
- **invalidate**: Sets the invalidate bit in register 0x70004 and waits up to 2000 milliseconds for the operation to complete (`nvkm/subdev/ltc/gf100.c:126`)
- **flush**: Sets the flush bit in register 0x70010 and waits up to 2000 milliseconds for the cache flush to complete (`nvkm/subdev/ltc/gf100.c:139`)

## INFERRED

- **cbc_clear**: Writes the start and limit of a range of compression tags (0x17e8cc, 0x17e8d0) and sets the clear command bit; CBC is not expanded in the source (`nvkm/subdev/ltc/gf100.c:31`)
- **zbc_color**: Constant 16: the number of entries in the table of colour clear values (ZBC table)
- **zbc_depth**: Constant 16: the number of entries in the table of depth clear values (ZBC table)

## UNKNOWN

(none)
