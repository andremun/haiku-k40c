# 010. Continue only after the captured bounded sensor address NACKs

Date: 2026-10-29. Status: accepted user decision for the next review package.
No card run is authorized by this decision.

## Evidence and correction

The Linux debug trace shows four attempts for each of the two pairs at ROM
0xab8d, address 0x4c, registers 0x19 and 0x0d, intended value 0x73. Each attempt
transmits only address byte 0x98, followed by NACK. No register/value payload
is sent in those frames. See work/S1A7I2C/linux-i2c.json and its capture lines.
Nouveau bios/init.c:1033-1056 ignores init_wri2cr's result and continues.
Earlier statements that Linux wrote the sensor registers meant an attempted
script operation. Successful delivery was not established and is not claimed.

The raw Haiku run5 log has Error::Io without transaction detail. Its precise
I2C failure remains UNKNOWN. Captured Linux responses reproduce address NACK
in the current host I2C code. This supports a hypothesis, not a Haiku diagnosis.

## User decision

The user selected: "Continue only after the same bounded, address-NACK outcome
for the two exact sensor writes; keep all other failures fatal (Recommended)".

The new package may attempt each exact pair at most four times. An address
NACK may retry only after a successful bounded STOP. After four address NACKs,
POST may continue and log ReferenceNack. The next exact pair remains eligible.
An ACKed transfer completes normally. A NACK in either payload byte, any IO,
stretch, timeout, clock, budget or STOP error remains fatal. Every error outside
these two exact ROM pairs remains fatal. Repeated/out-of-order pairs are denied.
No recovery pulses, reinitialization or inferred settle delay is added.
Existing per-attempt, POST and whole-stage bounds remain in force.

ADR 004's ROM and operation restrictions still apply. This narrows Linux's
ignore-all-return behaviour to the captured response. It does not claim the
internal bit-bang waveform equals Linux's selected adapter algorithm.
Claude review and an explicit yes for one new package are still required.
