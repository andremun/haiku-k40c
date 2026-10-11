# C3b Plan: Subsystem models (timer, privring, ltc)

## Steps
1. **timer** — Read 6 function sources (nv41.c:28, nv04.c:28/43/57/64/72).
   Decide role, needed_for_compute, what, certainty, evidence.
   Write `analysis/hwmodel/decisions/timer.json`, run tool + check.
2. **privring** — Read 3 function sources (gk104.c:100/58). Decide + write.
3. **ltc** — Read 11 function sources (gf100.c:27/56/67/111/126/139,
   gk104.c:27, plus two `value` members). Decide + write.
4. Commit each subsystem; update NOTES.md; commit final status.

## Checks
- `python3 tools/hwmodel.py --check` succeeds
- `make check` has 0 failures
- Role: `intr`→interrupt, `dtor`/`fini`→teardown, `init`→init, etc.
