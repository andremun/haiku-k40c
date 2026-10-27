# S1B5 findings

## Host preflight (2026-10-27)

KNOWN from read-only sysfs inventory: 0000:04:00.0 uses vfio-pci,
is alone in IOMMU group 23, and /dev/vfio/23 is writable by this user.
No host QEMU process ran. The saved VM PID was stale and both sockets absent.
No shutdown was needed. No host binding, BAR, or reset command ran.

## Implementation

The identity probe previously reported OS PASS when no K40c existed.
It now fails that case and emits a B5 stage marker and distinct identity PASS.
Host spies exercise memory-decode refusal, absence, wrong identity, and all-ones identity.
The new launcher checks complete serial evidence rather than shell exit alone.
The uploaded guest kernel must match the kernel hash in the stage manifest.
An independent pidfd watchdog enforces the deadline and handles launcher death.
The shared launch lock also covers the cardless and application launchers.
transfer_server.Handler and vm-test.sh remain unchanged.

The first host-test run exposed an HTTP log lock deadlock and a closed-pipe cleanup error.
Use a reentrant server lock and handle the watchdog pipe closure. The corrected tests pass.

The old B5 task ID names the completed Linux dependency map.
The initial rules commit reused its task/plan paths. Restore them unchanged and use S1B5.

Native builds link both probes against ~/haiku-cross/lib/kernel.so.
probe_stage.py --check verifies the identity ELF, source hashes, and raw kernel hash.
card_run.py --check passes on the real host without launching QEMU.
Only the matching kernel hash is retained in B5 evidence, not the kernel binary.
The identity host-spy test reports 32 checks and zero failures.
The launcher suite reports 11 tests and zero failures.
The unchanged shared transfer-server suite reports 26 checks and zero failures.

## Cardless native run

The single cardless KVM run passed in 51.74 seconds (tool result.json).
Evidence: results/20261027-s1a-cardless/. No panic. job.exit is 0.
Devfs loaded the cardless probe twice. Both loads reported OS PASS.
B5 verdict validation must accept multiple valid decode/identity observations.
No hardware-stage attempt has occurred yet.

The post-cardless make check passes. The B5 log validator accepts repeated valid
identity observations while rejecting any failed decode, panic, or probe failure.
The sibling OpenCode runner suite passes 21 tests using the bundled Node runtime.
The application integration checker fixture suite passes five tests.

## First B5 attempt: false panic classification

The first B5 launcher stopped at a normal Haiku boot banner, before probe load.
result.json records the tool's panic error. That classification was wrong.
The banner appears in both the failed-stage serial log (line 235) and the
successful cardless serial log (line 237). Neither has an actual PANIC message.
No B5 stage or identity marker appeared. No guest HTTP job ran.
Preserve the first result and logs. Fix only the host parser and add a regression.
This was no real hang or panic. A further authorized read-only attempt uses
the same guest options and driver. A real hang or panic still forbids retry.
The corrected host suite passes 12 tests.
