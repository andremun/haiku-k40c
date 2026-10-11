# ltc: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk104_ltc_new** (`nvkm/subdev/ltc/gk104.c:54`)
- Function table: **gk104_ltc** (`nvkm/subdev/ltc/gk104.c:39`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| oneinit | gf100_ltc_oneinit | None | None | 3 |
| init | gk104_ltc_init | None | None | 5 |
| intr | gf100_ltc_intr | None | None | 1 |
| cbc_clear | gf100_ltc_cbc_clear | None | None | 3 |
| cbc_wait | gf100_ltc_cbc_wait | None | None | 1 |
| zbc_color | 16 | None | None | 0 |
| zbc_depth | 16 | None | None | 0 |
| zbc_clear_color | gf100_ltc_zbc_clear_color | None | None | 5 |
| zbc_clear_depth | gf100_ltc_zbc_clear_depth | None | None | 2 |
| invalidate | gf100_ltc_invalidate | None | None | 1 |
| flush | gf100_ltc_flush | None | None | 1 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
