# Board operations in the card's start-up script

By the scaffold, 2026-10-14 (step A5 of `docs/S1-PLAN.md`). Source: the start-up script as it ran in
`reference/linux-run-debug/dmesg.txt.xz` (line numbers are lines of the
decompressed log), and the card's own board
tables decoded from its firmware image with envytools `nvbios -p gpio,
i2c, extdev` (image: `reference/vbios/README.md`). This is the list that
`docs/S1-PLAN.md` asks for before any change to the safety rules. **No rule
is changed by this document; the decision is the user's.**

## GPIO: one reset of the board's functions

Log line 1145, offset `0x89b7`, instruction `GPIO_NE`, executed. It resets
every GPIO function of the board to its default, except a list of
excluded functions (`nvkm/subdev/bios/init.c:2191`, `init_gpio_ne`; each
reset is `nvkm_gpio_reset`, which on this chip also sets the pin routing).

| Function (board table) | Line | Direction, default | Reset by the script? |
|---|---|---|---|
| `0x04` VID_0 (core voltage select) | 0 | out, 1 | **no** (excluded) |
| `0x05` VID_1 | 1 | out, 0 | **no** |
| `0x06` VID_2 | 2 | out, 0 | **no** |
| `0x1a` VID_3 | 3 | out, 1 | **no** |
| `0x73` VID_4 | 4 | out, 1 | **no** |
| `0x7a` ATX_FORCE_LOW_PWR | 6 | logic, 0 | yes |
| `0x18` MEM_VOLTAGE | 7 | out, 1 | yes |
| `0x34` THERM_ALERT | 9 | in, inverted | yes |
| `0x2e` MEM_VREF | 10 | out, inverted, 1 | yes |
| `0x79` ATX_POWER_LOW | 12 | in, inverted | yes |
| `0x3d` FAN_TACH | 13 | in | yes |
| `0x09` FAN_PWM | 16 | out, inverted, hardware-driven | yes |

Reading: the script deliberately leaves the core-voltage lines alone and
puts the memory-voltage, memory-reference, power and fan lines into their
board defaults. The defaults come from the card's own table; they are the
state the vendor firmware expects at power-on.

A second `GPIO` instruction (line 1187) was skipped.

## I2C: three writes on bus 2

The bus index `0x80` in the script means the board's default bus; the
driver's log shows `i2c: bus 0002`. Addresses below are 7-bit, as the
driver prints them (`init.c:1037` shifts the stored byte right by one).

| Log line | Device (7-bit address) | Register = value | Device, from the board table |
|---|---|---|---|
| 1131 | `0x20` | `0xdd` = `0x03` | **not in the board's device table** (unresolved) |
| 3184 | `0x4c` | `0x19` = `0x73` | MAX6649 temperature sensor (table address `0x98`, 7-bit `0x4c`) |
| 3184 | `0x4c` | `0x0d` = `0x73` | the same sensor |

`0x73` is 115. Register meanings from the Linux driver for this sensor
family (`drivers/hwmon/lm90.c` of v6.12, which handles the MAX6649 as the
`max6646` type): `0x19` is `LM90_REG_REMOTE_CRIT`, the remote critical
(OVERT) limit; `0x0d` is the write address of `LM90_REG_REMOTE_HIGHH`
(read address `0x07`, write address read + 6, `lm90_write_reg_addr`), the
remote high limit. So the script sets both limits of the sensor's remote
channel (the GPU die) to 115 °C. The sensor's own power-on limits were not
looked up. The board table also lists an INA3221 power monitor (table
address `0x80`, 7-bit `0x40`), which the script does not touch. The device
at `0x20` with register `0xdd` is not identified.

## VGA ports and registers

| Log line | Instruction | What |
|---|---|---|
| 1027 | `IO` | VGA port `0x3c3` (video subsystem enable), bit 0 set |
| 1028 | `ZM_CR` | VGA CRTC register `0x3f` = `0x57` |
| 3135 | `ZM_CR` | VGA CRTC register `0x85` = `0xff` |

In the guest these legacy VGA accesses go through QEMU. The K40c is passed
through as a compute device (class 3D controller), without the legacy VGA
ranges, so they most likely reach nothing. Nouveau did them in the guest
and the card came up, so they are not required for the bring-up there.
Not verified.

## Waits

Seven executed `TIME` waits (1 microsecond to 1 millisecond), nine `CONDITION_TIME` polls of card
registers (for example `0x12004c`, `0x00e800`, `0x61000c`, `0x131c20`),
and one skipped `TIME` of 10 milliseconds. `TIME` operands are microseconds, not milliseconds (`nvkm/subdev/bios/init.c:1781-1795`). The polls are of the card's own state; they change
nothing.

## What needs a decision

1. **GPIO reset.** Allow the executor to reset the seven listed functions
   to the board's defaults (memory voltage, memory reference, power, fan),
   as the vendor script does, while the core-voltage lines stay untouched.
2. **The temperature sensor.** Allow the two writes to the MAX6649 at
   `0x4c`: they set the high and the critical limit of the GPU die to
   115 °C, the vendor's values. Without them the sensor keeps its
   power-on limits, which were not looked up.
3. **The unknown device at `0x20`.** Recommendation: do not write to it
   until it is identified. Test first whether the bring-up works without
   this single write.
4. **VGA ports.** Recommendation: leave them out in the guest.

## ABC1 correction: VGA instruction helper effects (2026-10-16)

The earlier inference that legacy VGA accesses can be omitted is not established.
Nouveau's INIT_IO handler has NV50+ MMIO side effects for port 0x3c3/data 1
(`reference/nouveau/nvkm/subdev/bios/init.c:1623-1660`), independently of
legacy port routing through QEMU. The future executor must preserve or justify
those helper effects; it cannot silently drop the operation because the card
is a 3D controller. No extra hardware permission is granted. The host executor
delegates this operation to a default-denied board/helper boundary.

Register effects of that helper (`init.c:1631-1647`), for the decision:
`0x000200` bit 30 cleared then set (an engine-enable bit), `0x00e18c`
bit 17 set then cleared, `0x614100` and `0x614900` (display registers)
masked and written three times, two 10 ms waits. This is a fifth item
to decide, alongside the four above.
