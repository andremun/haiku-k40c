# Findings

- The user's "aproval is given" answered the explicit request for one new A7 run.
  Unchanged commit 24fb578 passed build.py --check and run.py --host-check.
- One launch ran. It stopped at 95.26 s with "A7 guest job failed", job.exit 1.
  The package-review-nits consumed marker remains; no retry was attempted.
- KNOWN: shell output reached A7-OPEN-DEVICE, then open of
  /dev/misc/k40_a7_stage failed with "Read-only file system". A7-DEVICE-OPEN is
  absent. No request, cutoff, grant, arming or POST/readiness event was captured.
- KNOWN: the serial log records a transient identity add-on "Not an executable"
  while the file was being installed. A later load successfully read B5 identity
  0x0f1240a1 and PCI command 0x0007 (HARDWARE_VERIFIED under Haiku, identity only).
- INFERRED: direct downloads into watched add-on paths race discovery, and the
  shell O_CREAT open races node publication. Exact causal proof needs the pinned
  Haiku loader/devfs chain. Do not classify this as a GPU POST failure.
- POST/readiness are NOT_REACHED. Target values are UNKNOWN. INFERRED no A7 GPU
  writes: no host grant was issued and the unchanged source requires that grant.
- KNOWN: R5 before/after bytes match exactly, limited to the selected classes.
  Host PCI command after guest exit is 0x0002, mastering disabled. No QEMU remains.
- Canonical copies: results/20261028-a7-post-02/. Original immutable launcher
  evidence: results/20261028-a7-4ac95d19/. First-run evidence is unchanged. Both
  consumed markers and original artifact archives remain. S1 is incomplete.
- Full make check passes. The recorder verifies all raw copies, original package
  metadata, archived artifacts, summary and empty selected-class delta.
