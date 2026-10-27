# S1HELPERS result — 2026-10-27

DONE for freestanding helper/host wiring and native link scope. Review pending.

- BoardCore separates freestanding interfaces/helpers from the hosted legacy adapter.
- GPIO uses bounded storage for all 255 possible records. Duplicate/default,
  exclusion/routing semantics and skipped IO waits remain unchanged.
- BoundPost DedicatedPins mode wires the source-only I2C candidate through the
  current instruction's register/width/direction policy. No transaction callback.
- Explicit prepareI2c derives one dedicated bus and separately writes init value 7.
  Preparation is once per image, including failure. POST never initializes the bus.
- The default trusted transaction-callback mode remains for existing simulations.
- Hardware backends remain refused in both modes. No ADR permissions expanded.
- Clock/timeout/budget failures propagate without becoming generic I/O errors.
  Sticky bound failures block further cleanup effects. Recovery is not established.

Validation: make check passes. Board helpers: 577 checks. Standalone I2C: 908.
Independent comparison: 34,128 queries match 777 allowed operation tuples.
Existing 32 scenarios retain 16 completions and 16 intended GPIO denials.
Dedicated pin profiles: one completion, one intended denial, ten fault cases.
Wire payloads match the three approved writes, with no pin-policy bypass or
transaction callback. The 20-access trace and conservative input closure pass.
Full seven-unit native cross-link passes without exceptions/RTTI/allocation,
with 4096-byte frame warnings as errors. Evidence: native-link.log, native-hashes.log.
The sized-delete import is compiler-emitted for virtual destructors, not allocation.
This link-only library has no stage/driver entry point and was not loaded.

No VM/card, root, PCI/BAR, reset, binding or push. Shared VM tools unchanged.
Owner/guest-wide integration, physical transports, DMA/visibility, VRAM and
readiness remain gated. No native execution, GPU or A7 readiness claim.
Next: S1OWNERPOST persistent owner POST binding.
