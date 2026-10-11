# fb: Hardware Model

## Purpose
Framebuffer subsystem: initialises clock gating via therm, allocates MMU read/write scratch memory, configures page size via MMIO 0x100c80, manages framebuffer interrupts from MMIO 0x0100, flushes page initialisation to MMIO 0x100c10, and creates RAM objects for framebuffer memory.

## Nouveau files

- Constructor: **gk110_fb_new** (`nvkm/subdev/fb/gk110.c:69`)
- Function table: **gk110_fb** (`nvkm/subdev/fb/gk110.c:56`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| dtor | gf100_fb_dtor | teardown | False | 0 |
| oneinit | gf100_fb_oneinit | init | True | 0 |
| init | gf100_fb_init | init | True | 0 |
| init_page | gf100_fb_init_page | init | True | 2 |
| intr | gf100_fb_intr | interrupt | True | 1 |
| sysmem.flush_page_init | gf100_fb_sysmem_flush_page_init | runtime | False | 1 |
| ram_new | gk104_ram_new | init | True | 0 |
| default_bigpage | 17 | data | True | 0 |
| clkgate_pack | gk110_fb_clkgate_pack | data | True | 0 |

## Dependencies
imem

## KNOWN

- **dtor**: Returns the internal gf100_fb struct pointer for cleanup of framebuffer resources (`nvkm/subdev/fb/gf100.c:99`)
- **oneinit**: Allocates MMU read and write scratch memory from instance memory with configurable size (`nvkm/subdev/fb/gf100.c:45`)
- **init**: Initialises clock gating by calling therm clkgate init with the clkgate_pack data table (`nvkm/subdev/fb/gf100.c:87`)
- **init_page**: Configures framebuffer page size by setting or clearing bit 0 of MMIO 0x100c80 for 16 or 17 bit page config (`nvkm/subdev/fb/gf100.c:68`)
- **intr**: Reads MMIO 0x0100 to check framebuffer interrupt flags PFFB and PBFB then logs if set (`nvkm/subdev/fb/gf100.c:32`)
- **sysmem.flush_page_init**: Writes the sysmem flush page address shifted by 8 bits to MMIO 0x100c10 to flush page init (`nvkm/subdev/fb/gf100.c:81`)
- **ram_new**: Initialises RAM sub-functions via gk104_ram_new_ to create framebuffer RAM objects (`nvkm/subdev/fb/ramgk104.c:1713`)
- **default_bigpage**: Sets the default big page size exponent to 17 for framebuffer page allocation
- **clkgate_pack**: Data table of clock gating parameters packed for therm clkgate init function

## INFERRED

(none)

## UNKNOWN

(none)
