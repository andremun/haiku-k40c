# mc: Hardware Model

## Purpose
Master control: enables GPU interrupts via MMIO register 0x0200, manages interrupt routing and masking per-engine, tracks device engine enablement state, and writes to register 0x0260 for unknown engine control and configuration.

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
| reset | gk104_mc_reset | teardown | False | 0 |
| device | nv04_mc_device | data | False | 0 |
| enabled | nv04_mc_device_enabled | runtime | False | 1 |
| enable | nv04_mc_device_enable | init | True | 2 |
| disable | nv04_mc_device_disable | teardown | False | 1 |
| unk260 | gf100_mc_unk260 | runtime | False | 1 |

## Dependencies
top

## KNOWN

- **init**: Writes 0xffffffff to MMIO 0x0200 to enable all interrupt sources on the GPU (`nvkm/subdev/mc/nv50.c:41`)
- **intr**: Reference to the gt215 interrupt handler table providing pending block allow unarm rearm (`nvkm/subdev/mc/gt215.c:73`)
- **pending**: Reads per-engine interrupt status from MMIO 0x0100 and returns whether any interrupt is pending (`nvkm/subdev/mc/nv04.c:94`)
- **unarm**: Writes 0 to MMIO 0x0140 per engine to disable interrupt auto-rearm then reads to clear (`nvkm/subdev/mc/nv04.c:82`)
- **rearm**: Writes 0x00000001 to MMIO 0x0140 per engine to acknowledge and rearm interrupt status (`nvkm/subdev/mc/nv04.c:72`)
- **block**: Writes zero mask to MMIO 0x0640 per engine leaf to block specified interrupt bits (`nvkm/subdev/mc/gt215.c:65`)
- **allow**: Writes mask to MMIO 0x0640 per engine leaf to allow specified interrupt bits to pass (`nvkm/subdev/mc/gt215.c:57`)
- **intrs**: Array of interrupt mapping data defining engine-to-interrupt routing configuration
- **intr_nonstall**: Flags that non-stall interrupts are enabled for this GPU interrupt controller
- **reset**: Data table of reset register mappings used to reinitialise GPU subsystem registers
- **device**: Reference to the nv04 device management sub-table providing enable disable enabled checks (`nvkm/subdev/mc/nv04.c:55`)
- **enabled**: Reads MMIO 0x0200 and checks if all bits in mask are set to verify engine enablement (`nvkm/subdev/mc/nv04.c:49`)
- **enable**: Sets mask bits in MMIO 0x0200 to enable engine interrupts then reads back the register (`nvkm/subdev/mc/nv04.c:40`)
- **disable**: Clears mask bits in MMIO 0x0200 to disable specified engine interrupt sources (`nvkm/subdev/mc/nv04.c:34`)

## INFERRED

- **unk260**: Writes data to MMIO register 0x0260 for unknown engine control purpose (`nvkm/subdev/mc/gf100.c:62`)

## UNKNOWN

(none)
