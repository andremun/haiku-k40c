# Preliminary plain native logging measurement

CARDLESS_KVM only: no GPU, POST, grant key or card permit. The probe replays
528 saved instruction records through synchronous dprintf, then through the
fixed-capacity diagnostic buffer, and measures drain time separately.
Two native initializations produced three sample pairs each; see serial.log.
The guest passed in 63.72 seconds; its uploaded kernel matched the link kernel.

This is preliminary evidence. The subsequent observed case stopped before QEMU
launch on an executable-path error. A trace/result output-order correction was
also made to the buffer header afterwards. The probe retained here is the binary
that produced this capture, not the final package candidate. Fresh plain/observed
measurements are required before the new physical package can be offered.
No further guest was launched without requesting ADR 006 permission.
