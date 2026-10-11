# privring: Hardware Model

## Purpose
The PCI Express PRI (Processor Requested Invalidate) ring manages the register bus from the PCIe root complex to the GPC and ROP units on the GK110 hub. It configures ring base pointers and size registers for hubs, ROPs, and GPCs during initialization, and handles interrupts from each unit type when they need attention, with a final synchronization wait before returning. The Haiku driver must set up the same ring hardware and service the interrupts to maintain correct address translation.

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

- **preinit**: Writes five mask registers to set the PRI ring base and size for hubs, ROPs, and GPC units (`nvkm/subdev/privring/gk104.c:100`)
- **init**: Writes five mask registers to set the PRI ring base and size for hubs, ROPs, and GPC units (`nvkm/subdev/privring/gk104.c:100`)
- **intr**: Reads interrupt status from two registers, dispatches to per-unit handlers for hubs, ROPs and GPCs then waits for synchronization (`nvkm/subdev/privring/gk104.c:58`)

## INFERRED

(none)

## UNKNOWN

(none)
