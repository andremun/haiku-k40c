# Task A2: Root captures — RESULT

## Summary
Added `pci_capabilities`, `interrupt`, and `link_capability` fields to both GPU objects in `hardware/record.json` and corresponding sections to `hardware/record.md`.

## Changes

### hardware/record.json
- GPU 0 (04:00.0): added `pci_capabilities` (8 entries, offsets 0x60–0x900), `interrupt` (pin A, IRQ 66, MSI config), `link_capability` (8GT/s, x16, ASPM not supported)
- GPU 1 (81:00.0): same structure, IRQ 67

### hardware/record.md
- Added "PCI Capabilities", "Interrupt", and "Link capability" tables for both GPUs with source line citations to `reference/pci/root/lspci-vvv-*.txt`

## Verification

- LnkCap for both GPUs: Speed 8GT/s, Width x16, ASPM not supported
- LnkSta for both GPUs: Speed 8GT/s (ok), Width x16 (ok) — agrees with existing `link` field
- MSI: enabled, 64-bit, maskable=false, count 1/1 for both GPUs
- 8 capabilities per GPU at identical offsets (expected for same PCI ID)
- All source citations point to exact lines in lspci-vvv captures

## Open questions
- Q1 (PMC_BOOT_0 for 81:00.0) remains — A2 doesn't address it; chipset status stays INFERRED for GPU 1
