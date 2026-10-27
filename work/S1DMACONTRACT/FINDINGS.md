# S1DMACONTRACT findings

- KNOWN current inventory: QEMU 6.2+dfsg-2ubuntu6.31, Linux 6.8.0-138-generic.
  The B5 evidence has no QEMU executable hash/version. Current identity cannot be
  retroactively bound to that historical launch. Its requested topology is saved.
- Exact Ubuntu QEMU orig/patch archives match official DSC sizes and SHA-256.
  dpkg-source applied the full patch series outside reference/. Signature was not
  checked. Four patched source files plus patch series have individual hashes.
- Pinned Haiku source confirms contiguous low guest storage and physical-map
  queries. Normal-RAM page-table flags support a cached candidate, not live PAT,
  MTRR, KVM/host memory-type or device coherency proof.
- QEMU's ordinary RAM path maps its section address-space offset as VFIO IOVA,
  with a separate QEMU host pointer. No selected guest IOMMU function yields the
  global memory address space. GPA/IOVA equality is therefore INFERRED under that
  configuration, not verified for a live extent. No identity provider was added.
- The RAM trace event occurs BEFORE vfio_dma_map/ioctl success. A future observer
  must capture actual map results and complete interval lifetimes, not accept that
  trace line as success. QEMU's internal EBUSY recovery includes unmap/retry.
- Linux v6.8 baseline maps pinned host PFNs with IOMMU_CACHE and conditionally
  enables enforced coherence. This is not the exact Ubuntu -138 source or a live
  VFIO_DMA_CC_IOMMU result. Those gaps remain UNKNOWN.
- Existing source supplies barriers, a DMA-mapped flush target and BAR completion,
  but no defined host-page payload response for a self-checking pre-POST transfer.
  No sentinel effect, coherency proof or bare BAR-flush safety was invented.
- D0 is a proposed new read-only mapping-observation stage, not B5. It would test
  structural runtime map coverage. D1 is a separate conditional first-write target/
  flush experiment with limited observations, not a complete payload proof.
  Neither is implemented, authorized or ready for approval. Exact prerequisites,
  fault baselines, trusted evidence handoff and visibility protocol remain gates.
- tools/dma_contract.py generates source/evidence metadata and exact --check text.
  Fourteen external file pins verify. Stale output is rejected unchanged, matching
  output accepted unchanged, and a tampered external source is rejected.
- The source audit needs no new root-readable data. Future physical baselines may
  require a user step. No root request is fabricated just to make this audit pass.
- Final make check exits 0. Repository checks report zero failures, exact reference
  pins are clean, and all source/generator comparisons and host suites pass.
  The new repository-only evidence --check also passes. Full log: check-final.log.
- Driver, provider and launcher implementations did not change. No shared VM tool
  or sibling application pin changed. No VM/card or physical mapping was run.
