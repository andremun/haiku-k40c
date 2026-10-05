# Status

Current phase: A (Ubuntu reference data)
Current task: A2 (root captures) — DONE
Last updated: 2026-10-06

## Last result

Task A2 added `pci_capabilities` (8 capabilities per GPU), `interrupt` (pin A,
IRQ 66/67, MSI config), and `link_capability` (8GT/s, x16, ASPM not supported)
to both GPU objects in record.json; added corresponding sections to record.md
with source lines. LnkSta agrees with existing link field on both GPUs.

## Task log

| Task | Result | Date | Notes |
|---|---|---|---|
| A1 | DONE | 2026-10-05 | `hardware/record.json` + `record.md` for 2 GPUs; reworked 2026-10-05, review ACCEPT |
| A2 | DONE | 2026-10-06 | Added `pci_capabilities`, `interrupt`, `link_capability` to record.json; sections in record.md; LnkSta agrees with link for both GPUs |
