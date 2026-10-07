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
| `nvidia-proc-*.txt` | `/proc/driver/nvidia/gpus/<address>/information` | GPU UUID: identifies a physical card when its address changes |

## Where the files come from

`scripts/capture_user.sh` writes the files in this directory and
`sudo scripts/capture_root.sh` writes `root/`. Both find the NVIDIA cards
themselves. `tools/hardware_record.py` then writes `hardware/record.json`
and `hardware/record.md`.

Current layout (2026-10-07): K40c at 03:00.0 and 04:00.0, both on NUMA
node 0, and the Quadro K600 at 82:00.0 on node 1. Until that date the
cards were at 81:00.0 (K40c, node 1), 04:00.0 (K40c) and 03:00.0 (K600).
The K40c at 04:00.0 did not move (same GPU UUID). Its BAR0 changed from
0xe6000000 to 0xe5000000.

## `config-*.hex` (xxd)

Bytes are printed in address order. Multi-byte values are little-endian.
BARs are at 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24 (BAR0..BAR5). Offset 0x0C
is not a BAR. A 64-bit BAR uses two slots (low word, then high word), so
the next BAR index is skipped: these cards have BAR0, BAR1 (slots 1+2)
and BAR3 (slots 3+4).

Worked example, `config-04_00_0.hex`, line `00000010:`:

    0000 00e5 | 0c00 00e0 | 0f02 0000 | 0c00 00f0     next line: 0f02 0000
    BAR0        BAR1 low    BAR1 high   BAR3 low                 BAR3 high

- BAR0 = 0xe5000000 (32-bit, non-prefetchable)
- BAR1 = 0x0000020f_e000000c -> base 0x20fe0000000 (low 4 bits 0xc:
  64-bit, prefetchable)
- BAR3 = 0x0000020f_f000000c -> base 0x20ff0000000

This agrees with `resource-04_00_0.txt` and lspci. The captures are
consistent with each other; if a decode disagrees, the decode is wrong.
