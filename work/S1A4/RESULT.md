# S1A4 result — 2026-10-27

DONE for the host candidate scope; grouped review pending.

- Followed selected GK110B callbacks through construction, preinit, and POST.
- Added docs/S1-PRESTART.md with source anchors, observed order, and omissions.
- Added host-only cold startup controller with atomic caller-owned once-per-boot state.
- Reentry, controller recreation, and all failed attempts cannot run startup twice.
- Require published verified device IOVA; retain flush-page pin after partial failure.
- Added selected IRQ/CRTC/private-ring/I2C-init/FB/FIFO register helpers.
- Reject physical transports, shared I2C pads, warm state, and bad page encoding.
- Bound callback sequence by monotonic deadline; callbacks must themselves be bounded.
- Host tests cover ordering, each transport failure, every callback failure,
  prerequisites, timeouts, clock rollback, duplicate startup, and quarantine.

Validation: make check passes; focused UBSan test: 228 checks, 0 failures.
Source provenance and licensing updated. No VM or card stage ran.

SOURCE_ONLY mechanics do not prove hardware readiness. Physical I2C transfer,
whole-program ROM/helper closure, native boot-persistent owner, verified DMA,
VRAM ownership, and independent readiness remain gates before A7.
No write permission, root operation, reset, or push was used.
Next: S1C2 host integration choices under ADR 007.
