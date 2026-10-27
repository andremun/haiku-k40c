# Board operations in the card's start-up script

By the scaffold, 2026-10-14 (step A5 of `docs/S1-PLAN.md`). Source: the start-up script as it ran in
`reference/linux-run-debug/dmesg.txt.xz` (line numbers are lines of the
decompressed log), and the card's own board
tables decoded from its firmware image with envytools `nvbios -p gpio,
i2c, extdev` (image: `reference/vbios/README.md`). This is the list that
`docs/S1-PLAN.md` asks for before any change to the safety rules.
The user made the decisions on 2026-10-27 in
[ADR 004](decisions/004-board-operations-and-review.md).
That record defines the permission and its limits.

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

**KNOWN (TRACE_VERIFIED):** On NV50 and later, Nouveau reads and writes
VGA ports through byte-wide card MMIO at `0x601000 + port`
(`reference/nouveau/nvkm/engine/disp/vga.c:27-30,49-52`).
The Linux capture records the port `0x3c3` access and CRTC `0x3f` write
at `reference/linux-run-debug/mmiotrace.txt.xz:45595-45598`.
It records the CRTC `0x85` write at lines 46468-46469.
These accesses reach card registers through MMIO, independently of QEMU
legacy VGA port routing.

**UNKNOWN:** Whether bring-up can succeed without these operations.
The Linux run executed them. It does not establish that omission is safe.
The user allowed decision 4 within the limits of ADR 004.

## Waits

Seven executed `TIME` waits (1 microsecond to 1 millisecond), nine `CONDITION_TIME` polls of card
registers (for example `0x12004c`, `0x00e800`, `0x61000c`, `0x131c20`),
and one skipped `TIME` of 10 milliseconds. `TIME` operands are microseconds, not milliseconds (`nvkm/subdev/bios/init.c:1781-1795`). The polls are of the card's own state; they change
nothing.

## User decisions (2026-10-27)

[ADR 004](decisions/004-board-operations-and-review.md) allows all five
operations as Linux ran them, on the specified ROM image only:

1. GPIO reset at ROM offset `0x89b7`.
2. MAX6649 writes at `0xab8d`.
3. The unidentified I2C device write at `0x862f`.
4. VGA operations at `0x8506`, `0x850b`, and `0x85e8`.
5. The `IO` helper writes and waits at `0x8506`.

ADR 004 lists the exact operands and ROM SHA-256.
Operations skipped by Linux stay denied if our run would execute them.
Other offsets and other ROM images stay denied. A difference stops the executor.
The device at I2C `0x20` remains UNKNOWN. Permission does not establish necessity.

No further outside review is required. Every card stage still requires the
user's go-ahead. The executor hardware gate remains until reviewed integration.

## ABC1 correction: VGA instruction helper effects (2026-10-16)

The earlier inference that legacy VGA accesses can be omitted is not established.
Nouveau's INIT_IO handler has NV50+ MMIO side effects for port 0x3c3/data 1
(`reference/nouveau/nvkm/subdev/bios/init.c:1623-1656`), in addition to
the byte-wide VGA MMIO accesses described above.
The future executor must preserve or justify those helper effects.
The card's 3D controller class does not justify omission.
ADR 004 now permits the observed operation within its stated limits.
The host executor still delegates it to a default-denied board/helper boundary.
Reviewed helper implementation and hardware integration remain necessary.

Register effects of that helper (`init.c:1638-1650`), covered by ADR 004:
`0x000200` bit 30 cleared then set (an engine-enable bit), `0x00e18c`
bit 17 set then cleared, `0x614100` and `0x614900` (display registers)
masked and written three times, two 10 ms waits.
ADR 004 includes these effects as the fifth board-operation decision.
