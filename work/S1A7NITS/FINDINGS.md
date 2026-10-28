# Findings

- The original approved attempt is committed as 600d114. It stopped before any
  request or grant. No POST failure was observed. No retry is authorized.
- FIFO preinit now tracks each successful register read. A write must preserve
  all bits except 0x100, clear that bit first, then set it. Exactly two writes
  are admitted. Missing reads, other-bit changes, wrong order and replay fail.
- BoundPost exposes a read-only derivation of the dedicated bus from its owned
  approved ROM. Its existing preparation and the A7 allowlist use that same
  derivation. For this ROM it selects bus 2, register 0xd054, value 7.
- The host owner probe tests the actual private transport under the real owner's
  active permit, rather than a second policy implementation. It rejects the
  other 15 bus registers, wrong pin values/reads, unrelated FIFO bit changes,
  missing reads, wrong ordering, other addresses and third writes. Its friend
  access is excluded from kernel builds. Positive owner scenarios still pass.
- The exact clean Ed25519 revision is copied to the persistent checkout at
  ~/haiku-cross/src/orlp-ed25519, with upstream recovery remote. Validation still
  checks the commit, clean tree and every compiled source/header/license hash.
  The old temporary checkout and consumed package remain untouched.
- Omissions are generated from the same immutable ROM's CCB 4.0 table. There are
  eight NVIO I2C buses and four hybrid pads. The seven omitted buses and four
  omitted pad power-offs are listed, plus ROM shadow toggles. The source chain
  maps PCI offset 0x50 through NV40's 0x88000 aperture. These are SOURCE_ONLY
  baseline facts, not new physical measurements. The reasons preserve A7 scope.
- The new shell captures stdout/stderr, marks its open step and uploads a bounded
  write-once output before job.exit. The client logs get_module failure status.
  Host tests inject that failure. This does not resolve the first run's cause.
- A fresh package/key is built under build/a7/package-review-nits/. Current
  reports are in work/S1A7NITS. The original work/S1A7NATIVE manifest and original
  build/a7/package/consumed.json are unchanged. Original artifacts are archived.
- Native cross-links and host fixtures pass. Actual platform/client assertions:
  4129/24. All 32 ROM/strap scenarios run (16 complete); tamper/scoping, clock,
  I2C and retained one-shot failures still pass. Eight launcher tests and two
  synthetic omission tests pass. New hardware behavior remains UNKNOWN.

- Full make check PASSES, including zero repository-checker failures, exact pins,
  all generator checks and the complete host suite. build.py --check,
  host_check.py --check, crypto_sources.py --check and record_run.py --check pass.
  Original source/approval evidence is preserved. The new package has not run.
