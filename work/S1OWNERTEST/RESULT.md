# S1OWNERTEST result — 2026-10-27

DONE for native cardless owner lifetime scope. Grouped review pending.

- Added GPU-free legacy owner-client probe with explicit init/uninit markers.
- Verified user-nonpackaged module/driver staging against pinned Haiku sources.
- Added fixed owner staging and strict reload evidence validation to cardless_run.
- Bound both ELF hashes, source commit and matching guest kernel in launch evidence.
- No QEMU option changed. Base disk stays unchanged; one disposable run only.

Validation: make check passes. Host probe: 13 checks; runner suite: 4 tests.
Owner and client cross-link against the matching hrev60207 kernel.
First prepared KVM run PASSES in 52.57 seconds, source commit 45923d6.
Evidence: results/20261027-owner-reload/ (launch/job/serial/HTTP/environment/hashes).
Both actual client init/uninit pairs and the legacy reload are present.
Lease 1 detaches token 2 into quarantine; lease 2 observes the same token,
Failed latch, owned=1 and quarantine=1. Repeated startup/allocation are denied.
Native host byte readback, aligned GPA, cleanup and denied publication pass.
The guest kernel hash matches the expected link kernel.

Shared tools re-pinned to 45923d6 in haiku-k40c-llm commit 0d59079.
Its make check passes. The initial sandboxed host server check was rerun outside
the sandbox; no extra VM launch occurred.
All changes committed. No physical card, PCI/BAR, root, reset, binding or push.

This closes the tested owner lifetime path only. DMA/device IOVA/visibility,
failed OS-release recovery, arbitrary concurrency, native executor binding,
VRAM ownership and physical readiness remain gated. No GPU evidence or A7 claim.
Next host task: S1POST immutable execution binding and register policy.
