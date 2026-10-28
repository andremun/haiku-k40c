# S1A7RUN5: new A7 package with the ADR 009 start-window allowance

After the S1A7RUN4 stop (results/20261029-a7-ba6a1a54/), allow exactly one
`vfio-pci 0000:04:00.0: enabling device (...)` line between QEMU start and the
first guest serial output (ADR 009). Build a new single-use package in
build/a7/package-run5/ with records in work/S1A7RUN5/. Keep the consumed package
and the S1A7REHEARSAL2 records unchanged. Rehearse the exact package cardless.
Run make check. A card run needs the user's explicit yes for one run.
