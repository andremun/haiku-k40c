# S1A7RUN7: one user-approved buffered A7 run

The user directly approves the b0c24e4 package: "I approve because this is not a
major change." This is the user's go-ahead for the unchanged package-buffer.
No separate Claude acceptance was supplied. Do not label this as Claude ACCEPT.
Approval is for one launch only, not D1 or a retry after any stop.

Verify build.py --check, review_package.py --check and run.py --host-check.
Match owner 944bdaf424789914a7b8a8b8fe3af272ea1f4d93d387e931d336aa084ce4c087
and manifest a4b47b8a3e8f56d533170b0bccad3e3f037ed03e627b1d16e017248f0b244bdd.
If the reviewed package differs, report and do not launch. No source/binary fixes.
Run python3 tools/a7/run.py --run-approved-A7-once exactly once if ready.
Preserve the consumed marker and all original captures. Do not reset manually.

Record command/hashes, instruction and I2C outcomes, full timing/poll diagnostics,
flush/readback/re-arm, readiness, R5 delta/allowances and end bus-master check.
Label physical results at their scope. Missing steps are UNKNOWN/NOT_REACHED.
A7 success is not S1 success. Write results README, FINDINGS/RESULT (40 lines max),
update STATUS, run make check and commit on main. No push. Report any stop and
never retry this approval, including parser false alarms or already-POSTed state.
