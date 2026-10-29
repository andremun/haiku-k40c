# Findings

KNOWN / SOURCE_ONLY: selected Nouveau handlers read MC, FIFO aggregate,
MMU pending units and privring status before separate acknowledgement writes.
The new code never acknowledges them. All unexplained nonzero raw status
stops, even if a corresponding interrupt would have been masked in Linux.
Fault details are read only for the bounded pending units. Partial/failed reads
remain errors; zero-initialized output storage is never a valid missing baseline.

Reset preflight reads MC only. Its non-destructive read is sourced; applicability
before POST is INFERRED and remains visible in the catalog. Post-A7 adds scoped
FIFO/MMU/privring coverage. These checks do not establish whole-chip coverage.
TOP uses 64 source-defined words with bounded continuation groups and explicit
fault/runlist presence. No runlist-zero assumption or PBDMA-count write probe.
No channel or scheduler is enabled. Unsupported/incomplete topology stops.

Diagnostic events and routes have fixed resident capacity. Phase/epoch mismatch,
overflow, backwards/failed clock and budget expiry latch failure. A finite scan
also bounds work if the clock makes no progress. Output is deferred; future
native integration must revoke its permit before draining this journal.
Twenty-five host cases and native object compilation pass. No VM/card run.
