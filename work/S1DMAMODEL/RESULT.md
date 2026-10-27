# S1DMAMODEL result — 2026-10-27

DONE for bounded host evidence-model scope. Grouped review pending.

- Fixed launch/device/container/generation identity and successful backend setup.
- Typed contiguous complete observations; bounded records/events and 64-bit extents.
- No map coverage from announcements, failed maps or incomplete histories.
- Separate source-backed Type1/V2 whole-record unmap rules, checked returned sizes,
  holes, original boundaries and EBUSY/unmap/retry observations.
- Conservative invalidation for failed/unlocated removal, overlap and ambiguity.
- Independent GPA/IOVA/HVA fields. Immutable cutoff witnesses stale after every event.
  No provider token, verified bit, authentication or publication authority.

Validation: ten host tests pass, including a seeded independent page-set oracle
with 500 updates. make check passes. Existing source-bound reports regenerated
where their test-build input changed. No driver or physical launcher was changed.

The user approved hardware access during this task. ADR 008 records planned S1
hardware authorization on 04:00.0, retaining isolation, root/review/stop rules.
This task used no guest, ioctl, device, PCI/BAR, root, binding, reset or push.
No live address, coherency or payload proof follows. Q7 remains open.
Next: S1D0OBSERVER host observation/source/fixture boundary, then a concrete D0
package if its prerequisites close. Continue task-by-task under the user's request.
