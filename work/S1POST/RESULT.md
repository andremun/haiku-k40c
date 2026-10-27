# S1POST result — 2026-10-27

DONE for host immutable binding/access-policy scope. Grouped review pending.

- PostImage owns and hashes the complete ROM; no caller digest/tables/roots/index.
- PostLayout derives bounded main/extra roots and reviewed table/opcode inputs.
- Cache one simulated strap-selection attempt; failure cannot silently reread it.
- BoundPost runs only derived roots with aggregate step/deadline budgets.
- Per-instruction permissions constrain register, direction and width; I2C payloads
  and exact board rows remain tied to the private image. Hardware backends refused.
- Extracted shared BoardPolicy identity/rules; all six ADR permissions unchanged.
- Alternate GPIO remains denied. No caller view can mutate the owned snapshot.
- Updated source-bound generated reports; prior 20-access board trace still matches.

Validation: make check passes. Synthetic parser: 37 checks, zero failures.
Policy tool suite: 5 tests pass. Compiled comparison: 34,128 queries match
777 allowed tuples (218 read, 559 write), across 530 potential starts/eight roots.
Artificial 32-scenario matrix: 16 complete, 16 stop at denied GPIO 0x89c2.
Fault cases cover mutation, missing/failed selection, I/O, timeout, clock rollback,
budget exhaustion, failed-execution retry and hardware refusal.
Freestanding PostImage/BoardPolicy/SHA cross-compile with 4096-byte frame bound.

No VM/card stage, PCI/BAR, root, reset, binding or push ran. Shared VM tools
were unchanged; no application re-pin needed. Work is committed on main.

The binding is not yet in the permanent owner. BoundPost uses hosted helpers;
its I2C callback is a trusted bounded transaction transport. Native helper/transport
wiring, guest-wide ownership, DMA/visibility, owned VRAM and readiness stay gated.
Permissions do not independently prove write values/order or hardware safety.
No production executor or A7 claim follows.
Next: S1HELPERS freestanding guarded board helpers.
