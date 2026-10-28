# Findings

- KNOWN: build.py --check and run.py --host-check passed for unchanged commit
  8974695. The single approved command launched QEMU and consumed the package.
- KNOWN: the launcher stopped after 107.88 seconds with "A7 guest job failed".
  job.exit is 1. QEMU and its tracer exited. No retry was attempted.
- KNOWN / HARDWARE_VERIFIED under Haiku: B5 read PMC_BOOT_0=0x0f1240a1 and PCI
  command 0x0007 twice during driver discovery. These are identity reads only.
- KNOWN: the A7 client logged its role. No native PREPARED event, request upload,
  cutoff, grant, arming, POST result or readiness marker was captured.
- INFERRED: failure occurred during device discovery/open, before the request
  upload. The approved job did not redirect guest shell stderr to the host.
  The exact guest failure cause is UNKNOWN. This is not evidence that POST failed.
- INFERRED: no A7 GPU writes executed. The host never issued a grant, and the
  approved source requires a verified grant before any physical execution permit.
- UNKNOWN: 0x100c10 values before/after POST, POST behavior and readiness results.
- KNOWN: R5 before/after bytes match exactly, so the selected-class delta is empty.
  This is not a clean full-kernel-log claim or payload/coherency proof.
- KNOWN: end-of-guest host PCI command is 0x0002 (bus mastering disabled). A
  separate process-table check found no QEMU process. No manual reset was used.
- Raw launcher evidence remains at results/20261028-a7-fad36717/. Byte-identical
  copies and a generated summary are at results/20261028-a7-post/. The original
  consumed marker still points to the original folder. S1 remains incomplete.
- Full make check passes in check-final.log. record_run.py --check verifies the
  raw copies, original manifest, archived artifacts, summary and empty delta.
  No source or artifact from the approved package changed before or during launch.
