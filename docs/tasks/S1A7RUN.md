# S1A7RUN: one approved unchanged A7 run

Direct user approval on 2026-10-28 covers one launch of the reviewed 8974695
package. Run build.py --check, run.py --host-check, then
run.py --run-approved-A7-once, in that order. No source changes before launch.
Never remove the consumed marker. Any launcher stop ends this approval.

Preserve the run under results/20261028-a7-post/, including command, exact
hashes, serial and observer logs, filtered kernel delta, target arming/readback,
readiness results and host PCI bus-master state after owned guest exit.
Label unavailable results UNKNOWN or NOT_REACHED. A7 success is not S1 success.

Update STATUS and write work/S1A7RUN/{PLAN,FINDINGS,RESULT}.md. Keep RESULT under
40 lines. Run make check and commit this evidence separately on main. No push.
Then address the four supplied review nits as a new host-only package task.
A second A7 run or D1 requires fresh explicit approval.
