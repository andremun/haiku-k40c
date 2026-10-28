# Second approved A7 attempt: STOPPED at device open

The user approved exactly one run of unchanged package 24fb578. Build and host
checks passed. The launcher stopped after 95.26 s with guest job exit 1.
Both consumed markers remain. No third launch is authorized.

KNOWN: job-output.txt records the failed operation:
`/dev/misc/k40_a7_stage: Read-only file system`.
The job reached A7-OPEN-DEVICE but not A7-DEVICE-OPEN. No request/grant was captured.
The serial log also records a transient identity add-on "Not an executable",
then successful B5 identity reads. Device publication/loading race is INFERRED.

POST and readiness were NOT_REACHED. 0x100c10 before/after values are UNKNOWN.
No verified POST success/failure result exists. No A7 writes is INFERRED from the
missing required grant. B5 identity and command are HARDWARE_VERIFIED under Haiku.

R5 selected-class before/after bytes match. kernel-delta.log is empty. Host PCI
command after exit is 0x0002, with mastering disabled. No QEMU remains.
This is not proof of payload/coherency or a clean full kernel log. S1 is incomplete.

summary.json, approved-package.json and raw copies are generated/preserved by
tools/a7/record_run2.py. Original launcher files remain in
results/20261028-a7-4ac95d19/. Original artifacts are archived, outside Git, at
build/a7/approved-24fb578/. The recorder's --check compares all preserved bytes.
