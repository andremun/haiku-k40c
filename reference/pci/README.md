# PCI capture formats

Read this before you decode any file here. Do not re-derive the formats.

| File | Format | Use for |
|---|---|---|
| `resource-*.txt` | sysfs `resource`: one line per resource, `start end flags` (hex). Line N (from 0) is BAR N. All zero = not present. | BAR base, size (`end - start + 1`) and flags. This is the authority. |
| `sysfs-*.txt` | `key: value` lines | `numa_node`, link speed and width, IRQ |
| `lspci-*.txt`, `root/lspci-vvv-*.txt` | lspci text | IDs, capabilities, cross-check of BARs |
| `config-*.hex` | `xxd` dump of the first 64 bytes of config space | cross-check only |
| `root/lspci-xxxx-*.txt` | full 4096-byte config space (lspci hex) | capabilities (task A2) |
| `root/boot0-*.txt` | PMC_BOOT_0 register read | chipset identification |

## `config-*.hex` (xxd)

Bytes are printed in address order. Multi-byte values are little-endian.
BARs are at 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24 (BAR0..BAR5). Offset 0x0C
is not a BAR. A 64-bit BAR uses two slots (low word, then high word), so
the next BAR index is skipped: these cards have BAR0, BAR1 (slots 1+2)
and BAR3 (slots 3+4).

Worked example, `config-04_00_0.hex`, line `00000010:`:

    0000 00e6 | 0c00 00e0 | 0f02 0000 | 0c00 00f0     next line: 0f02 0000
    BAR0        BAR1 low    BAR1 high   BAR3 low                 BAR3 high

- BAR0 = 0xe6000000 (32-bit, non-prefetchable)
- BAR1 = 0x0000020f_e000000c -> base 0x20fe0000000 (low 4 bits 0xc:
  64-bit, prefetchable)
- BAR3 = 0x0000020f_f000000c -> base 0x20ff0000000

This agrees with `resource-04_00_0.txt` and lspci. The captures are
consistent with each other; if a decode disagrees, the decode is wrong.
