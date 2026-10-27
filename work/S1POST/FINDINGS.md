# S1POST findings

- Added owned, noncopyable exact-ROM binding; input hash is computed after copy.
  Roots/tables are internally derived. A source-buffer mutation cannot change them.
- Freestanding layout inspects all 530 potential starts and eight POST roots.
  Caller tables/roots/index/flags do not enter the bound execution API.
- RAM selection attempts one simulated strap read and caches the mapped group.
  Failures cannot silently reread the strap. No hardware access occurred.
- Per-instruction policy derives read/write/width permissions for core/table/helper
  operations. Independent tool matches 34,128 queries against 777 allowed tuples.
- Exact six-row ADR 004 permission identity is shared in freestanding BoardPolicy.
  The alternate GPIO at 0x89c2 stays denied when conditions enable it.
- Artificial 32-scenario matrix: 16 complete, 16 denied at that GPIO, as intended.
  No hardware initialization or production-compatibility claim follows.
- Binding/policy/SHA sources cross-compile freestanding with a 4096-byte frame
  warning treated as error. Large snapshot/layout belong in persistent storage.
- Host adapter remains hosted through BoardHelpers. The I2C callback is a trusted
  transaction transport; physical wiring/visibility and owner integration stay gated.
- Original board trace facts remain unchanged; generated hashes are refreshed for
  the extracted shared permission source. No VM, PCI/BAR, root, reset or push ran.
- Full make check passes with zero failures. Synthetic parser has 37 checks and policy-tool suite has 5 tests. All original helper/trace checks pass.
