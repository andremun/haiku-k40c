# S1A4 findings

- KNOWN: GK110B selects GF100 devinit; preinit and POST precede TOP parsing.
  Source and observed lifecycle anchors are in docs/S1-PRESTART.md.
- SOURCE_ONLY: host helpers model IRQ unarm, CRTC unlock, seven private-ring
  masks, dedicated NVIO I2C init, flush-page encoding, and cold FIFO reset.
- Host startup requires verified published IOVA, pins it, and retains the pin
  after partial failure. It rejects physical transports and warm state.
- OncePerBoot handles reentry and controller recreation only when the caller
  preserves its owner. Native driver reload persistence is still UNKNOWN.
- Dedicated I2C wire transfer is not implemented. The internal Linux algorithm
  is build-conditional; the capture configuration is UNKNOWN.
- No physical memory-readiness, GR omission, or quiescence claim follows.
- Focused UBSan host test: 228 checks, 0 failures.
- Injected failure at every one of the 29 register/byte transactions; later steps stop.
- Initial check overlapped a temporary test bound error and sandbox-blocked local HTTP tests. Corrected the bound to 29 accesses; full check outside the sandbox passes.
