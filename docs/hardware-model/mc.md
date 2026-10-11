# mc: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk104_mc_new** (`nvkm/subdev/mc/gk104.c:63`)
- Function table: **gk104_mc** (`nvkm/subdev/mc/gk104.c:52`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| init | nv50_mc_init | None | None | 1 |
| intr | gt215_mc_intr | None | None | 0 |
| pending | nv04_mc_intr_pending | None | None | 1 |
| unarm | nv04_mc_intr_unarm | None | None | 2 |
| rearm | nv04_mc_intr_rearm | None | None | 1 |
| block | gt215_mc_intr_block | None | None | 1 |
| allow | gt215_mc_intr_allow | None | None | 1 |
| intrs | gk104_mc_intrs | None | None | 0 |
| intr_nonstall | true | None | None | 0 |
| reset | gk104_mc_reset | None | None | 0 |
| device | nv04_mc_device | None | None | 0 |
| enabled | nv04_mc_device_enabled | None | None | 1 |
| enable | nv04_mc_device_enable | None | None | 2 |
| disable | nv04_mc_device_disable | None | None | 1 |
| unk260 | gf100_mc_unk260 | None | None | 1 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
