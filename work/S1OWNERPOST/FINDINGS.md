# S1OWNERPOST findings

- NativeOwner reserves aligned PostImage storage in its resident module object.
  No large image is placed on a kernel stack. One exact-size copy is constructed
  by placement new, and its internal snapshot/layout never leave the owner.
- A valid lease, Fresh state and no quarantine are required to bind. Invalid
  extents do not consume the slot. A wrong exact-size identity is retained as a
  rejected attempt and cannot be replaced after client detach/reacquire.
- OwnerPostInfo is copied diagnostic state. A small BoundPost adapter exists only
  during the synchronous host simulation. No provider/transport/callback pointer
  is stored after that call. Resident image, selection, result and latch persist.
- simulatePost is absent from the _KERNEL_MODE declaration and implementation.
  Its separate host fixture source rejects kernel compilation. The native C ABI
  remains v1 with no firmware upload, simulation or production startup entry.
- The owner guard spans every callback. The same OncePerBoot latch is consumed
  before selection, dedicated bus preparation or POST. Existing begin cannot
  furnish a second attempt. A scope guard finishes/quarantines on host exceptions.
- Complete means only the recorded host simulation completed. Both successful and
  failed attempts quarantine owned memory immediately and survive new clients.
- The simulation test initially counted all explicit ROM reads of 0x101000 as
  repeated strap selection. That register can also be a decoded POST operand.
  The fixture now separately counts the pre-interpreter cached selection read.
- Native cross-link with the resident image and complete bound core passes.
  The first mixed C/C++ command rejected a C++-only -std option under -Werror.
  The corrected common flags keep -Werror, frame checks and kcc's freestanding,
  no-exception/no-RTTI defaults. No native module has been installed or loaded.
- Final targeted host evidence: nine cases and 6,388 assertions, zero failures.
  This includes an actual blocked callback on another thread: inspection, detach
  and rebinding return Busy until it finishes. No callback/data race is required.
- Synthetic owner binding tests pass without private firmware: 177 checks total.
  Existing owner-client probe tests still pass 13 checks.
- Native header assertions compile. Kernel compilation of the host-only fixture
  is deliberately rejected. Linked symbols contain neither simulatePost nor a
  global constructor. The native ABI table and client source are unchanged.
- Aggregate host-check.json is generated only by tools/owner_post_check.py and
  compares exactly under --check. All evidence remains host/source or compile/link.
- Final make check exits 0. Repository checks report zero failures, exact reference
  pins are clean, all source/generator comparisons and host suites pass. The new
  source-bound owner exercise also compares exactly. Full log: check-final.log.
- No shared VM tool changed. No sibling application tool re-pin is required.
  No VM/card stage, PCI/BAR, root, binding, reset or push occurred.
