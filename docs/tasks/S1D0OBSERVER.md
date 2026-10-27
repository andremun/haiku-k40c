# Macro task S1D0OBSERVER: source-checked host observation boundary

## Why

D0 needs actual VFIO ioctl outcomes and mapping lifetimes, not QEMU's earlier RAM
announcement. S1DMAMODEL supplies typed coverage checks. Establish a concrete
observer format and its identity/completion rules before building a device stage.

## Inputs

Read docs/STATUS.md, docs/DMA-CONTRACT.md (D0), docs/DMA-MODEL.md,
work/S1DMAMODEL/RESULT.md and ADR 008. Use tools/dma_model.py and its tests.
Identify the installed observer version and narrow primary source decoder paths.
Record exact source/version/hashes outside reference/. Do not guess trace grammar.

## Outputs

- Plan a bounded owned-child observer/normalization boundary. Record container FD
  identity/lifecycle, launch identity, setup backend, syscall completion/return,
  mapping extents/permissions and actual returned unmap size.
- Check grammar against exact source and harmless owned-process fixtures where
  possible. No VFIO device or guest. A fixture may issue an inert ioctl to
  /dev/null solely to verify failure decoding, never to a GPU/VFIO node.
- Reject truncated, restarted, interleaved/unfinished, unknown and ambiguous input.
  Reused fds cannot inherit mapping identity. Tie coverage to a complete cutoff.
- Build host tests for source-checked format, malformed inputs and model handoff.
  Keep parsed/fixture results diagnostic and publication denied. Source pins and
  generated fixtures/reports need exact --check support if they write output files.
- Identify observer/launcher and guest-probe requirements for the next D0 package.
  Do not silently extend B5, install a provider or claim physical visibility.
- Update licensing, status and work records. Run make check and commit on main.

## Limits

Host observer/source/fixture work only. No guest, VFIO device, PCI/BAR, root,
binding, reset or process attachment. Hardware approval persists under ADR 008
for later ready stages. ADR 006 still controls any launcher-reported stop.
