# S1DMAMODEL plan

1. Implement a host-only typed observation ledger. Identity includes launch, device,
   container and generation. Require complete, contiguous observations and an
   explicit successful supported SET_IOMMU before any mapping coverage is possible.
2. Keep original mapping boundaries and independent IOVA/HVA domains. Reject
   overlap/overflow/capacity ambiguity. Failed maps add no coverage. Announcements
   add no coverage. Incomplete or failed-unmap histories invalidate the ledger.
3. Model upstream Type1 and Type1v2 whole-mapping removal separately, checking the
   returned size against the original map records. Do not invent partial byte
   locations from an aggregate returned size. Any later observation stales a witness.
4. Test boundaries, permissions, stale identities/cutoffs, split record removal,
   V1 expansion/zero-removal, failed maps, EBUSY/unmap/retry and exhaustion.
   No raw trace parser, native provider or live ioctl is part of this model.
5. Document source semantics/limits, run make check, update handoff and commit.
   Continue with the next authorized host task. No VM/GPU/root/push.
