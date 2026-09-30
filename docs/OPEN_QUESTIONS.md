# Open questions

| ID | Question | Status | Evidence so far | Needed to close |
|---|---|---|---|---|
| Q1 | Which Nouveau chipset entry does this K40c use? | INFERRED: `nvf1_chipset` (GK110B) | lspci reports GK180GL, 10de:1024 (`reference/pci/lspci-nn.txt`). Nouveau selects the chipset from PMC_BOOT_0, not from the PCI ID. | Read PMC_BOOT_0 (BAR0 offset 0x0). Needs root and a GPU with no model loaded. |
