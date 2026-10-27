# S1D0OBSERVER findings

- The installed strace is 5.16-0ubuntu3. Exact Ubuntu archives match DSC size/hash
  fields; extraction applies Ubuntu patches. DSC signature was not checked.
- Its ioctl.c has no VFIO argument decoder. The RAM pointer alone cannot establish
  mapping extents/permissions. No parser was built that invents missing pointees.
- A separate userspace observer now includes an original narrow Type1 payload
  decoder. The existing strace syscall-return machinery supplies actual outcomes.
  SETUP/MAP/UNMAP inputs and successful unmap returned-size are explicit markers.
- The first build hook matched an earlier command-number switch without an arg
  variable. Compilation rejected it. The hook now uses the unique argument-decoder
  context. The corrected build passes; the first generated source remains under
  ignored build/observer/first-ioctl.c. No VM launcher or hardware retry occurred.
- The owned-child fixture opens only /dev/null. Actual SETUP/MAP/UNMAP calls all
  return ENOTTY. The decoded structs match source and expose no false success.
  Actual raw trace is null-trace.log. No VFIO device was opened or traced.
- The strict path-filtered stream boundary tracks original FD open/close/reuse,
  fixed single-process identity, backend setup, complete outcomes and model cutoff.
  Unknown requests, duplicates, incomplete/restarted/injected records and layout
  mismatches close coverage. Other processes/threads require separate fd-table
  proof; this boundary rejects them instead of guessing shared descriptor identity.
- Eight unit tests pass. Positive histories replace strings only in memory and
  are explicitly synthetic. Actual ENOTTY trace cannot produce mapping coverage.
- Group-to-container/device association, realized DMA address space, live evidence
  cutoff/guest handshake and fault baselines remain D0 package requirements. This
  observer does not authenticate evidence, verify DMA or install a provider.
- Final make check exits 0. Repository/reference/source checks and every host suite
  pass. Existing source-bound owner report was regenerated for the test build list.
  No shared VM file changed, so no sibling application tool re-pin is required.
- Pinned strace documentation offers -D to preserve the tracee as the launcher's
  direct child. The D0 package should validate that mode with an owned-child test
  so the independent watchdog targets QEMU itself rather than only its tracer.
