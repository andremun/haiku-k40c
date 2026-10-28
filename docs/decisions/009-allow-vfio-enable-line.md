# 009. Allow the VFIO device-enable line at QEMU start

Date: 2026-10-29. Status: accepted (user decision, after the S1A7RUN4 stop).

## Context

The A7 launcher stops on any new kernel line of the R5 filtered classes. The
approved fourth A7 run stopped after 2.52 s on
`vfio-pci 0000:04:00.0: enabling device (0000 -> 0002)`
(`results/20261029-a7-ba6a1a54/kernel-after.log:149`). That was the first
VFIO open of the card after a host reboot: the PCI command register was 0. The
guest never started. The line is informational, not an IOMMU, VFIO or AER fault
(INFERRED).

## Decision

The A7 launcher (`tools/a7/run.py`, `StrictLog`) allows exactly one line of the
form `vfio-pci 0000:04:00.0: enabling device (XXXX -> YYYY)`, for that card
only, between QEMU start and the guest's first serial output. Every other
filtered line, a second enable line, or an enable line outside that window
still stops the run. Allowed lines are recorded in `result.json`
(`allowed_kernel_lines`).

## Limits

No other stop rule changes. ADR 006 and ADR 008 still apply: each write-stage
run needs the user's explicit yes, and any stop is reported before another run.
