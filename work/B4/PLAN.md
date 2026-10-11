# Plan for Task B4: Linux dependency map

## Steps
1. Write `tools/linux_deps.py`:
   a. Read `analysis/files.json`, filter non-other-chip (70 files).
   b. For each file, strip comments, find calls matching `([A-Za-z_]\w*)\s*\(`.
   c. Drop C keywords (B4_KW) and Nouveau-defined names (from all .c/.h).
   d. Produce `linux_deps.json`: list of {symbol, count, example, category, haiku_api, header, note}.
   e. `--check` mode: compare generated JSON with existing file.
2. First run: get raw symbol counts, verify we get ~139 symbols.
3. Fill the classification table: memory (C), locks (C), lists (C),
   timing (C), firmware/DMA (C), atomic/macro (A), unnecessary (D),
   non-Linux (X).
4. Run `make check`, fix failures.
5. Write `analysis/linux_deps.md` (30+ lines, grouped by category).

## Checks
- `make check` validates 139 symbols, categories, haiku_api, headers, notes.
- Specific checks for kzalloc, mutex_lock, spin_lock_irqsave, msleep, etc.
