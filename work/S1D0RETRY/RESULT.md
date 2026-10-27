# S1D0RETRY result: D0 PASS (structural mapping only)

One authorized retry passes in 110.5 s. Command:
`python3 tools/haiku/d0_run.py`. Exact source/artifact hashes and argv are saved
in results/20261028-d0-mapping-retry-01/launch.json.

KNOWN from serial.log:887-907: allocation GPA 0x15e4000, 4096 bytes, token 1.
Lease 1 detaches retaining it. Lease 2 sees the same quarantined native extent.
Publication stays denied. B5 reads PCI command 0x0007 and identity 0x0f1240a1.

The live cutoff binds the owner extent, approved device/group, supported backend,
realized topology and complete READ/WRITE API map coverage. Worker calls carry
syscall-stop TGID/KCMP_FILES proof. Saved cutoff/hash/topology/map replay passes.
The full selected shutdown trace parses. No final explicit VFIO close is captured.
Process exit ends live authority outside the passive supplied-record ledger.
No QEMU guest remains. Filtered before/after logs match. No new filtered line
was captured. This is not a claim of a clean complete kernel log.

D0 does not prove physical payload, cache coherency, native POST, GPU quiescence,
or S1. No provider is installed and no IOVA is published. Q7 remains open.
The first failed capture is unchanged. No additional retry occurred.

Full make check passes in check-final.log. No root or push was run.
Review: docs/D0-STAGE-REVIEW.md and docs/S1-PROGRESS-REVIEW-2026-10-27.md.
Next: native POST integration and an A7 package. A7 requires an explicit yes for
one run. D1 and further DMA/visibility work follow POST, as Claude advised.
