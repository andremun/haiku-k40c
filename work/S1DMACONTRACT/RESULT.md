# S1DMACONTRACT result — 2026-10-27

DONE for source/evidence and verification-design scope. Grouped review pending.
Q7 remains OPEN. Publication remains denied and no provider was installed.

- Reconstructed exact Ubuntu QEMU source from verified DSC archive hashes.
  Recorded 14 external content pins/URLs plus current host and saved B5 evidence.
- Mapped guest CPU pointer -> GPA -> QEMU HVA/VFIO IOVA -> host physical backing.
  GPA-as-IOVA is a conditional source inference, not a live mapping proof.
- Distinguished cached-RAM candidate, CPU fences, IOMMU_CACHE/enforced coherency,
  GPU cache/BAR completion and physical payload visibility. Unknowns stay explicit.
- Found QEMU's RAM trace precedes map success. Future evidence must capture actual
  ioctl returns and mapping/removal lifetimes. Current B5 has neither that evidence
  nor a QEMU binary hash. The exact host Ubuntu kernel source was not audited.
- Specified a bounded future provider/evidence contract without changing the API.
- Designed D0 structural mapping observation and a conditional D1 flush experiment.
  No justified self-checking pre-POST payload protocol was found. D1 cannot alone
  establish bidirectional visibility or enable a general DMA provider.
- New stage/first-write permissions, prerequisites and fault baselines are listed.
  Neither stage is implemented, authorized or ready for approval.

Validation: make check passes. Exact metadata --check and all 14 external content
pins pass. Negative checks reject stale output and modified source without writes.
All driver/provider/launcher behavior is unchanged. No reference/ content changed.

No VM/card, PCI/BAR, root, binding, reset, DMA publication or push occurred.
No new root data is required for this source audit. No shared VM tool changed.
Trusted evidence handoff, effective coherency, physical payload semantics,
quiescence and provider publication remain gates. Next: S1DMAMODEL host-only
mapping coverage/lifetime evidence model. No A7 readiness follows.
