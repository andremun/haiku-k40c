# S1A7RUN6: one approved run of the reviewed I2C package

The user supplied Claude's ACCEPT review of 2818763 and explicitly authorized
one launch of build/a7/package-i2c on 2026-10-29. Run build.py --check,
run.py --host-check, verify the exact reviewed hashes, R5, VFIO group ownership
and absence of QEMU. Then run --run-approved-A7-once exactly once.
Do not alter the reviewed source or binaries. Keep the consumed marker.

Record the command, artifact hashes, native I2C outcomes and instruction counts,
flush target/readback/re-arm, timer, VRAM, scratch and pending observations,
R5 delta/allowed lines and post-exit bus-master observation. Missing evidence
stays UNKNOWN/NOT_REACHED. A7 success does not establish S1 success.
Add a README to the original results folder. Update STATUS and task findings,
write RESULT (max 40 lines), run make check, and commit on main. Never push.
A stop consumes approval. Report it and do not retry, including an already-POSTed
stop or a parser false alarm. D1 and other write stages remain unapproved.
