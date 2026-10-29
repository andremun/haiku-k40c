# S1A7BUFFER handoff — incomplete

Buffered implementation and host validation are complete; the macro task is not.
No physical run. No new card approval. Old package-i2c remains consumed.

Owner-resident 2048-record buffer and 16 poll summaries. No extra GPU reads.
Overflow/reversed diagnostic clock fail closed; hardware permissions unchanged.
Drain follows controller return and permit revocation, before failure reporting.
POST_RESULT/readback/readiness logical order remains intact. Deadlines unchanged.
Host tests cover overflow, polls, timing, result order, and revoked-permit drain.
All 32 simulated RAM/profile write counts match the prior reviewed package.
Changed native objects and inert logger probe compile with the 4096-byte frame
warning enforced. Full make check PASS (check-host.log); host_check.py --check,
provenance --check and git diff --check PASS.

Plain native logging measurement passed, results/20261029-172432-a7-logging-plain.
Observed measurement stopped before QEMU launch on a relative executable name.
Failure preserved in results/20261029-172432-a7-logging-observer-stop.
Path fixed. ADR 006 continuation question is pending; no guest launched after it.
The buffer header changed after the preliminary measurement to place all timing
before POST_RESULT. Fresh plain/observed measurements are therefore required.

Next: receive permission to resume cardless validation; run logging_bench.py;
build fresh package-buffer; exact rehearse.py and all --check gates; complete
review hashes/docs and request review/explicit yes for one physical run.
Shared-tool consumer pin must follow this commit before consumer checks.
See docs/A7-BUFFER-REVIEW.md. S1 incomplete; D1 unapproved.
