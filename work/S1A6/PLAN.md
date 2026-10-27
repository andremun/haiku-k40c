# S1A6 plan

1. Follow BIT-I/M dispatch, RAM selection, contextual registers, condition and macro inputs.
2. Extend structural preflight with a separate deterministic semantic closure report.
3. Report supported inputs and all denied or unknown paths without claiming hardware readiness.
4. Add a host-only dedicated GF119 I2C transport with bounded clock stretching,
   monotonic deadline, failure propagation, and no retries or invented bus recovery.
5. Test wire encoding, ACK/NACK, every transport failure, stalled/rollback clocks,
   invalid bus descriptors, and physical-backend refusal.
6. Preserve ADR 004 exact-ROM permission and existing source-derived reports.
7. Update documentation, licensing, provenance and handoff. Run make check and commit.
