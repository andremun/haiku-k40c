# Findings

- The second independently approved attempt is committed as 2c8a34d. Shell output
  identifies the read-only-filesystem error at device open. No grant or POST ran.
  A transient identity add-on Not an executable precedes valid B5 identity reads.
- KNOWN / SOURCE_ONLY: pinned Haiku devfs.cpp:774-779 publishes S_IFCHR nodes and
  line 1986 leaves create NULL. VFS vfs.cpp:5578 opens an existing node; 5587-5590
  returns B_READ_ONLY_DEVICE for an absent entry whose parent lacks create.
  The legacy loader queues filesystem changes at legacy_drivers.cpp:1090-1101
  and loads add-ons at 1161. See source-pins.json for exact revision/URLs/hashes.
- INFERRED: direct downloads exposed incomplete ELF files to the watched loader,
  and the O_CREAT shell open preceded character-node publication. The captured
  messages and pinned chain support that mechanism, not every scheduling detail.
  Exact running-kernel source identity is not established. No GPU defect is shown.
- The new job privately stages complete downloads, chmods them, and atomically
  hard-links into final paths. Exclusive stage/role directories and no-overwrite
  destination checks prevent repeats from truncating a published inode. A failed
  hard link, including EXDEV, stops without copying into a watched path.
- B5-BEGIN now precedes identity publication. The A7 node wait checks S_IFCHR,
  scans at most 30 times with one-second delays and never opens while polling.
  After publication the job opens once. A remaining disappearance race fails
  safely; it is not a reason to retry. All existing outer deadlines remain.
- Five host fixtures execute actual shell helpers with inert mocks and paths.
  They cover complete/mode-correct hard links, partial downloads, each failure,
  repeated installation, bounded node waits, syntax and one open. They do not
  prove Haiku BFS hard-link behavior or physical execution.
- GPU register sequences and all nits remain unchanged. The fresh package/key is
  at build/a7/package-publication/, metadata in this folder. Both consumed markers,
  original manifests, artifact archives and raw evidence remain unchanged.
- Both native artifacts cross-link. The unchanged owner/authority/native-client
  fixtures pass, as do eight launcher and two omission fixtures. No new guest,
  host binding change, root command, manual reset or D1 run has occurred.

- Full make check PASSES (zero repository-checker failures, exact pins, all
  generators and host tests). Package/host/source-pins --check and both immutable
  run recorders pass. Both old consumed markers are present; the publication
  package has no consumed marker. No third guest has been launched.
