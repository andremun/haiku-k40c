# Task C1 Plan: Register database

## Steps
1. Write `tools/build_regdb.py`:
   a. Read `registers/mmio_accesses.json`, group entries by subsystem (fifo→pbdma for 0x40000–0x5FFFF).
   b. For each distinct `reg` text per group, build an entry with: reg, address (hex parse or macro eval or null), name/name_source/fields (from `rnndb.lookup`), width=32, readable/writable (from op), source (sorted file:line list), status="SOURCE_ONLY".
   c. Write `hardware/registers/<group>.yaml` files sorted by `reg`.
   d. Write `hardware/registers/README.md` table + "Not named" section.
   e. `--check` mode: regenerate all, diff against existing files.
2. Start with `mc` group (14 entries) to validate.
3. Run `make check`, fix failures.
4. Generate all 14 files, run `make check` to completion.

## Outputs
- `tools/build_regdb.py` (with --check)
- 14 YAML files in `hardware/registers/`
- `hardware/registers/README.md`

## Checks
- `make check` (C1 section in check_repo.py)
- `tools/build_regdb.py --check` returns 0 on second consecutive run.
