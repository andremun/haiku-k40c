# 004. Allow the five board operations; no further outside review

Date: 2026-10-27. Status: accepted (user decision).

## Context

`docs/BOARD-OPERATIONS.md` listed five operations of the card's start-up
script that act on the board or need a decision: the GPIO reset, the
temperature sensor writes, the write to the unknown I²C device `0x20`,
the VGA register writes, and the register side effects of the `IO`
helper. Each needed one answer: allow, omit or stop.

All five ran in the Linux reference run on this card, and the card came
up (KNOWN):

- `reference/linux-run-debug/dmesg.txt.xz`, lines 1027-1028, 1131,
  1145, 3135, 3184. The bracket digit after the offset is the call depth
  and is printed only for an instruction that runs; a blank means
  skipped (`reference/nouveau/nvkm/subdev/bios/init.c:40-44`).
- `reference/linux-run-debug/mmiotrace.txt.xz`, lines 45579-45598 (the
  `IO` helper and its VGA writes) and 46468-46469 (CRTC `0x85`).
- On NV50 and later, the VGA port writes are card register writes at
  `0x601000 + port` (`reference/nouveau/nvkm/engine/disp/vga.c:27-30,49-52`).

The plan also asked for a third, outside review before any card stage.
Two outside reviews were done (`docs/external/`), and the scaffold
reviewed the host code against Nouveau on 2026-10-21.

## Decision

1. **Allow all five operations**, as the vendor script does under
   Nouveau, on this ROM image only (SHA-256
   `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`):

   | ROM offset | Instruction | What |
   |---|---|---|
   | `0x8506` | `IO` | port `0x3c3`, data 1, with Nouveau's helper writes and waits (`init.c:1623-1656`) |
   | `0x850b` | `ZM_CR` | CRTC `0x3f` = `0x57` |
   | `0x862f` | `ZM_I2C_BYTE` | bus `0x80`, device `0x20`, register `0xdd` = `0x03` |
   | `0x89b7` | `GPIO_NE` | reset of the board functions not in its list |
   | `0x85e8` | `ZM_CR` | CRTC `0x85` = `0xff` |
   | `0xab8d` | `ZM_I2C_BYTE` | bus `0x80`, device `0x4c` (MAX6649), registers `0x19`, `0x0d` = `0x73` |

2. **Allow means what Linux did.** An operation that the Linux run
   skipped stays denied if our run would execute it (for example `GPIO`
   at `0x89c2`). A board operation at any other offset, or on another
   ROM image, stays denied. A difference from the Linux run stops the
   executor and is reported.
3. **No further outside review.** The reviews already done are enough.
   Every card stage still needs the user's go-ahead (B5, A7, the first
   write of each C3 stage).

## Consequences

- The executor needs reviewed helper implementations for `IO` (with its
  side effects), `ZM_CR`, `ZM_I2C_BYTE` and `GPIO_NE`, behind a policy
  table that holds exactly the rows above. Default stays deny.
- The device at I²C `0x20` stays UNKNOWN. It is allowed because the
  Linux run wrote it, not because it is identified.
- "Allow" is not evidence that an operation is needed. It is evidence
  that it did no harm once on this card.
- The hardware gate of the executor (it refuses a backend that is not a
  host simulation) stays until a reviewed hardware integration.
- `docs/S1-PLAN.md` and `docs/BOARD-OPERATIONS.md` must say that the
  decisions are made, and cite this record.
