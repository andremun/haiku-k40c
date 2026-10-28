# S1A7INSTALL: host-only publication correction

Diagnosed a source-supported installation/publication race from the captured
read-only-filesystem and transient Not an executable errors. Exact runtime
scheduling remains INFERRED. No GPU POST failure was observed.

The new job stages complete executable files outside watched directories,
publishes hard links with no copying fallback, and refuses existing targets or
repeated installs. It waits at most 30 seconds for the fixed character node,
then opens exactly once. B5-BEGIN precedes identity publication. Timeout and
open errors stop; no retry or extra GPU write sequence was added.

Five inert host shell fixtures pass. Both native artifacts cross-link, existing
owner/authority/client fixtures pass, and the new package/source check passes.
Full make check passes, recorded in check-final.log. Source URLs/hashes are captured at
the project Haiku reference revision. reference/ and reviewer checks are unchanged.

Package: build/a7/package-publication/, with fresh key and no consumed marker.
Metadata: package.json, write-inventory.json, host-check.json and source-pins.json.
Review: docs/A7-REVIEW-PACKAGE.md. Both raw-capture recorders still pass.
Both consumed markers and original archives remain. Second-run evidence is
committed as 2c8a34d, results/20261028-a7-post-02/.

No third guest, D1, root command, binding change, manual reset or push occurred.
A further A7 launch requires fresh review and explicit one-run approval.
S1 remains incomplete. S2/S3 preparation is still conditional on actual S1 success.
