# S1A7RUN7 result

PASS: native POST and independent readiness on this card under Haiku only.
One directly user-approved unchanged package-buffer launch. No Claude ACCEPT
claimed. Approval consumed; no retry. S1 incomplete. D1 unapproved.
Evidence: results/20261029-a7-069cb71b/README.md; work/S1A7RUN7/report.json.

Native 537 active/38 skipped exactly match Linux's normalized 575-entry path.
Linux raw 560/38 includes 23 synthetic offset-zero REPEAT messages. Opcode bytes
match ROM. This is instruction selection, not MMIO/timing equivalence.
0x20 completes; both 0x4c sensor pairs record four address NACKs with clean STOP,
then ReferenceNack under ADR 010. Sensor configuration/presence not established.
POST 88,805 us; drain 21,694,572 us; guest 134.02 s. No overflow/clock fault.
Nine conditions complete: three sample twice, six once. Strong evidence supports
logging overhead for run6 (INFERRED); its exact past breakdown stays UNKNOWN.

Fresh arm target 0x16d2000, encoded 0x16d20. Post-POST readback is zero. Cause
UNKNOWN. Driver re-arms successfully; no final register readback is recorded.
Timer advances; VRAM 11520 MiB; three sampled dwords pass two patterns/BAR flush.
Pending zero is INFERRED from unchanged guarded PASS, not separately logged.
Owner retains token 1 in Complete state 2. No DMA-publication/visibility claim.
R5 byte-identical, no allowed lines. Host command 0x0002/master off. Owned
QEMU/tracer exited; separate pgrep finds no QEMU. No root/manual reset.

PASS: source/capture-bound result_report.py --check, full make check and diff check.
Package remains consumed. Next gate is D1 with its own prepared package/review
and explicit run approval; Q7 remains open.
