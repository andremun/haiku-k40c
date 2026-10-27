# S1 pre-start candidate (host only)

The selected GK110B path is KNOWN from the pinned Nouveau source. The helpers
below are SOURCE_ONLY. They have not run against the card. The Linux debug
capture uses kernel 6.8, while the source pin is 6.12; observed order is supporting
evidence, not proof that every source operation occurred.

## Selected lifecycle

`reference/nouveau/nvkm/engine/device/base.c:1770-1805` selects GF100 devinit,
GK104 private ring/MC/GPIO, GK110 I2C/FB/FIFO, and NV41 timer. There is no selected
GK110 devinit implementation to substitute for GF100.

Construction adds subdevices in layout order (`include/nvkm/core/layout.h`,
`nvkm/core/subdev.c:264`, `nvkm/engine/device/base.c:3301-3339`).
Device preinit first unarms interrupts, calls device preinit, then calls each
subdevice's preinit, and only then runs POST (`engine/device/base.c:2889-2931`).
A preinit callback does not implicitly run oneinit or normal init
(`core/subdev.c:81-118`). TOP parsing and FB memory unlock follow POST.

| Before POST | Selected behavior and source (under reference/nouveau) |
|---|---|
| Interrupts | Two MC leaves are unarmed, followed by a drain read: nvkm/subdev/mc/{base.c:140-141,gk104.c:56,nv04.c:82-90,gt215.c:72-78} |
| Devinit | Read POST-needed bit, then unlock extended CRTC: nvkm/subdev/devinit/{gf100.c:101,base.c:90-110}; nvkm/engine/disp/vga.c:128-142 |
| Private ring | Seven masked settings: nvkm/subdev/privring/gk104.c:98-119 |
| I2C | Initialize pads then buses: nvkm/subdev/i2c/base.c:167-183. Dedicated GF119 pad has no mode callback; bus init writes 7: padgf119.c:42-45,busgf119.c:69,93 |
| FB | Program owned, DMA-mapped host page address shifted by 8: nvkm/subdev/fb/base.c:225-229,281-288; gf100.c:81-84 |
| FIFO | Reset selected FIFO before POST: nvkm/engine/fifo/base.c:328-331; nvkm/subdev/mc/base.c:51-79,gk104.c:28,nv04.c:39-49 |
| POST | GF100 selects nv04 POST, which executes BIOS init roots: nvkm/subdev/devinit/gf100.c:107-116,nv04.c:394-396; nvkm/subdev/bios/init.c:2322-2346 |

The cold FIFO reset uses the fallback MC map because TOP has not been parsed.
This is not a warm-reset recipe. Old NV04 memory-test code is not inherited by
GF100 merely because the POST callback resides in nv04.c.
The Linux debug log (`reference/linux-run-debug/dmesg.txt.xz`) records devinit
at lines 842-843, private ring 844-845, I2C 848-879, FB 892-893, FIFO 920-921,
and init tables at 932. Other logged preinit entries can be no-ops.

## Host implementation and ownership

`src/runtime/PreStart.*` models this cold-only ordering. Both register transports
must identify as host simulations. Identity and ROM policy are callback gates;
there is no physical backend or readiness implementation. A verified, published,
aligned device IOVA is required for the flush page. Its pin survives success and
all later failures until the caller proves quiescence. CPU/GPA addresses cannot
stand in for that IOVA. The S1B2 native default still denies publication.

A caller-owned atomic `OncePerBoot` changes Fresh to Running exactly once and
ends Complete or Failed. Reentrant calls and recreated controllers sharing it
are rejected. The owner must survive driver unload/reload for the entire guest
boot. A static variable inside an unloadable driver does not meet that condition;
S1NATIVE now implements a separate KEEP_LOADED owner candidate and client API
(`docs/NATIVE-OWNER.md`). The S1OWNERTEST cardless load/reload path passes; production executor integration
and physical lifetime proof remain gates before A7. No automatic retry or reset exists.
Each callback must itself be bounded; deadlines are checked around callbacks and
clock rollback fails. Deadline checks cannot interrupt an unbounded backend call.

The register helper covers dedicated NVIO I2C initialization only. The approved
ROM resolves its default bus to dedicated drive 2 (CCB 4.0). Shared pads are
rejected. S1A6 now models dedicated transfer, clock stretching and ACK failures
in `src/devinit/I2c.*`, with explicit initialization and bounded host tests.
Physical integration and bus recovery remain unimplemented. The internal bit
algorithm in i2c/bit.c is conditional on
CONFIG_NOUVEAU_I2C_INTERNAL; the capture's configuration is UNKNOWN. Its timings
must not be presented as trace-verified transport behavior.

## Omissions and gates

This is a candidate subset, not a claim that omitted callbacks are unnecessary.
Later display-encoder scripts in nv50_devinit_init, normal interrupt rearming,
GR, BAR/MMU/FIFO normal init, thermal and power management are not pre-POST
prerequisites established by this controller. The effect of omitting them for
S1 remains UNKNOWN. GPIO policy helpers retain ADR 004's exact-ROM restrictions.
Whole-program script preflight, helper completeness, and independent memory/fault
readiness must pass before any hardware integration. The script marker alone
cannot establish memory readiness.

Preinit writes need explicit write-stage authorization in addition to the six
ROM instruction permissions. A7 also requires native boot-persistent ownership,
verified DMA/IOMMU publication, owned VRAM scratch, bounded physical transports,
fault baselines and a reviewed recovery path. B5's PCI command 0x0007 means bus
mastering was already enabled; its source remains INFERRED. No permission or
DMA safety follows from masking interrupts. No card or VM run is part of S1A4.
