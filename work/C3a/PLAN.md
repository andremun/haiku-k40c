# Plan: C3a — Subsystem models (mc, bar, imem, mmu, fb, top)

## Steps

1. Write `tools/hwmodel.py` with structural extraction only (no decisions filled).
   - Parse Nouveau source: function definitions, table definitions.
   - For each of 6 subsystems: find constructor, function table, members.
   - Output `analysis/hwmodel/<sub>.json` with constructor, table, members, accesses.
   - Output `docs/hardware-model/<sub>.md` skeleton.
2. Run `make check`: verify member lists match (structural check only).
3. Fill decisions: role, needed_for_compute, what, certainty, evidence for each member.
   - Do top and mmu first (small: 1 and 3 members), then mc, imem, bar, fb.
4. Run `make check` after each subsystem to catch errors early.
5. Final `make check` pass. Update STATUS.md, write RESULT.md.

## Outputs
- `tools/hwmodel.py` (tool with `--check` mode)
- `analysis/hwmodel/{mc,bar,imem,mmu,fb,top}.json`
- `docs/hardware-model/{mc,bar,imem,mmu,fb,top}.md`
