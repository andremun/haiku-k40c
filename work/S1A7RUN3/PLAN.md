# One approved run of package 0390b8b

The user replied "aproval is given" to the explicit request for one run of the
corrected package. This authorizes exactly one launch, no D1 or later retry.
Unchanged build.py --check and run.py --host-check passed. The guarded launch
has started. No approved source or artifact was changed before or during it.

1. Let the unchanged launcher enforce one guest, R5, observer and deadline gates.
2. Preserve the outcome, raw logs, exact hashes, target/POST/readiness events,
   filtered kernel delta and end-of-guest bus-master observation.
3. Keep all three consumed markers and previous raw evidence. Never retry.
4. If this is another failure of the same pre-grant problem, apply the repository
   three-attempt escalation rule. Do not prepare an unreviewed fourth attempt.
5. Update status/task/result, run make check and commit this run separately.
   A7 success is not S1 success. Any further write stage needs explicit approval.
