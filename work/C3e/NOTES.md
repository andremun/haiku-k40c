# C3e notes

Start: tools/hwmodel.py lists gr; analysis/hwmodel/gr.json is generated (70 members) with no decisions yet.

## Part 1 (2026-10-12)
14 members decided: zbc (3), fecs.ucode (4), gpccs.ucode (4), mmio (1).
- `zbc` (table, INFERRED): container for ZBC clear functions
- `zbc.clear_color` (function, runtime, KNOWN): writes 7 registers to set a clear colour value and trigger it (TRIGGER|WRITE|COLOR)
- `zbc.clear_depth` (function, runtime, KNOWN): writes 4 registers to set a clear depth value and trigger it (TRIGGER|WRITE|DEPTH)
- `fecs.ucode` (table, INFERRED): FECS firmware container
- `fecs.ucode.code.data` / `.size` / `data.data` / `.size` (values, INFERRED): FECS hub firmware blob
- `gpccs.ucode` (table, INFERRED): GPCCS firmware container
- `gpccs.ucode.code.data` / `.size` / `data.data` / `.size` (values, INFERRED): GPCCS GPC firmware blob
- `mmio` (table, INFERRED): init function pointers packed into GR context image for register setup
All 56 remaining members have no decisions yet (expected). `make check` passes for the 14 decided members.

