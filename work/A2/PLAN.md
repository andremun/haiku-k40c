# Task A2: Root captures

## Steps

1. Parse `reference/pci/root/lspci-vvv-04_00_0.txt` and `lspci-vvv-81_00_0.txt` for:
   - `pci_capabilities`: every `Capabilities: [...]` line
   - `interrupt`: Interrupt + MSI lines
   - `link_capability`: LnkCap line
2. Update `hardware/record.json` with three new fields per GPU object.
3. Add a "PCI Capabilities / Interrupt / Link" section per GPU to `hardware/record.md` with source lines. Note LnkSta agreement with existing link field.
4. Update `docs/STATUS.md`: set current task to A2 DONE.
5. Write `work/A2/RESULT.md`.
6. Run `make check`.

## Verification
- `make check` compares capability offsets and IRQ with capture, requires the three fields.
- Offsets: 0x60, 0x68, 0x78, 0x100, 0x128, 0x420, 0x600, 0x900 for both GPUs.
- IRQ: 66 (04:00.0), 67 (81:00.0).
- LnkSta: Speed 8GT/s (ok), Width x16 (ok) -- agrees with existing link field.
