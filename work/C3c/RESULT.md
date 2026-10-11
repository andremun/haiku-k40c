# Result: C3c — Subsystem models, part 3 (fifo)

## Outputs
- `analysis/hwmodel/decisions/fifo.json` — 48 members with roles, certainties, evidence, evidence lines verified against source
- `analysis/hwmodel/fifo.json` — generated JSON with constructor, table, members, accesses
- `docs/hardware-model/fifo.md` — generated Markdown with Purpose, Nouevau files, Members, Dependencies, KNOWN/INFERRED/UNKNOWN sections

## Decisions summary
- **48 members** covered: 15 in the main `gk110_fifo` table + 33 in six sub-tables (mmu_fault 6, nonstall 2, runl 11, runq 4, engn 6, engn_ce 4)
- **Roles**: init (5), interrupt (3), teardown (1), runtime (20), data (19)
- **Needed for compute**: 23 true, 25 false
- **Certainty**: All KNOWN (functions traced to source; value/table members described from their enum definitions)
- **Evidence**: Every function member has a line number inside the function body with a 10+ character quote from that line — all verified against `reference/nouveau/nvkm/engine/fifo/`
- **depends_on**: `["top", "imem"]` — derived from `device->top`, `device->instmem`, and `vctx->vmm` calls seen in functions
- **summary**: 36 words describing the FIFO's role in command dispatch and what Haiku must reproduce

## Key findings
- `runl` is the gk110 variant (8-entry runlist with cgrp support); `runq` uses the gk104 variant
- `engn` and `engn_ce` share the same function implementations (chsw, cxid, mmu_fault_trigger, mmu_fault_triggered)
- `nonstall` is an event table with init/fini — controls bit 31 of 0x002140
- `mmu_fault` sub-table is mostly enum data (access, engine, reason, hubclient, gpcclient) plus the recover function
- FIFO main table references `cgrp` and `chan` which are not covered in this task (those are separate subsystems)

## make check
0 failures.

## Open questions
- `cgrp` and `chan` members of the main table reference `gk110_cgrp` and `gk110_chan` — these may need separate model entries
- The exact hardware meaning of the bit fields in `gk110_runl_insert_cgrp` (128 << 18, 3 << 14) is not documented in source comments
