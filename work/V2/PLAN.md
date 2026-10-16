# V2: restore pinned verification inputs and reproduce ROM decoding

2026-10-16. User asks what else can be completed from the current plan.

Bounded cardless task: restore the five exact source revisions without changing
reference contents/pins; provision isolated pytest/PyYAML; rerun the full check;
build the pinned independent ROM decoder without sudo if dependencies permit;
reproduce decoding against the verified offline ROM and document warnings.
Do not start the separate A3 reachability task, design hardware register recipes
without their sources, or perform any physical GPU/VM/passthrough actions.

Record commands/revisions/hashes and unsuccessful attempts. If the environment
can be restored, close that gate honestly; do not call full repository acceptance
passed unless make check succeeds. Keep caches and firmware outputs outside Git.
Commit the task handoff locally, never push. No reviewer implementation access,
no subagents, no host drivers/services/sudo.
