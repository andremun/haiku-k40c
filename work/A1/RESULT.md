# Task A1 — Hardware record

## What exists

- `hardware/record.json` — structured JSON for both K40c cards
- `hardware/record.md` — human-readable table for both cards

## Check results

- `make check` passes (record.json format validated).
- Check fails only because RESULT.md was missing — now added.

## Known / Inferred / Unknown

| Item | Status | Notes |
|---|---|---|
| PCI IDs, BARs, NUMA nodes, VBIOS, VRAM, link | KNOWN | Direct reads from sysfs, lspci, nvidia-smi |
| 04:00.0 chipset (nvf1_chipset / GK110B) | KNOWN | PMC_BOOT_0 = 0x0f1240a1, bits[28:20]=0x0f1 |
| 81:00.0 chipset | INFERRED | Same PCI ID + VBIOS as 04:00.0; PMC_BOOT_0 not read |
| BAR2 | UNKNOWN | Present in resource-* but not PCI config decode |

## What the next task (A2) needs

- `reference/pci/root/` captures (R2 done: boot0, config space, lspci).
- Task A2 updates record.json/record.md with PCI capabilities, interrupt
  config and link state from these root captures.
