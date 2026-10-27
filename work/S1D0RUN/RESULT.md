# S1D0RUN result: STOPPED

D0 did not pass. One physical read-only attempt ran for 124.63 s and stopped on
`D0 observer: unproved binding process`. No modified retry occurred.

Applied Claude's requested R5 changes: home-folder path and environment override,
AER/PCIe stops, filtered evidence wording, SIGPIPE test and one-line prerequisite
errors. Added immediate detection of full-pattern filter exit and same-inode
output binding. The user approved a real control-entry prefix for the otherwise
empty filtered baseline. Six journal tests and six orchestration tests pass.
Full make check passes in check-final.log. No root command or push was run.

Command: python3 tools/haiku/d0_run.py
Evidence: results/20261028-d0-mapping/. Exact hashes/argv: launch.json.

KNOWN: trace.log:104 records successful MAP_DMA from task 1617915 through
container FD 21. The owned QEMU PID is 1617905. The observer rejects this record.
INFERRED: the second task is a QEMU thread. Shared FD-table lineage is unproved.
The correct fix needs that proof, not acceptance of arbitrary process IDs.

The serial log is empty. No native extent or evidence cutoff was attested.
Publication, physical payload and coherency verification remain false.
The before/after filtered log bytes match. No new filtered line was captured.
This does not establish a clean full kernel log. No QEMU guest remains.

Claude's batch acceptance is preserved in CLAUDE-REVIEW.md. ADR 008 now permits
read-only stages only. Write stages require an explicit yes per run.

Next: prepare a thread/FD-proof correction and reviewed retry package. ADR 006
requires user go-ahead before another guest run. S1 remains incomplete.
