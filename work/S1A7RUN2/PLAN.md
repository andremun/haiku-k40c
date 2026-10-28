# One approved run of package 24fb578

The user replied "aproval is given" to the explicit question asking for one
A7 run of the new package after review. This authorizes one launch only.
The execution sequence is build.py --check, run.py --host-check, then
run.py --run-approved-A7-once. The first two passed and the launch has started.
No approved source or artifact was changed. No D1 or second launch is authorized.

1. Let the unchanged guarded launcher supervise its single guest and deadline.
2. On success or stop, preserve raw logs, source/artifact hashes, the R5 delta,
   target/readiness events and end-of-guest bus-master observation.
3. Keep both consumed markers and all first-attempt evidence. Never retry.
4. Label claims only as supported by this capture. A7 success is not S1 success.
5. Update status/task/result, run make check and commit this run separately.
   Report any stop and request fresh approval before another physical launch.
