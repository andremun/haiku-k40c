# S1NATIVE findings

- KNOWN/SOURCE_ONLY: Haiku module.cpp:356-363,2216-2221 adds a permanent
  reference after successful INIT of B_KEEP_LOADED. put_module:2262-2275 cannot
  ordinarily drop that module to zero. This retains initialized state, not just code.
- Legacy unload_driver:463-476 calls uninit_driver then unloads its add-on.
  Driver statics therefore cannot own per-boot startup/quarantine state safely.
- The sparse pinned checkout lacks these two source files. Exact commit
  49a0af9585d80e42240af63ab66e31e9873f59b8 was retrieved from raw.githubusercontent
  into /tmp, without changing reference/. Module source is byte-identical to
  the separate cross-source checkout. Source hashes are recorded in source-hashes.log.
- Added separate permanent owner module with explicit placement construction,
  no destructor/reset/uninit path, serialized bounded entry, exclusive monotonic
  leases, opaque allocation handles, and no external provider/callback storage.
- After attempted startup, detach quarantines all storage. Failed pre-start cleanup
  is also retained. Stale leases/tokens fail. Lost active leases block further use.
- The startup latch was separated from host-only Board/vector includes. First
  cross compile exposed that dependency; freestanding BootState.h fixes it.
- Host tests pass 161 checks. Native module links with --no-undefined against
  matching kernel.so. This is not a module-load or native reload result.
- KNOWN: fixed card_run.py command requests no explicit guest IOMMU device.
  Live VFIO DMA aperture, address equality, cache/device visibility and mapping
  lifetime are UNKNOWN. No DmaProvider installation exists in owner ABI v1.
- No VM/card, PCI/BAR, root, binding, reset or push operation ran.
- Full make check: zero failures. Native kernel.so is byte-identical to the exported kernel except ELF type. ELF has no init/fini-array sections. Shared VM files were unchanged.
