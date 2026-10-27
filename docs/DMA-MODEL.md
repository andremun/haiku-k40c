# Host DMA mapping evidence model

The tools/dma_model.py ledger checks structural coverage in supplied typed
observations. It does not parse a trace, authenticate evidence, prove GPA/IOVA
identity, verify hardware or enable publication. No native API references it.

A ledger has a fixed launch/device/container/generation identity. Container IDs
are observer identities, not reused file descriptors. Only the development card
is accepted. A successful supported backend setup precedes mapping observations.
Sequences start at one and must be contiguous. Incomplete calls, unknown flags,
identity changes and ambiguous results permanently invalidate that ledger.

The model retains at most a configured number of original mappings, not an
unbounded event history. It checks aligned 64-bit extents, HVA extents, direction
permissions, overlaps and event capacity. Successful maps add coverage. Failed
maps and announcements do not. A failed unmap may have partial effects and closes
all coverage. No reset method exists. A new ledger is a new supplied fixture,
not a means to authenticate a new mapping generation.

Unmap semantics follow the pinned upstream Linux v6.8 baseline
vfio_iommu_type1.c:1279-1426. Type1v2 requests must cover complete original maps.
A request can include holes, so its returned size can be smaller than its request.
Type1 can remove an entire original map past the requested endpoint. A request
starting inside the first original map returns zero removal. The model compares
the returned aggregate with the original records, never guesses byte locations
from an aggregate count. Unknown, bisected V2 or contradictory removal closes
coverage. The actual Ubuntu kernel behavior still needs the separate source/live
closure identified by docs/DMA-CONTRACT.md.

A coverage query supplies GPA and IOVA separately and asks for full permissions
across an extent. Adjacent mapping records can cover it. A hole or permission
failure rejects it. The immutable witness contains the cutoff and original map
segments, including HVA. It contains no provider token or verified flag. It does
not establish that the supplied GPA belongs to the supplied IOVA. Any subsequent
observation stales the witness, even an announcement or failed map. current checks
both the cutoff and recomputed structural coverage.

The ten host tests include a seeded 500-step independent page-set oracle,
permissions/domains, lifetime cutoffs, V1/V2 removals, holes, EBUSY/unmap/retry,
failed/incomplete calls, identity/sequence failures, overflow and capacity.
No actual ioctl, process attachment, guest or device file is used.

Run python3 tests/test_dma_model.py or make check. The user's general S1 hardware
approval is recorded separately in ADR 008. This host model does not use it and
does not turn a synthetic history into permission or readiness evidence.
