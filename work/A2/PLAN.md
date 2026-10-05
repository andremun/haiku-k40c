# Task A2 — Plan

## Task
Fix incorrect BAR1 upper 32-bit note in `hardware/record.md`.

## Steps
1. Verify the resource files for both GPUs to determine correct upper 32 bits.
2. Fix the Notes section in `hardware/record.md`:
   - GPU 0 (04:00.0): `0x0000020fe0000000` → bits 63-32 = `0x0000020f`
   - GPU 1 (81:00.0): `0x0000021fe0000000` → bits 63-32 = `0x0000021f`
3. Update `docs/STATUS.md`: set current task to A2, add review ACCEPT to A1 row.
4. Run `make check`.

## Outputs
- `hardware/record.md` — corrected BAR1 note
- `docs/STATUS.md` — updated task log

## Check
`make check` passes.
