# S1OWNERPOST result — 2026-10-27

DONE for resident binding/host integration and native link scope. Review pending.

- NativeOwner reserves one immutable PostImage in aligned resident storage.
- Lease-checked binding rejects wrong identity and all replacement attempts.
  Invalid extents do not consume the slot. Rejected bindings persist across clients.
- Copied diagnostics retain selection, RAM index and the final simulation result.
- Host-only simulatePost consumes the existing boot latch before selection,
  dedicated I2C preinit or POST. A temporary executor retains no client callbacks.
- Every admitted attempt finishes and quarantines owned memory, including a
  throwing host fixture. Detach/reacquire preserves result, latch and quarantine.
- Native header/build gates exclude simulation. The native module ABI stays v1,
  with no new firmware upload, callback-bearing or production startup operation.
- Default-denied DMA publication and existing owner/client contracts stay intact.

Validation: make check passes. Owner/POST: 9 cases, 6,388 assertions, zero failures.
Includes mutation, rejected/replacement ROM, leases, callback destruction, failed
strap/preinit/NACK/exception, reentrancy, real concurrent calls and latch conflict.
Synthetic owner suite: 177 checks. Existing owner-probe suite: 13 checks.
Generated aggregate evidence has exact --check comparison and source/ROM hashes.
Native owner/full-core cross-link and native header assertions pass. Compiling the
host fixture for the kernel is rejected; no simulatePost/global constructor symbol.
No exceptions/RTTI in the linked native units. No native load/execution claim.
Evidence: host-check.json, native-link.log, native-gate.log and native-hashes.log.

No VM/card, root, PCI/BAR, reset, binding or push. Shared VM tools unchanged.
The earlier native reload evidence covers its earlier recorded revision only.
Native POST execution, physical transports, verified DMA/visibility, VRAM,
quiescence and readiness remain gated. Complete means host simulation completion.
No A7 package or permission follows. Next: S1DMACONTRACT source/evidence closure.
