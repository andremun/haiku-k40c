# S1A7STARTUP result

Host-only diagnosis complete; review pending. No guest/card/reset action.
No production driver, deadline, permission, package or consumed-marker change.

Deliverable: docs/A7-STARTUP-DIAGNOSIS.md.
KNOWN: run6 is an exact 528-entry prefix of run5. Its Timeout is our wall-clock
POST guard. Haiku lifecycle source fits the existing open/write design.
Pinned source and exact saved kernel show synchronous IRQ-disabled UART output.
INFERRED: serial/VM/observer overhead likely contributes to budget exhaustion.
UNKNOWN: attribution among logging, condition polling, MMIO and scheduling.
Nine completed condition polls have no actual sample counts in the capture.
Explicit TIME/IO waits total 22,421 us; this excludes conditional waits.
Host inert 20,837-byte benchmark records observer amplification: one-byte
writes 0.329/2.659 s median untraced/traced; with two inert syscalls 0.337/5.992 s.
This is not a guest calibration or a hardware result.

Propose buffered instruction traces and bounded phase/poll measurements,
then native cardless validation before any new reviewed physical package.
Keep deadlines and hardware sequencing initially. Q10 records missing timing.
Run6 remains stopped; sensor operation not reached; Q9 remains open.
S1 incomplete. D1 unapproved. No retry authorization remains.

Validation: full make check PASS (check-final.log); all three generator
--check modes PASS; git diff --check PASS.
