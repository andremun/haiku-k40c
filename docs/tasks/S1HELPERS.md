# Macro task S1HELPERS: freestanding guarded board helpers

## Why

S1POST's immutable binding and register policy compile freestanding. BoundPost
still depends on hosted BoardHelpers. Remove that dependency before native owner
integration while preserving the exact board policy and hardware refusal.

## Inputs

Read docs/STATUS.md, docs/POST-BINDING.md, docs/DEVINIT-EXECUTOR.md,
work/S1POST/RESULT.md and ADR 004. Use current Board/BoardPolicy/BoundPost/I2c
sources and tests. Follow only the already cited GPIO/CCB/IO/helper source ranges.

## Outputs

- Separate freestanding transport/view/helper interfaces from the hosted legacy
  adapter. Replace dynamic helper storage with bounded owned/caller storage.
- Compile/link the bound interpreter and helpers freestanding with no exceptions,
  RTTI or dynamic allocation. Keep all hardware backend gates intact.
- Preserve GPIO duplicate/default/exclusion/routing semantics, IO skipped waits,
  and exact I2C descriptor/payload handling. Check pin-register operations through
  the bound policy when wiring the dedicated host I2C candidate.
- Host regression/fault tests and independent generated policy/trace comparisons.
- Update licensing/provenance, documents, status and work/S1HELPERS records.
  Run make check before commit. Do not claim native execution from linking.

## Limits

Host/source work only. No VM, physical card, PCI/BAR, root, reset, binding or push.
Do not expand ADR permissions, expose mutable ROM storage, or infer readiness.
Owner integration, verified DMA/visibility and A7 permission remain separate gates.
