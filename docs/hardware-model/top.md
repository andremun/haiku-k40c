# top: Hardware Model

## Purpose
Parses the device topology table at MMIO offset 0x022700 to build a list of all engines and their instances, identifying each engine type, instance number, address, fault channel, IRQ, runlist, and reset source for the GPU.

## Nouveau files

- Constructor: **gk104_top_new** (`nvkm/subdev/top/gk104.c:117`)
- Function table: **gk104_top** (`nvkm/subdev/top/gk104.c:112`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| parse | gk104_top_parse | init | True | 1 |

## Dependencies
(none identified)

## KNOWN

- **parse**: Reads 64-entry topology table from MMIO to enumerate GPU engines and build per-engine info structs (`nvkm/subdev/top/gk104.c:29`)

## INFERRED

(none)

## UNKNOWN

(none)
