# chan: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk110_fifo_new** (`nvkm/engine/fifo/gk110.c:128`)
- Function table: **gk110_chan** (`nvkm/engine/fifo/gk110.c:49`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| inst | gf100_chan_inst | None | None | 0 |
| size | 0x1000 | None | None | 0 |
| zero | true | None | None | 0 |
| vmm | true | None | None | 0 |
| userd | gk104_chan_userd | None | None | 0 |
| bar | 1 | None | None | 0 |
| size | 0x200 | None | None | 0 |
| clear | gf100_chan_userd_clear | None | None | 0 |
| ramfc | gk104_chan_ramfc | None | None | 0 |
| write | gk104_chan_ramfc_write | None | None | 0 |
| devm | 0xfff | None | None | 0 |
| priv | true | None | None | 0 |
| bind | gk104_chan_bind | None | None | 1 |
| unbind | gk104_chan_unbind | None | None | 1 |
| start | gk104_chan_start | None | None | 1 |
| stop | gk104_chan_stop | None | None | 1 |
| preempt | gk110_chan_preempt | None | None | 0 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
