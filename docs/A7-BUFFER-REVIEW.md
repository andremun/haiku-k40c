# A7 buffered diagnostics package

S1A7BUFFER, 2026-10-29. Preparation complete. Claude review and explicit one-run approval are pending.
No physical run is authorized.

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

The user approved resuming cardless validation after the preserved pre-launch
path failure. Fresh measurements use the final buffer header. Six samples in
each mode give these medians:

| Native cardless mode | Live output us | Buffer insertion us | Deferred drain us |
|---|---:|---:|---:|
| Plain | 900,671 | 20.0 | 1,684,176 |
| Observed | 8,169,705 | 25.5 | 14,996,946 |

These replay the 528 run6 instruction records in init_driver context. They are
not a POST or authenticated-write timing measurement. Host workload was not
isolated. Brief retained host/I2C checks overlapped the observed guest. All raw
samples are saved in work/S1A7BUFFER/native-logging.json and its two result folders.
No additional GPU read, grant, owner module or VFIO device was used.

The exact fresh package passed rehearsal in 78.50 s at
results/20261029-175324-a7-rehearsal/. Native identity/client/owner load counts
and one preparation are recorded in work/S1A7BUFFER/rehearsal.json. The raw open
returned B_ERROR (0xffffffff) after the expected no-card refusal, with no
request/grant or POST. The prior failed attempt and preliminary plain capture
remain immutable and are not bound to this fresh package.

The removal of synchronous I2C audit output also removes incidental serial-output
gaps between attempts. No protocol delay was removed or added. Hardware timing
may change as a result; the bounded sensor policy and all fatal outcomes remain
as reviewed in ADR 010. Cardless logging measurements cannot validate those
physical timing effects.

Full make check, host authentication/boundary checks, provenance and diff checks
pass. Package, benchmark and rehearsal --check modes pass. The live read-only
host check passes at preparation time. Prerequisites must be rechecked immediately
before any approved launch. See docs/A7-REVIEW-PACKAGE.md for complete artifact
hashes, write inventory, commands and stop conditions.

Review the implementation commits 0b450b1 and 210e5ee, plus the package-completion
commit containing this document. S1 is incomplete. D1 remains unapproved.

A test-dispatch error was found during completion. A header dependency had
preceded all and changed the default target. The dependency now follows all,
and .DEFAULT_GOAL explicitly selects all. The complete suite passed via
make -s -C tests all, followed by the final make check. The source-bound host
report and package metadata were rebuilt. Guest binaries, kernel, ROM and job
remain byte-identical to the passing rehearsal, verified by --check.
The earlier incomplete-dispatch logs remain preserved and are not the final
validation record. Use host-all-tests.log and check-final.log for full coverage.
