# Macro task S1DMACONTRACT: source and evidence closure for DMA publication

## Why

S1OWNERPOST connects resident image/latch state in host tests. The default-denied
DMA provider remains the main pre-POST integration gate (Q7). Establish what source
and existing evidence can prove before implementing a provider or requesting a
physical verification stage.

## Inputs

Read docs/STATUS.md, docs/NATIVE-OWNER.md (DMA proof obligations),
docs/OWNER-POST.md, docs/S1-INTEGRATION-CHOICES.md and Q7 in docs/OPEN_QUESTIONS.md.
Use the current NativePool/HaikuMemory contract and approved launcher configuration.
Use saved launch/capture evidence only as it is documented. Follow narrow relevant
Haiku DMA/allocation/cache and QEMU/VFIO guest-RAM mapping source ranges. Record
exact version/hash/URLs for any additional primary source. Do not modify reference/.

## Outputs

- Record the investigation plan, then map the complete candidate address chain:
  CPU pointer, guest physical extent, VFIO/QEMU guest-memory mapping and device IOVA.
  Distinguish requested configuration, source behavior and runtime verification.
- List aperture, alignment, lifetime, invalidation and CPU/device visibility
  obligations. Do not infer coherency, identity IOVA or safe bus mastering merely
  from allocation, KEEP_LOADED, QEMU command options or successful CPU readback.
- Identify which facts are KNOWN/SOURCE_ONLY, INFERRED or UNKNOWN, with exact
  citations. Retain any contradictory evidence and stop under the escalation rule.
- Specify a bounded provider interface only to the extent supported by evidence.
  Keep publication denied and add no physical callback implementation or override.
- Prepare a concrete, reviewable design for the smallest separate verification
  stage, including owned storage, bounded effects, fault baseline, success limits,
  quarantine/cleanup, and exactly which user permission it would require.
  Do not execute it or imply approval. Separate further write stages from B5.
- Record missing root-readable facts as exact read-only user commands in
  docs/REQUESTS.md only when necessary. Continue independent source work.
- Update Q7, status, licensing, provenance and work records as applicable.
  Run make check before committing on main. No push.

## Limits

Host/source/design only. No VM, physical card, PCI/BAR, root, binding, reset,
provider publication or DMA experiment. No permissions expand. The bus-master
bit observed by B5 is an existing fact, not a grant to perform DMA.
