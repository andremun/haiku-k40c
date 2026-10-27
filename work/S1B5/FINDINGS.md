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
