# Fourth approved A7 attempt: STOPPED by the R5 rule at QEMU start

Run 2026-10-29 by Claude Code, after the user's explicit yes for one run of
package build/a7/package-rehearsal2/ (commit b77fd36). `build.py --check` and
`run.py --host-check` passed. Command: `python3 tools/a7/run.py --run-approved-A7-once`.
The consumed marker remains. No retry ran (ADR 006).

KNOWN: the launcher stopped after 2.52 s with "new R5 selected-class line; stop
without retry" (result.json). The new kernel line (kernel-after.log:149) is:
`vfio-pci 0000:04:00.0: enabling device (0000 -> 0002)`.
It appeared when QEMU opened the VFIO device. The host had rebooted at
2026-10-28 13:20, so this was the first open of the card in this boot: its PCI
command register was 0, and the kernel enabled memory decoding.

KNOWN: serial.log is empty. The guest firmware produced no output before the
stop. No guest job, driver load, request, grant, arming, POST or readiness step
ran. No write by our driver reached the card. VFIO's own open-time enable and
reset are host-side and allowed (ADR 005).

Teardown: host PCI command after exit 0x0002, bus mastering off (teardown.json).
No QEMU remains.

INFERRED: the line is informational (PCI enable from command 0x0000 to 0x0002),
not an IOMMU, VFIO or AER fault. The D0 retry did not print it because the card
had already been enabled earlier in that boot. The A7 rule stops on any new line
of the filtered classes, so it stopped here as designed. The A7 review said the
rule would not fire on a normal start; that was wrong for the first open after a
host reboot.
