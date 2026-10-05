# Task A1 — Hardware record

## What exists

- `hardware/record.json` — structured JSON for both K40c cards
- `hardware/record.md` — human-readable table for both GPUs

## Check results

- `make check` passes (record.json format validated).
- RESULT.md present.

## Review corrections (applied 2026-10-05)

| Finding | Fix |
|---|---|
| F1: Subsystem ID cited nonexistent `lspci-*.txt` | Changed to `reference/pci/lspci-vvv-04_00_0.txt` lines 1-2 |
| F2: Link speed/width cited `lspci-*.txt` | Changed to `reference/pci/sysfs-*.txt` lines 3-4 |
| F3: PCI ID/Revision cited `sysfs-*.txt` (not present) | Changed to `reference/pci/lspci-vvv-*.txt` lines 1-2 |
| F4: VRAM 12288 MiB | Changed to 11441 MiB per `nvidia-smi-q.txt` Total |
| F5: "VBIOS Version" field name mismatch | Field renamed to "VBIOS Version"; exact line cited |
| F6: BAR0 flags "I/O + 32-bit + prefetchable" wrong | Corrected to "Memory, 32-bit, non-prefetchable" per lspci-vvv Region 0 |
| F7: BAR2 present in record | All BAR2 statements and Q2 removed |
| F8: "quad-socket" | Changed to "dual-socket" |

## Known / Inferred / Unknown

| Item | Status | Notes |
|---|---|---|
| PCI IDs, BARs, NUMA nodes, VBIOS, VRAM, link | KNOWN | Direct reads from sysfs, lspci-vvv, nvidia-smi |
| 04:00.0 chipset (nvf1_chipset / GK110B) | KNOWN | PMC_BOOT_0 = 0x0f1240a1, bits[28:20]=0x0f1 |
| 81:00.0 chipset | INFERRED | Same PCI ID + VBIOS as 04:00.0; PMC_BOOT_0 not read |

## What the next task (A2) needs

- `reference/pci/root/` captures (R2 done: boot0, config space, lspci).
- Task A2 updates record.json/record.md with PCI capabilities, interrupt
  config and link state from these root captures.
