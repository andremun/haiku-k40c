# S1A6 result — 2026-10-27

DONE for host scope. Grouped macro review remains pending.

- Added tools/devinit_closure.py and deterministic analysis/devinit_closure.json.
- Audited POST roots, BIT-I/M, RAM mapping, condition/macro spans, register
  operands, shifts, generated ranges, table overlap and board-table inputs.
- Bound board permissions to ROM digest, offset and opcode. Six rows stay allowed;
  the GPIO at 0x89c2 stays denied if changed conditions enable it.
- Approved image: 530 potential starts, 25 opcodes, 438 register references,
  349 distinct registers, eight RAM groups, zero unresolved reviewed-input issues.
- Added host-only DedicatedI2c with explicit initialization, descriptor matching,
  MSB-first transfer, ACK/NACK, bounded stretching, deadline/clock/budget guards.
- Preserve primary and STOP cleanup errors. No retry or recovery pulses.
- Reject physical backends and shared/PMGR bus descriptors.
- Added wire-transition decoder and every-callback failure injection tests.
- Added malformed/table/policy/strap mutation and no-write --check tests.
- Integrated audit generation check under the existing private-ROM CI gate.
- Updated executor/prestart/recipe/plan documentation, licensing and provenance.

Validation: make check passes. I2C UBSan suite: 908 checks, zero failures.
Input audit suite: 10 tests pass. Generated checks and existing policy tests pass.
No VM/card stage, physical access, root, reset, binding change, or push ran.

SOURCE_ONLY timings use the optional Linux internal algorithm. Capture choice
remains UNKNOWN. Input coverage does not prove feasible paths or termination.
The report always denies production eligibility. Native input binding, live
RAM selection, register policy, persistent owner, DMA/visibility, VRAM ownership
and independent readiness remain gates. No production executor/A7 claim.
Next host task: S1NATIVE persistent owner and DMA contract.
