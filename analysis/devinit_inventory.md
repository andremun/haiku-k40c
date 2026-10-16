# Observed devinit inventory

## Summary

This is observed execution/listing agreement, not a reachability proof.

Log instructions: 598; executed: 560; skipped: 38.
Listing rows (task definition): 2041; listing offsets absent from log: 1519.

| Script | Offset |
|---|---|
| 0 | 0x8637 |
| 1 | 0x8ee8 |
| 2 | 0x657f |
| 3 | 0xaa1b |
| 4 | 0xaa1c |
| 5 | 0xab8d |
| 6 | 0xac0d |

## Instructions

| Name | Executed | Skipped |
|---|---|---|
| CONDITION | 24 | 1 |
| CONDITION_TIME | 9 | 0 |
| COPY_NV_REG | 7 | 0 |
| COPY_ZM_REG | 3 | 0 |
| DONE | 23 | 0 |
| END_REPEAT | 25 | 0 |
| GPIO | 0 | 1 |
| GPIO_NE | 1 | 0 |
| IO | 1 | 0 |
| MACRO | 10 | 0 |
| NOT | 2 | 2 |
| NV_REG | 151 | 9 |
| RAM_RESTRICT_ZM_REG_GROUP | 60 | 1 |
| REPEAT | 25 | 0 |
| RESET_BEGUN | 1 | 0 |
| RESET_END | 1 | 0 |
| RESUME | 18 | 14 |
| SUB_DIRECT | 15 | 4 |
| TIME | 7 | 1 |
| ZM_CR | 2 | 0 |
| ZM_I2C_BYTE | 2 | 0 |
| ZM_MASK_ADD | 8 | 0 |
| ZM_REG | 141 | 5 |
| ZM_REG_SEQUENCE | 24 | 0 |

## Not in the listing

- `0x00000000`
- `0x0000858c`
- `0x00008e09`
- `0x00008e1f`
- `0x00008e35`
- `0x00008e4b`
- `0x00008e61`
- `0x00008e77`

Offset zero is a synthetic REPEAT trace after END_REPEAT sets the interpreter offset to zero; it is not a ROM instruction at zero (Nouveau bios/init.c:658-677,724-733).
The seven COPY_NV_REG starts are present as byte-only lines; nvbios prints their names at start+16 on the second line of each 22-byte instruction (nvbios/nvbios.c:469-476). They follow RESUME or the preceding register/copy instruction in the log, not a hidden branch or missing script.
The listing-offset count follows the task definition, including numeric table rows and a repeated DONE at 0x657f. It is not a count of reachable bytecode instructions.

## Board operations

| Log line | Offset | Marker | Name | Text | Detail lines |
|---|---|---|---|---|---|
| 1027 | 0x00008506 | `1` | IO | IO  I[0x03c3] &= 0x00 &#124;= 0x01 | 0 |
| 1028 | 0x0000850b | `1` | ZM_CR | ZM_CR C[0x3f] = 0x57 | 0 |
| 1036 | 0x00008708 | `0` | TIME | TIME 0x0001 | 0 |
| 1055 | 0x0000877d | ` ` | TIME | TIME 0x2710 | 0 |
| 1131 | 0x0000862f | `1` | ZM_I2C_BYTE | ZM_I2C_BYTE I2C[0x80][0x20] | 7 |
| 1145 | 0x000089b7 | `0` | GPIO_NE | GPIO_NE | 27 |
| 1187 | 0x000089c2 | ` ` | GPIO | GPIO | 0 |
| 1236 | 0x00008ec8 | `1` | CONDITION_TIME | CONDITION_TIME 0x0b 0xff | 2 |
| 1245 | 0x00008b2f | `0` | CONDITION_TIME | CONDITION_TIME 0x07 0xff | 1 |
| 1248 | 0x00008b33 | `0` | CONDITION_TIME | CONDITION_TIME 0x09 0xff | 1 |
| 1304 | 0x00008c47 | `0` | CONDITION_TIME | CONDITION_TIME 0x08 0xff | 1 |
| 1307 | 0x00008c4b | `0` | CONDITION_TIME | CONDITION_TIME 0x0a 0xff | 1 |
| 1345 | 0x00008588 | `1` | CONDITION_TIME | CONDITION_TIME 0x00 0xff | 1 |
| 1349 | 0x000085a2 | `1` | CONDITION_TIME | CONDITION_TIME 0x01 0xff | 2 |
| 2381 | 0x00009b66 | `0` | CONDITION_TIME | CONDITION_TIME 0x11 0xff | 1 |
| 2392 | 0x00009b9e | `0` | CONDITION_TIME | CONDITION_TIME 0x13 0xff | 1 |
| 2885 | 0x0000a261 | `0` | TIME | TIME 0x0064 | 0 |
| 2890 | 0x0000a288 | `0` | TIME | TIME 0x00c8 | 0 |
| 2956 | 0x0000a335 | `0` | TIME | TIME 0x0014 | 0 |
| 3057 | 0x0000a486 | `0` | TIME | TIME 0x03e8 | 0 |
| 3087 | 0x0000a59a | `0` | TIME | TIME 0x0064 | 0 |
| 3118 | 0x0000a5cd | `0` | TIME | TIME 0x03e8 | 0 |
| 3135 | 0x000085e8 | `1` | ZM_CR | ZM_CR C[0x85] = 0xff | 0 |
| 3184 | 0x0000ab8d | `0` | ZM_I2C_BYTE | ZM_I2C_BYTE I2C[0x80][0x4c] | 14 |

Board-operation occurrence or script origin is not authorization to execute it. See docs/BOARD-OPERATIONS.md.
