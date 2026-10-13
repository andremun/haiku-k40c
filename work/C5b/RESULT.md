# Result: C5b — Summary of the register trace of the reference run

## Outputs
- `tools/trace_summary.py` — parses mmiotrace, writes JSON + Markdown. Single pass, <60 s.
- `analysis/linux_run_trace.json` — structured trace summary.
- `analysis/linux_run_trace.md` — human-readable report with 5 sections.

## Numbers (from JSON)
- Trace lines: 901370
- BARs: 3 (BAR 0: 0xc1000000/0x1000000, BAR 1: 0x800000000/0x10000000, BAR 3: 0x810000000/0x2000000)
- Mappings: 27
- Marks: 2 (MARK compute_test start at line 573420, MARK compute_test end at line 901168)
- Job registers: 1086 (142 unnamed / no rnndb entry)
- Job runs: 509
- Domains in job: 16

### Phase accesses (BAR 0)
- Load: 52 084 reads, 156 004 writes (lines 11–573419)
- Job: 1 648 reads, 5 783 writes (lines 573421–901167)
- After: 122 reads, 80 writes (lines 901169–901370)

## Checks
- `make check`: 0 failures.
- `--check` passes twice.
- `check_repo.py` reference implementation (`c5b_build`) matches exactly.

## Defects found during dev
1. Typo: `miotrace.txt.xz` → `mmiotrace.txt.xz` (file path).
2. Registers without a name section: stripped `0x` prefix with `[2:]`, causing the regex `0x[0-9a-f]{6}\b` in check_repo.py to find 0 matches instead of 142. Fixed by keeping full `"0x%06x"` format.
