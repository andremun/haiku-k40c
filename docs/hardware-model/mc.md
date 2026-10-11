# mc: Hardware Model

## Purpose
Master control: register 0x000200 holds one enable bit for each engine and subdevice (nv50_mc_init writes 0xffffffff to it, with the source comment 'everything enabled'), registers 0x000100, 0x000140 and 0x000640 report, arm and mask the interrupt of each unit, and register 0x000260 is written 0 and then 1 around the microcode upload of the GR engine (purpose not known). The Haiku driver must enable the units it uses and route their interrupts.

## Nouveau files

- Constructor: **gk104_mc_new** (`nvkm/subdev/mc/gk104.c:63`)
- Function table: **gk104_mc** (`nvkm/subdev/mc/gk104.c:52`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| init | nv50_mc_init | init | True | 1 |
| intr | gt215_mc_intr | data | True | 0 |
| pending | nv04_mc_intr_pending | interrupt | True | 1 |
| unarm | nv04_mc_intr_unarm | interrupt | False | 2 |
| rearm | nv04_mc_intr_rearm | interrupt | True | 1 |
| block | gt215_mc_intr_block | interrupt | False | 1 |
| allow | gt215_mc_intr_allow | interrupt | False | 1 |
| intrs | gk104_mc_intrs | data | True | 0 |
| intr_nonstall | true | data | True | 0 |
| reset | gk104_mc_reset | data | False | 0 |
| device | nv04_mc_device | data | False | 0 |
| enabled | nv04_mc_device_enabled | runtime | False | 1 |
| enable | nv04_mc_device_enable | init | True | 2 |
| disable | nv04_mc_device_disable | teardown | False | 1 |
| unk260 | gf100_mc_unk260 | runtime | True | 1 |

## Dependencies
top

## KNOWN

- **init**: Writes 0xffffffff to register 0x000200, the enable bits of all engines and subdevices (`nvkm/subdev/mc/nv50.c:41`)
- **intr**: Reference to the gt215 interrupt handler table providing pending block allow unarm rearm (`nvkm/subdev/mc/gt215.c:73`)
- **pending**: Reads per-engine interrupt status from MMIO 0x0100 and returns whether any interrupt is pending (`nvkm/subdev/mc/nv04.c:94`)
- **unarm**: Writes 0 to MMIO 0x0140 per engine to disable interrupt auto-rearm then reads to clear (`nvkm/subdev/mc/nv04.c:82`)
- **rearm**: Writes 0x00000001 to MMIO 0x0140 per engine to acknowledge and rearm interrupt status (`nvkm/subdev/mc/nv04.c:72`)
- **block**: Writes zero mask to MMIO 0x0640 per engine leaf to block specified interrupt bits (`nvkm/subdev/mc/gt215.c:65`)
- **allow**: Writes mask to MMIO 0x0640 per engine leaf to allow specified interrupt bits to pass (`nvkm/subdev/mc/gt215.c:57`)
- **device**: Reference to the nv04 device management sub-table providing enable disable enabled checks (`nvkm/subdev/mc/nv04.c:55`)
- **enabled**: Reads register 0x000200 and checks that the enable bits of one engine or subdevice are set (`nvkm/subdev/mc/nv04.c:49`)
- **enable**: Sets the mask bits in register 0x000200 to enable one engine or subdevice, then reads the register back (`nvkm/subdev/mc/nv04.c:40`)
- **disable**: Clears the mask bits in register 0x000200 to disable one engine or subdevice (`nvkm/subdev/mc/nv04.c:34`)

## INFERRED

- **intrs**: Array of interrupt mapping data defining engine-to-interrupt routing configuration
- **intr_nonstall**: Flags that non-stall interrupts are enabled for this GPU interrupt controller
- **reset**: Data table of reset register mappings used to reinitialise GPU subsystem registers
- **unk260**: Writes data to register 0x000260; the GR engine calls it with 0 before and 1 after the microcode upload (purpose not known) (`nvkm/subdev/mc/gf100.c:62`)

## UNKNOWN

(none)
