# Plan

1. Add a private physical-window transaction using owned VRAM tokens and explicit
   UC profile, with selector/data serialization and no cached-selector assumption.
2. Bound bulk work and flush polls; separate CPU ordering from the BAR protocol.
3. Stage zeroed objects and two address-dependent/complement data pages; verify
   only after all writes. Keep table updates private to the future Mapper.
4. Exercise independent physical storage, alias and window/chunk-boundary faults,
   cross-compile, source-bind reports and run all checks. No guest/card.
