# S1A7BUFFER: defer POST diagnostics and prepare the next package

Implement the plan approved by the user after S1A7STARTUP. Preserve all hardware
permissions, reference retention, one-shot gates and 10 s/15 s/600 s deadlines.
No physical run is authorized. Do not modify consumed packages or saved captures.

Use docs/A7-STARTUP-DIAGNOSIS.md; src/a7/Owner.*, src/devinit/Interpreter.* and
BoundPost.*; tools/a7/build.py, host_check.py, rehearse.py; native cardless tools.
Do not read tools/check_repo.py or tests/accept/.

Add a fixed-capacity owner-resident trace buffer. Keep instruction/I2C records
and logical event order. Overflow must stop effects and fail closed. Drain after
the controller returns and the permit is revoked, before fatal result markers.
Measure POST elapsed, delay requests/elapsed, condition sample counts/last values,
MMIO count/maximum latency and buffer drain time. Do not perform extra MMIO.
Test overflow, failed paths, unchanged access sequence, ordered drain and polling.
Measure the native logging path cardlessly with/without the existing observer.
Build a fresh single-use package; rehearse its exact job/binaries cardlessly.
Bind benchmark and rehearsal evidence to the package and publish review details.
Write PLAN/FINDINGS/RESULT, update STATUS; make check before the macro commit.
Then request review and explicit approval for one run. Never launch the card here.
