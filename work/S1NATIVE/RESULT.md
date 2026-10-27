# S1NATIVE result — 2026-10-27

DONE for source/host/native-link scope. Grouped review pending.

- Verified pinned Haiku permanent module-reference and legacy unload semantics.
- Added separate KEEP_LOADED owner module and versioned kernel-only C ABI.
- Owner stores pool, one-shot latch and handles; no driver/provider callbacks persist.
- Added exclusive monotonic leases, stale-handle refusal and nonblocking entry guards.
- Retain all storage after attempted startup; quarantine failed pre-start cleanup.
- Added OwnerClient detach-before-put discipline, including busy-close retention.
- Separated freestanding BootState from host-only board/STL dependencies.
- Publication remains denied; no native DMA provider or verified identity cast exists.
- Documented required translation/visibility/lifetime evidence in docs/NATIVE-OWNER.md.

Validation: make check passes. Owner host suite: 161 checks, zero failures.
Pre-start suite: 228 checks, zero failures. Existing allocator/VM-tool tests pass.
Native owner/client sources compile with real headers and link --no-undefined.
ELF exports modules[] without global init/fini constructors.
The link kernel matches the exported guest kernel except ELF type conversion.
Build/source/kernel hashes and logs are saved in this work folder.

The first native compile exposed a host-vector include; extraction fixed it.
The host test initially used a stdio-colliding counter name; corrected before checks.
No source pin or shared VM tool changed. No new application tool pin is needed.
No module install/load, VM/card, PCI/BAR, root, reset, binding change or push ran.

Module residency and owner reload behavior are SOURCE_ONLY until native testing.
Caller-reported startup state is not readiness or permission. DMA/visibility,
immutable execution input integration, owned VRAM and physical bring-up remain gated.
Next: S1OWNERTEST cardless module load/client reload, with ADR 006 stop discipline.
