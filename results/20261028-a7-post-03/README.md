# Third individually approved A7 attempt: STOPPED at publication

The directly approved unchanged 0390b8b package passed build/host checks and
launched once. The job stopped after 103.26 s, exit 1. No retry occurred.

KNOWN: job-output.txt reports that hard-link publication of the staged identity
add-on to kernel/drivers/bin/k40_identity_probe failed: Operation not allowed.
The fail-closed installer did not copy into the live path. Only GET identity
occurred. Owner/client downloads, device open and the grant exchange were not
reached. This is not a verified GPU POST failure.

B5 identity reads, A7 target arming, POST and readiness were NOT_REACHED.
Identity, PCI command under the probe and 0x100c10 values are UNKNOWN for this
attempt. No A7 writes is INFERRED from the absent required host grant.

R5 selected-class before/after bytes match. kernel-delta.log is empty. Host PCI
command after exit is 0x0002, mastering disabled. No QEMU remains. This is not
payload/coherency proof or a clean full-kernel-log claim. S1 remains incomplete.

summary.json, approved-package.json and exact raw copies are preserved by
tools/a7/record_run3.py. Original: results/20261028-a7-c07e1db9/. Artifacts are
archived outside Git at build/a7/approved-0390b8b/. All consumed markers remain.
The three-attempt installation problem is escalated as escalations/ESC-003.md.
No fourth package change or physical launch is authorized by this record.
