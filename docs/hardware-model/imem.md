# imem: Hardware Model

## Purpose
Instance memory management: allocates and wraps instance memory objects from physical RAM, suspends and saves object contents to host memory, restores them on resume via BAR2, and manages the instance address space lifetime.

## Nouveau files

- Constructor: **nv50_instmem_new** (`nvkm/subdev/instmem/nv50.c:436`)
- Function table: **nv50_instmem** (`nvkm/subdev/instmem/nv50.c:410`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| dtor | nv50_instmem_dtor | teardown | False | 0 |
| fini | nv50_instmem_fini | teardown | False | 0 |
| suspend | nv04_instmem_suspend | runtime | False | 0 |
| resume | nv04_instmem_resume | runtime | False | 0 |
| memory_new | nv50_instobj_new | init | True | 0 |
| memory_wrap | nv50_instobj_wrap | init | True | 0 |
| zero | false | data | True | 0 |

## Dependencies
bar

## KNOWN

- **dtor**: Returns the internal nv50_instmem struct pointer for cleanup of instance memory resources (`nvkm/subdev/instmem/nv50.c:404`)
- **fini**: Sets the instance memory base address to ~0ULL to invalidate the address space (`nvkm/subdev/instmem/nv50.c:398`)
- **suspend**: Saves instance object contents to host memory for objects marked as preserve (`nvkm/subdev/instmem/nv04.c:177`)
- **resume**: Restores instance objects from host memory then reinitialises BAR2 address space (`nvkm/subdev/instmem/nv04.c:159`)
- **memory_new**: Allocates physical RAM from device then wraps it into an instance memory object (`nvkm/subdev/instmem/nv50.c:377`)
- **memory_wrap**: Allocates nv50_instobj struct then wraps given RAM into it as an instance memory object (`nvkm/subdev/instmem/nv50.c:357`)
- **zero**: Flags whether new instance memory objects should be zeroed on allocation

## INFERRED

(none)

## UNKNOWN

(none)
