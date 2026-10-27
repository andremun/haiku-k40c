# 005. Use main, review macro tasks, and permit Haiku read-only passthrough

Date: 2026-10-27. Status: accepted (user decision in the pasted context update).

## Decision

Use only main. Commit small working steps after make check passes.
Never create task branches or push. The user pushes.
Keep the rejected A3 attempt only as archive/task-a3. Do not use it.

Claude Code reviews completed macro tasks, such as the B5 launcher or
board-operation policy and helpers. Small fixes need no separate review.
The user requests review at the macro-task handoff.

The user authorizes Haiku read-only stages with only the development card,
0000:04:00.0. Verify vfio-pci binding, sole IOMMU-group membership, and
writable VFIO group access before launch. Only the user changes host binding.
The VFIO reset at VM start is part of this permitted passthrough.
A7 and the first write of each C3 stage still require the user's go-ahead.
ADR 004 retains its ROM and operation restrictions. No further outside review is required.

Never run as root. Never touch 0000:03:00.0, which runs llm-server.
Never pass through the Quadro K600 at 0000:82:00.0.
No manual GPU reset, setpci writes, host BAR access, or host /dev/mem access.
Never run scripts/passthrough.sh. Linux --gpu needs separate approval.
The cardless vm-test.sh command line stays unchanged.

## Consequences

A separate launcher must enforce the B5 stage, one guest at a time,
a disposable disk overlay, incremental logs, and a ten-minute deadline.
A hang or panic ends the task without a modified retry.
Ask before shutting down a running VM. No shutdown is needed when none runs.
Shared Haiku tool changes require a haiku-k40c-llm tool re-pin.
That pin metadata is the sole authorized reference-file update for this task.
All other safety, evidence, licensing, and read-only reference rules remain.
