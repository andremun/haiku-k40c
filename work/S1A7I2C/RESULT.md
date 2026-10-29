# S1A7I2C result

KNOWN / TRACE_VERIFIED: Linux made four address-NACK attempts for each exact
sensor pair at 0xab8d. Each sent only 0x98. No register/value payload followed.
Nouveau's script ignores the transfer result. The old fatal-on-any-NACK policy
differs. Run5's actual Haiku I2C class remains UNKNOWN.

The independent decoder and real DedicatedI2c response replay reproduce all
eight address NACKs with clean STOP. An ACK-all control succeeds. No guessed
settle delay, pad write or recovery sequence is added.

The user selected ADR 010: only those two exact sensor pairs may retry up to
four times and continue after four address NACKs with clean STOP. All other
failures stay fatal. New telemetry records PC/bytes, primary/cleanup error,
phase/bit, attempt/disposition, elapsed guards and operation count.

Fresh package: build/a7/package-i2c/. Manifest/inventory and host results are
in work/S1A7I2C/. The exact binaries pass cardless rehearsal in 78.34 s:
results/20261029-104357-a7-rehearsal/. Final names only, raw B_ERROR, one prepare,
identity/client/owner loads 3/2/1, and retained Failed state on client reload.
This is cardless OS evidence, not sensor-policy hardware verification.

Actual-owner host cases permit only the captured address-NACK outcome and
reject payload NACK, STOP/IO/stretch/timeout and other-address NACK. Package,
replay, rehearsal, native cross-link and full make check pass. Logs accompany the handoff.
Review: docs/A7-REVIEW-PACKAGE.md. No physical run was attempted or approved.
Run5 and all consumed markers remain intact. S1 is incomplete. D1 unapproved.
