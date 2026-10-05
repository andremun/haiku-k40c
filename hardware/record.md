# Hardware Record — Tesla K40c ×2

## GPU 0000:04:00.0

| Field | Value | Source |
|-------|-------|--------|
| PCI ID | 0x10de1024 | `reference/pci/sysfs-04_00_0.txt` vendor=0x10de device=0x1024 |
| Subsystem ID | 0x10de0983 | `reference/pci/lspci-04_00_0.txt` (rev a1) |
| Revision | 0xa1 | `reference/pci/sysfs-04_00_0.txt` revision=0xa1 |
| BAR0 | 0xe6000000 / 16M | `reference/pci/resource-04_00_0.txt` line 1 |
| BAR1 | 0x20fe0000000 / 256M | `reference/pci/resource-04_00_0.txt` line 2 |
| BAR3 | 0x20ff0000000 / 32M | `reference/pci/resource-04_00_0.txt` line 4 |
| NUMA node | 0 | `reference/pci/sysfs-04_00_0.txt` numa_node=0 |
| VBIOS | 80.80.65.00.01 | `reference/pci/nvidia-smi-q.txt` Board Logo |
| VRAM | 12288 MiB | `reference/pci/nvidia-smi-q.txt` |
| Link speed | 8.0 GT/s PCIe | `reference/pci/lspci-04_00_0.txt` |
| Link width | x16 | `reference/pci/lspci-04_00_0.txt` |
| Nouveau chipset | `nvf1_chipset` (GK110B) | PMC_BOOT_0=0x0f1240a1; bits[28:20]=0x0f1; `reference/nouveau/nvkm/engine/device/base.c:3218` |

## GPU 0000:81:00.0

| Field | Value | Source |
|-------|-------|--------|
| PCI ID | 0x10de1024 | `reference/pci/sysfs-81_00_0.txt` vendor=0x10de device=0x1024 |
| Subsystem ID | 0x10de0983 | `reference/pci/lspci-81_00_0.txt` (rev a1) |
| Revision | 0xa1 | `reference/pci/sysfs-81_00_0.txt` revision=0xa1 |
| BAR0 | 0xfa000000 / 16M | `reference/pci/resource-81_00_0.txt` line 1 |
| BAR1 | 0x21fe0000000 / 256M | `reference/pci/resource-81_00_0.txt` line 2 |
| BAR3 | 0x21ff0000000 / 32M | `reference/pci/resource-81_00_0.txt` line 4 |
| NUMA node | 1 | `reference/pci/sysfs-81_00_0.txt` numa_node=1 |
| VBIOS | 80.80.65.00.01 | `reference/pci/nvidia-smi-q.txt` Board Logo (both GPUs) |
| VRAM | 12288 MiB | `reference/pci/nvidia-smi-q.txt` |
| Link speed | 8.0 GT/s PCIe | `reference/pci/lspci-81_00_0.txt` |
| Link width | x16 | `reference/pci/lspci-81_00_0.txt` |
| Nouveau chipset | `nvf1_chipset` (GK110B) | INFERRED — same PCI ID and VBIOS as 04:00.0; PMC_BOOT_0 not read (Q1) |

## Open Questions

- **Q1**: PMC_BOOT_0 read for 04:00.0 only. 81:00.0 chipset status is INFERRED, not KNOWN.
- **Q2**: BAR2 (0x1000000 at 0xe7000000 / 0xfb000000) present in `resource-*` but not in PCI config space decode — likely unassigned or MMIO for auxiliary functionality. Not included in `record.json` per Task A1 scope (BAR0–BAR1 used for core + memory).

## Notes

- BAR flags decoded: `0x00040200` = BAR0 = I/O + 32-bit + prefetchable; `0x0014220c` = BAR1 = 64-bit + prefetchable (bits 63-32 = `0x20fe0000` for GPU 0, `0x21fe0000` for GPU 1).
- GPUs are on different NUMA nodes (04:00.0 → node 0, 81:00.0 → node 1) — quad-socket Xeon with PCIe slots distributed across nodes.
