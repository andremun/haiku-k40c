# Macro task S1POST: immutable execution binding and register policy

## Why

Host input closure, board semantics and native owner lifetime are now established
within their stated scopes. The executor still accepts caller-supplied table
pointers and a hosted policy adapter. Bind native-safe inputs before hardware work.

## Inputs

Read docs/STATUS.md, docs/DEVINIT-EXECUTOR.md, docs/NATIVE-OWNER.md,
docs/S1-PRESTART.md, work/S1A6/RESULT.md and work/S1OWNERTEST/RESULT.md.
Use current Interpreter/Board/Sha256 sources, devinit_closure.py and the exact
external ROM. Follow only the selected pinned init/table/register-wrapper ranges.

## Outputs

- Define and implement a freestanding immutable POST-input binding with owned
  storage and bounds, exact ROM identity, table/root selection and cached RAM
  selection requirements. Do not commit firmware bytes or trust a caller digest.
- Derive and validate read/write operation permissions for selected core/table
  inputs and helper effects. Preserve ADR 004's six exact rows and the denied
  alternate GPIO. Encoded/contextual register handling must fail closed.
- Host tests for mutation, wrong images/pointers, missing live inputs, malformed
  spans, alternate conditions and permission refusal. No hardware backend.
- Document the remaining native executor/owner integration, DMA/visibility and
  readiness work. Update provenance/licensing, status and work/S1POST records.
  Run make check before commit. Cross-compile new freestanding code where supported.

## Limits

Host/source work only. No VM, PCI/BAR, physical card, root, reset, binding or push.
No verified mapping or readiness from a ROM hash, compiler fence or software latch.
No changes to ADR permissions. A7 remains separately reviewed and user-authorized.
