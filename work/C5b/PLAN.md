# Plan: C5b — Summary of the register trace of the reference run

## Steps

1. **Parse bars & maps** — Parse PCIDEV (10de1024) for BARs, MAP/UNMAP for mappings.
2. **Parse marks & phases** — Detect MARK lines to split trace into load/job/after; count accesses per BAR per phase.
3. **Parse registers & runs** — For job-phase BAR 0 accesses, look up register names, build job_registers (sorted by offset), build job_runs (consecutive same-domain sequences).
4. **Write JSON** — `analysis/linux_run_trace.json` with all keys: trace, lines, bars, maps, marks, phases, job_registers, job_runs.
5. **Write Markdown** — `analysis/linux_run_trace.md` with 5 sections: Mappings, Phases, Domains of the job, Timeline of the job, Registers without a name.
6. **Implement --check** — Regenerate both files and diff against existing. Exit 0 when identical.
7. **Test** — Run `make check` (check_repo.py validates against its own reference implementation).

## Checks
- check_repo.py reference implementation (`c5b_build`) must match exactly.
- `--check` passes twice.
- Markdown tables have one row per mapping / run.
