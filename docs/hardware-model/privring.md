# privring: Hardware Model

## Purpose
The PRI ring is the register bus inside the GPU that carries register accesses from the hub to the GPC and ROP units of the GR engine (PRI is a register-bus name in the source, not a PCI Express term). gk104_privring_init writes five mask values to registers 0x122318 to 0x122358 and is used both as preinit and as init; the source does not say what the values mean. gk104_privring_intr reads the status registers 0x120058 and 0x12005c and reports the failing address of each hub, ROP or GPC unit. The Haiku driver must repeat the five writes before it touches GR registers.

## Nouveau files

- Constructor: **gk104_privring_new** (`nvkm/subdev/privring/gk104.c:121`)
- Function table: **gk104_privring** (`nvkm/subdev/privring/gk104.c:114`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| preinit | gk104_privring_init | init | True | 7 |
| init | gk104_privring_init | init | True | 7 |
| intr | gk104_privring_intr | interrupt | False | 7 |

## Dependencies
(none identified)

## KNOWN

- **intr**: Reads interrupt status from two registers, dispatches to per-unit handlers for hubs, ROPs and GPCs then waits for synchronization (`nvkm/subdev/privring/gk104.c:58`)

## INFERRED

- **preinit**: Writes five mask values to PRI ring registers 0x122318 to 0x122358; the source does not say what the values mean (`nvkm/subdev/privring/gk104.c:100`)
- **init**: Writes five mask values to PRI ring registers 0x122318 to 0x122358; the source does not say what the values mean (`nvkm/subdev/privring/gk104.c:100`)

## UNKNOWN

(none)
