# fb: Hardware Model

## Purpose


## Nouveau files

- Constructor: **gk110_fb_new** (`nvkm/subdev/fb/gk110.c:69`)
- Function table: **gk110_fb** (`nvkm/subdev/fb/gk110.c:56`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| dtor | gf100_fb_dtor | None | None | 0 |
| oneinit | gf100_fb_oneinit | None | None | 0 |
| init | gf100_fb_init | None | None | 0 |
| init_page | gf100_fb_init_page | None | None | 2 |
| intr | gf100_fb_intr | None | None | 1 |
| sysmem.flush_page_init | gf100_fb_sysmem_flush_page_init | None | None | 1 |
| ram_new | gk104_ram_new | None | None | 0 |
| default_bigpage | 17 | None | None | 0 |
| clkgate_pack | gk110_fb_clkgate_pack | None | None | 0 |

## Dependencies
(none identified)

## KNOWN

(none)

## INFERRED

(none)

## UNKNOWN

(none)
