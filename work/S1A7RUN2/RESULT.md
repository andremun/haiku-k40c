# S1A7RUN2: STOPPED before device open

The directly approved unchanged 24fb578 package passed build/host checks and
launched once. The guest job failed after 95.26 s at the stream-device open:
/dev/misc/k40_a7_stage: Read-only file system. Captured shell output identifies
that operation. The identity add-on also had a transient "Not an executable".
A publication/loading race is INFERRED, not yet a verified causal conclusion.

No arm request or grant was captured. POST/readiness were NOT_REACHED and target
register values are UNKNOWN. No verified POST success/failure result exists.
No A7 writes is INFERRED from the required-grant gate. B5 identity/command reads
passed (HARDWARE_VERIFIED under Haiku). S1 remains incomplete.

R5 selected-class delta is empty. Host command after exit is 0x0002, mastering
disabled. No QEMU remains. Both consumed markers are retained. No retry, D1,
manual reset, root command or push occurred.

Evidence: results/20261028-a7-post-02/, with exact copies, manifest and summary.
Original launcher folder: results/20261028-a7-4ac95d19/.
Next: host-only source diagnosis and a corrected package. Any new physical
launch requires fresh approval under ADR 006 and ADR 008.

Full make check and record_run2.py --check pass. This run's evidence is committed
separately from any subsequent host-only publication/loading correction.
