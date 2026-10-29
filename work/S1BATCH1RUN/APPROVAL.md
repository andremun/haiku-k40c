# Review and approval

Claude's user-supplied review ACCEPTS batch 1 package acb2aca for one card run
once the user gives an explicit yes. Scope: unchanged run7 A7, separate signed
memory grant, gk104 BAR1 only, no BAR2/G2/D1, Q7/Q11 open, requested UC unmeasured.
Claude reports package/rehearsal/checks and current host prerequisites passing.

Codex independently reran build.py --check and run.py --host-check successfully.
Codex then asked: "Do you approve exactly one card launch using
python3 tools/memstage/run.py --run-approved-batch1-once?"
The user replied: "Approved".

This permits one launch of this unchanged package. Any stop requires a new user
decision under ADR 006. No approval for a second run or another write stage.
