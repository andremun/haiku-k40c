# Macro task S1NATIVE: persistent native owner and DMA contract

## Why

S1A6 has a host POST input audit and bounded I2C candidate. The native probe
still lacks a boot-persistent startup/allocation owner and verified publication.
Close the host/source design and implement only contracts supported by evidence.

## Inputs

Read docs/STATUS.md, docs/HAIKU_BUILD_TEST.md, docs/MEMORY-CONTRACT.md,
docs/S1-PRESTART.md, docs/DEVINIT-EXECUTOR.md, and work/S1A6/RESULT.md.
Follow src/os/HaikuMemory.*, src/memory/Memory.*, src/runtime/PreStart.*,
and the selected Haiku module/driver lifetime interfaces in the pinned tree.
Read the guarded launcher's fixed IOMMU/guest configuration before evaluating
any proposed DMA contract. Do not assume GPA equals device IOVA.

## Outputs

- Document the selected persistent-owner and module unload behavior, with sources.
- Implement and host-test the owner where its lifetime can be established.
- Specify mapping/visibility proof required by any native DmaProvider; keep the
  default denied until that proof exists. Record exact missing evidence.
- Cross-compile native changes using the matching kernel. No VM or card run.
- Update licensing/provenance, status and work/S1NATIVE/{PLAN,FINDINGS,RESULT}.md.
  Run make check before commit.

## Limits

Host/source work only. No VM, physical card, PCI write, BAR, root, reset,
binding or push. Do not grant a verified mapping from a guessed identity
conversion or module flag. A7 and physical transport integration stay gated.
If native code cannot safely preserve state, fail closed and document the blocker.
