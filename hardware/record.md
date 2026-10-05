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

### PCI Capabilities

| Offset | Name | Version | Source |
|--------|------|---------|--------|
| 0x60 | Power Management | 3 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 12: `Capabilities: [60] Power Management version 3` |
| 0x68 | MSI | — | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `Capabilities: [68] MSI: Enable+ Count=1/1 Maskable- 64bit+` |
| 0x78 | Express | 2 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 17: `Capabilities: [78] Express (v2) Endpoint, MSI 00` |
| 0x100 | Virtual Channel | 1 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 44: `Capabilities: [100 v1] Virtual Channel` |
| 0x128 | Power Budgeting | 1 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 53: `Capabilities: [128 v1] Power Budgeting <?>` |
| 0x420 | Advanced Error Reporting | 2 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 54: `Capabilities: [420 v2] Advanced Error Reporting` |
| 0x600 | Vendor Specific Information | 1 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 63: `Capabilities: [600 v1] Vendor Specific Information: ID=0001 Rev=1 Len=024 <?>` |
| 0x900 | Secondary PCI Express | 1 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 64: `Capabilities: [900 v1] Secondary PCI Express` |

### Interrupt

| Field | Value | Source |
|-------|-------|--------|
| Pin | A | `reference/pci/root/lspci-vvv-04_00_0.txt` line 6: `Interrupt: pin A routed to IRQ 66` |
| IRQ | 66 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 6: `routed to IRQ 66` |
| MSI offset | 0x68 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `Capabilities: [68] MSI` |
| MSI enabled | true | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `Enable+` |
| MSI count | 1/1 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `Count=1/1` |
| MSI 64-bit | true | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `64bit+` |
| MSI maskable | false | `reference/pci/root/lspci-vvv-04_00_0.txt` line 15: `Maskable-` |

### Link capability

| Field | Value | Source |
|-------|-------|--------|
| Speed | 8GT/s | `reference/pci/root/lspci-vvv-04_00_0.txt` line 24: `LnkCap: Port #0, Speed 8GT/s` |
| Width | x16 | `reference/pci/root/lspci-vvv-04_00_0.txt` line 24: `Width x16` |
| ASPM | not supported | `reference/pci/root/lspci-vvv-04_00_0.txt` line 24: `ASPM not supported` |
| LnkSta agrees | Speed 8GT/s (ok), Width x16 (ok) | `reference/pci/root/lspci-vvv-04_00_0.txt` line 28: `LnkSta: Speed 8GT/s (ok), Width x16 (ok)` — agrees with existing `link` field (8.0 GT/s PCIe, x16) |

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

### PCI Capabilities

| Offset | Name | Version | Source |
|--------|------|---------|--------|
| 0x60 | Power Management | 3 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 12: `Capabilities: [60] Power Management version 3` |
| 0x68 | MSI | — | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `Capabilities: [68] MSI: Enable+ Count=1/1 Maskable- 64bit+` |
| 0x78 | Express | 2 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 17: `Capabilities: [78] Express (v2) Endpoint, MSI 00` |
| 0x100 | Virtual Channel | 1 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 44: `Capabilities: [100 v1] Virtual Channel` |
| 0x128 | Power Budgeting | 1 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 53: `Capabilities: [128 v1] Power Budgeting <?>` |
| 0x420 | Advanced Error Reporting | 2 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 54: `Capabilities: [420 v2] Advanced Error Reporting` |
| 0x600 | Vendor Specific Information | 1 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 63: `Capabilities: [600 v1] Vendor Specific Information: ID=0001 Rev=1 Len=024 <?>` |
| 0x900 | Secondary PCI Express | 1 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 64: `Capabilities: [900 v1] Secondary PCI Express` |

### Interrupt

| Field | Value | Source |
|-------|-------|--------|
| Pin | A | `reference/pci/root/lspci-vvv-81_00_0.txt` line 6: `Interrupt: pin A routed to IRQ 67` |
| IRQ | 67 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 6: `routed to IRQ 67` |
| MSI offset | 0x68 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `Capabilities: [68] MSI` |
| MSI enabled | true | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `Enable+` |
| MSI count | 1/1 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `Count=1/1` |
| MSI 64-bit | true | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `64bit+` |
| MSI maskable | false | `reference/pci/root/lspci-vvv-81_00_0.txt` line 15: `Maskable-` |

### Link capability

| Field | Value | Source |
|-------|-------|--------|
| Speed | 8GT/s | `reference/pci/root/lspci-vvv-81_00_0.txt` line 24: `LnkCap: Port #0, Speed 8GT/s` |
| Width | x16 | `reference/pci/root/lspci-vvv-81_00_0.txt` line 24: `Width x16` |
| ASPM | not supported | `reference/pci/root/lspci-vvv-81_00_0.txt` line 24: `ASPM not supported` |
| LnkSta agrees | Speed 8GT/s (ok), Width x16 (ok) | `reference/pci/root/lspci-vvv-81_00_0.txt` line 28: `LnkSta: Speed 8GT/s (ok), Width x16 (ok)` — agrees with existing `link` field (8.0 GT/s PCIe, x16) |

## Open Questions

- **Q1**: PMC_BOOT_0 read for 04:00.0 only. 81:00.0 chipset status is INFERRED, not KNOWN.

## Notes

- BAR flags from `resource-*`: BAR0 = `0x00040200` (Memory, 32-bit, non-prefetchable per `lspci-vvv-*.txt` Region 0); BAR1 = `0x0014220c` (64-bit, prefetchable, bits 63-32 = `0x0000020f` for GPU 0, `0x0000021f` for GPU 1).
- GPUs are on different NUMA nodes (04:00.0 → node 0, 81:00.0 → node 1) — dual-socket Xeon with PCIe slots distributed across nodes.
