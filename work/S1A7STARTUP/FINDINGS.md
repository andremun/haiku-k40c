# Findings

Host-only investigation. No guest, card access, reset or production change.

KNOWN: run6's 528 trace entries are the exact prefix of run5. Our 10 s
wall-clock guard includes synchronous logging, waits and off-vCPU time.
The stopping PC is a ZM_REG write, not a hardware poll timeout.
Explicit TIME/IO waits total 22,421 us. Nine CONDITION_TIME operations may add
poll waits; actual sample counts remain UNKNOWN. Do not call 22,421 us all waits.

KNOWN SOURCE_ONLY: pinned Haiku driver hooks permit setup at open/write;
no generic ten-second startup deadline or missing required initialization hook
was found. PCI reservation is ownership, not GPU reset or POST. Native delay
units match Haiku APIs. Stock older-NVIDIA first-open setup is only a lifecycle
example, not a Kepler sequence.

KNOWN: saved kernel serial routine uses IRQ disabling and per-character port
I/O. Pinned debug.cpp makes dprintf synchronous. QEMU upstream and observer
sources support a syscall-amplification mechanism. Exact complete running
source identity and actual syscall counts remain unestablished.
Host inert benchmark: 20,837 one-byte writes take median 0.329 s untraced,
2.659 s observed; adding two inert syscalls per write gives 0.337/5.992 s.
These are not guest or hardware timing measurements.

INFERRED: logging/VM/observer cost likely contributes to exhaustion. UNKNOWN:
attribution among logging, condition waits, MMIO, sleep overshoot and scheduling.
Legacy Book 19200 baud is not the guest setting or a QEMU time bound.
No printed reset ioctl is inconclusive because of the trace's device-FD filter.

Propose fixed-capacity in-memory instruction trace and phase/poll timing, then
native cardless measurements, with existing deadlines and permissions retained.
No implementation/package change in this task. See docs/A7-STARTUP-DIAGNOSIS.md.
