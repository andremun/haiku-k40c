# S1D0RUN plan

1. Apply the accepted Claude review: home-folder filtered journal stream, path
   override, AER stops, pipe-reader exit test and one-line prerequisite errors.
2. Preserve Claude's review and the amended ADR 008. Read-only D0 is approved.
   Every later write-stage run requires its own explicit user go-ahead.
3. Check the current stream and isolation without root. Require a nonempty boot
   baseline, the full requested filter and no running QEMU guest.
4. Regenerate the stage source record, run host tests and make check. Validate
   the exact stage before the first physical run. Keep publication denied.
5. Run D0 once. Preserve evidence on any stop. Never modify and retry without
   asking under ADR 006. Record the actual observation limits.
6. Update task status/result and commit this task. After a passing D0, prepare
   native POST integration and the A7 package. Do not build D1 before POST.
