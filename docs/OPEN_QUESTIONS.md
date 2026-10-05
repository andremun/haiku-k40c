# Open questions

| ID | Question | Status | Evidence so far | Needed to close |
|---|---|---|---|---|
| Q1 | Which Nouveau chipset entry does this K40c use? | CLOSED 2026-10-05. KNOWN for 0000:04:00.0: `nvf1_chipset` (GK110B). INFERRED for 0000:81:00.0 (same PCI ID and VBIOS, not read). | PMC_BOOT_0 = 0x0f1240a1 (`reference/pci/root/boot0-0000_04_00_0.txt`). Nouveau takes the chipset from bits 28:20 = 0x0f1 (`reference/nouveau/nvkm/engine/device/base.c:3218`, `case 0x0f1` at line 3218). | To make 81:00.0 KNOWN: read PMC_BOOT_0 on that card with no model running on it. |
