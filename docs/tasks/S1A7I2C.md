# S1A7I2C: diagnose the run5 sensor stop and prepare a reviewed package

Read the immutable run5 evidence, pinned Nouveau and Linux debug trace. Decode
actual I2C address/data/ACK responses independently and replay captured responses
through the current I2C implementation. Distinguish source/capture facts from
unobserved Haiku error details. Do not infer a missing delay from elapsed gaps.
Add bounded native telemetry for each transaction: PC/address/register/value,
primary/cleanup error, transfer phase/byte and timing/budget information.
The user selected the bounded sensor address-NACK policy in ADR 010. Implement
that exact scope for review. Do not ignore unknown IO/clock/stretch failures,
add recovery pulses, invent timing or widen register/DMA permissions.
Prepare a fresh single-use package, host checks, matching cardless rehearsal,
write inventory and review document. Keep all consumed markers/evidence.
No card run is approved. Update STATUS and PLAN/FINDINGS/RESULT, make check and
commit one macro task on main. Never push or change llm-server branches.
