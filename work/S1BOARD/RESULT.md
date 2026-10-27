# S1BOARD result — 2026-10-27

DONE for host scope. Macro review remains pending in the authorized host batch.

- Added the exact six-row ADR 004 policy, keyed by ROM hash, offset, and opcode.
- PolicyBackend owns and hashes the full ROM. Wrong images and payloads fail closed.
- Added IO, ZM_CR, ZM_I2C_BYTE, and GPIO_NE semantic helpers.
- Preserved both skipped IO waits, GPIO exclusions, routing, and duplicate matching.
- Resolved I2C defaults and seven-bit addresses. Missing/NACK transport errors stop execution.
- Both backend transports must be host simulations. The hardware gate is unchanged.
- Recorded Claude's S1B5 ACCEPT and review requirements. ADR 006 requires retry approval.
- ADR 007 permits sequential host work while reviews are pending.
- Recorded all consulted sources and regenerated register provenance.

Validation: make check exits 0. Log: work/S1BOARD/check.log.
The initial provenance-only failure and its correction are retained in check-initial.log.
C++ helper suite: 572 checks, zero failures.
Python tool suite: four tests, including 13 hashlib cross-check inputs.
The external-ROM exercise accepts six policy rows and checks failure and ownership cases.

KNOWN / TRACE_VERIFIED access facts: 20 IO/CRTC accesses match the Linux capture.
Tool: tools/board_trace.py compare_io. Report: work/S1BOARD/trace-check.json.
Skipped IO produces only two 10 ms waits. No register access occurs when skipped.
The comparison uses captured initial read values, not a write replay.

No VM, card, root, binding, reset, or push command ran.
The adapter is host-only. Physical I2C transactions and pre-start bus setup remain open.
A4, native memory integration, C2 choices, and A7 one-shot startup remain separate work.
Next task: native B2 allocation and mapping adapter, under ADR 007.
