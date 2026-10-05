# Status

Current phase: A (Ubuntu reference data)
Current task: A2 (root captures)
Last updated: 2026-10-05

## Last result

Task A1 reworked per review findings: fixed source citations (Subsystem ID,
PCI ID, Revision, Link speed/width → correct lspci-vvv and sysfs files),
VRAM corrected to 11441 MiB, VBIOS field name aligned, BAR0 flags corrected,
all BAR2 statements and Q2 removed, "quad-socket" → "dual-socket".
Q1 closed for 04:00.0; 81:00.0 remains INFERRED.
Review: ACCEPT.

## Task log

| Task | Result | Date | Notes |
|---|---|---|---|
| A1 | DONE | 2026-10-05 | `hardware/record.json` + `record.md` for 2 GPUs; reworked 2026-10-05, review ACCEPT |
