# Hardware Record — Tesla K40c ×2

## GPU 0000:04:00.0

| Field | Value | Source |
|-------|-------|--------|
| PCI ID | 0x10de1024 | `reference/pci/lspci-vvv-04_00_0.txt` line 1: `[10de:1024]` |
| Subsystem ID | 0x10de0983 | `reference/pci/lspci-vvv-04_00_0.txt` line 2: `[10de:0983]` |
| Revision | 0xa1 | `reference/pci/lspci-vvv-04_00_0.txt` line 1: `(rev a1)` |
| BAR0 | 0xe6000000 / 16M | `reference/pci/resource-04_00_0.txt` line 1 |
| BAR1 | 0x20fe0000000 / 256M | `reference/pci/resource-04_00_0.txt` line 2 |
| BAR3 | 0x20ff0000000 / 32M | `reference/pci/resource-04_00_0.txt` line 4 |
| NUMA node | 0 | `reference/pci/sysfs-04_00_0.txt` line 1: `numa_node: 0` |
| VBIOS | 80.80.65.00.01 | `reference/pci/nvidia-smi-q.txt` line 247: `VBIOS Version : 80.80.65.00.01` |
| VRAM | 11441 MiB | `reference/pci/nvidia-smi-q.txt` line 300: `Total : 11441 MiB` |
| Link speed | 8.0 GT/s PCIe | `reference/pci/sysfs-04_00_0.txt` line 3: `current_link_speed: 8.0 GT/s PCIe` |
| Link width | x16 | `reference/pci/sysfs-04_00_0.txt` line 4: `current_link_width: 16` |
| Nouveau chipset | `nvf1_chipset` (GK110B) | PMC_BOOT_0=0x0f1240a1; bits[28:20]=0x0f1; `reference/nouveau/nvkm/engine/device/base.c:3218` |

## GPU 0000:81:00.0

| Field | Value | Source |
|-------|-------|--------|
| PCI ID | 0x10de1024 | `reference/pci/lspci-vvv-81_00_0.txt` line 1: `[10de:1024]` |
| Subsystem ID | 0x10de0983 | `reference/pci/lspci-vvv-81_00_0.txt` line 2: `[10de:0983]` |
| Revision | 0xa1 | `reference/pci/lspci-vvv-81_00_0.txt` line 1: `(rev a1)` |
| BAR0 | 0xfa000000 / 16M | `reference/pci/resource-81_00_0.txt` line 1 |
| BAR1 | 0x21fe0000000 / 256M | `reference/pci/resource-81_00_0.txt` line 2 |
| BAR3 | 0x21ff0000000 / 32M | `reference/pci/resource-81_00_0.txt` line 4 |
| NUMA node | 1 | `reference/pci/sysfs-81_00_0.txt` line 1: `numa_node: 1` |
| VBIOS | 80.80.65.00.01 | `reference/pci/nvidia-smi-q.txt` line 438: `VBIOS Version : 80.80.65.00.01` |
| VRAM | 11441 MiB | `reference/pci/nvidia-smi-q.txt` line 491: `Total : 11441 MiB` |
| Link speed | 8.0 GT/s PCIe | `reference/pci/sysfs-81_00_0.txt` line 3: `current_link_speed: 8.0 GT/s PCIe` |
| Link width | x16 | `reference/pci/sysfs-81_00_0.txt` line 4: `current_link_width: 16` |
| Nouveau chipset | `nvf1_chipset` (GK110B) | INFERRED — same PCI ID and VBIOS as 04:00.0; PMC_BOOT_0 not read (Q1) |

## Open Questions

- **Q1**: PMC_BOOT_0 read for 04:00.0 only. 81:00.0 chipset status is INFERRED, not KNOWN.

## Notes

- BAR flags from `resource-*`: BAR0 = `0x00040200` (Memory, 32-bit, non-prefetchable per `lspci-vvv-*.txt` Region 0); BAR1 = `0x0014220c` (64-bit, prefetchable, bits 63-32 = `0x20fe0000` for GPU 0, `0x21fe0000` for GPU 1).
- GPUs are on different NUMA nodes (04:00.0 → node 0, 81:00.0 → node 1) — dual-socket Xeon with PCIe slots distributed across nodes.
