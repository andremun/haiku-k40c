# A7 guest installation/publication correction (host only)

1. Check pinned Haiku devfs, VFS and legacy-loader sources against the captured
   read-only-filesystem and transient not-executable errors. Do not guess a GPU bug.
2. Download add-ons into a private staging directory outside watched kernel
   directories. Finish and chmod before publishing an atomic hard link. Fail
   on cross-filesystem or existing-target errors. Never copy into a live path.
3. Wait a bounded time for the actual character node. Open the A7 stream exactly
   once after publication. A timeout/open failure stops the job without retry.
4. Test actual shell functions with inert host fixtures for partial downloads,
   failed download/link, bounded publication waits and no repeated device open.
5. Build a fresh-key package at a new path. Preserve both consumed packages and
   both captured attempts. No guest or D1 launch is authorized by this task.
6. Update review/status/results, run make check, and commit this host-only task
   separately. A further physical launch needs fresh review and explicit yes.
