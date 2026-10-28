# Findings

- The user directly approved one corrected-package run. Unchanged 0390b8b passed
  build.py --check and run.py --host-check. Exactly one guest launched.
- KNOWN: the guest job stopped after 103.26 s, exit 1. Captured stderr identifies
  hard-link publication of the identity add-on: Operation not allowed. The
  installer failed closed instead of copying into a watched path.
- KNOWN: only GET identity occurred. Owner/client files were not downloaded.
  No B5 identity marker, native A7 event, request, cutoff or grant was captured.
  B5 reads, arming, POST and readiness were NOT_REACHED. Values are UNKNOWN.
- INFERRED no A7 GPU writes: the required host grant was never issued. This is
  not a hardware-verified POST failure or evidence against the card.
- KNOWN: R5 before/after bytes match exactly in the selected classes. Host PCI
  command after exit is 0x0002, mastering disabled. No QEMU remains. No reset used.
- Linux host fixtures established publication ordering, not Haiku filesystem
  hard-link support. The actual guest rejected the selected publication method.
- There are now three individually approved pre-grant installation failures:
  8974695 (unknown discovery/open error), 24fb578 (read-only filesystem at open),
  0390b8b (hard-link publication denied). Source/artifact changes differentiated
  these packages. Apply the repository three-attempt escalation rule now.
- ESC-003 requests review of a Haiku-supported atomic publication method and a
  cardless validation plan. No fourth package correction or launch is attempted.
- Raw launcher folder: results/20261028-a7-c07e1db9/. Canonical raw copies and
  generated summary: results/20261028-a7-post-03/. All three consumed markers,
  earlier captures and archived original artifacts remain unchanged.
- Full make check PASSES, including zero repository-checker failures, pins,
  generator checks and host fixtures. record_run3.py --check verifies raw copies,
  original package metadata, archived artifacts, summary and empty R5 delta.
  Passing host checks do not establish Haiku publication support or POST success.
