# A7 buffered diagnostics package

S1A7BUFFER, 2026-10-29. Preparation in progress. No physical run is authorized.

## Change for review

S1A7STARTUP identified synchronous serial output as an INFERRED contributor to
run6's POST timeout. This package moves instruction and I2C diagnostics to a
fixed-capacity resident buffer and measures the remaining costs. It does not
establish that logging was the sole cause of the timeout.

- Owner-resident storage: 2048 records and 16 distinct condition-poll summaries.
  No allocation or large kernel-stack buffer is added to POST.
- Instruction and I2C records retain their names and values. TRACE_AT gives the
  record index and microseconds since POST began. Poll observations use the
  value already read by the interpreter; there are no extra GPU reads.
- Poll summaries give PC, count, last raw value, condition index, final match and
  first/last sample times. Delay totals distinguish requested and elapsed time.
  MMIO totals/count/maximum cover the platform call during POST, excluding policy
  lookup and the timestamp-call cost itself. These measurements add CPU overhead.
- Buffer overflow or diagnostic clock reversal stops further effects. Existing
  guards remain in force. A diagnostic failure cannot become successful startup.
- Drain occurs after the controller returns and the execution permit is revoked.
  Script/I2C records and timing summaries precede POST_RESULT. Readback/re-arm and
  readiness records retain their logical order; they are deferred observations,
  not live progress. PASS/FAIL startup follows the complete drain.
- TRACE_DUMP_US measures drain time outside the controller. The independent
  600-second guest limit still bounds the whole run, including output.

The 10-second POST limit, 15-second controller limit, register/value allowlists,
arm-only witness/retention, sensor policy, observer proof, R5 rule, one open and
single-use approval remain unchanged. No pad, power, reset or PCI writes were
added. The old package-i2c and its consumed marker are retained.

## Validation and remaining gates

Host unit/boundary tests cover poll observation without additional reads,
overflow, reversed diagnostic clock, deferred result order and permit revocation
before drain. All 32 RAM/profile scenarios retain the old reviewed write counts.
These are simulated results, not physical execution evidence.

Native cardless logging measurement, final package hashes, exact package
rehearsal, full repository checks and approval are recorded below when complete.
A first observed logging measurement stopped before QEMU launch because the
observer received a relative executable name. The path was corrected; no guest
or card was started by that failed attempt. ADR 006 permission to continue was
requested. The earlier plain measurement is retained as preliminary evidence.

The removal of synchronous I2C audit output also removes incidental serial-output
gaps between attempts. No protocol delay was removed or added. Hardware timing
may change as a result; the bounded sensor policy and all fatal outcomes remain
as reviewed in ADR 010. Cardless logging measurements cannot validate those
physical timing effects.

Full make check, host authentication/boundary checks, provenance and diff checks
pass for this committed implementation. Fresh native measurement and exact
package rehearsal remain pending. This is not yet an eligible physical package.
