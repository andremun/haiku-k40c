# User approval and limit (2026-10-28)

The user relayed Claude Code's review and directly supplied this approval:
"I approve one A7 run of the current package
(tools/a7/run.py --run-approved-A7-once), as reviewed. Nits can follow afterwards."

Scope: unchanged commit 8974695, with owner faef759d..., stage 48ea12e8...,
identity 8c45ec7b..., observer 75b7aeed..., kernel 2da9a5b9... and ROM aecb0b5f....
The exact hashes are in the captured approved-package.json. build.py --check
and run.py --host-check had to pass first. R5 had to remain live.

Approval covers exactly one launch, including a failed launch. It covers no
retry, parser workaround, D1 or other write stage. Keep the consumed marker.
The user requests evidence, status/task records, then the four host-only nits
in a new package. Those nits were provided separately after the launch began.
