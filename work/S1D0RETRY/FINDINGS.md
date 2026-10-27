# Findings

- The user authorized the observer correction and one retry after the first D0
  stop. Correction 002217e passes full checks and includes real shared/private
  FD-table fixture results. Guest artifacts and GPU effects are unchanged.
- The user restarted the R5 stream. The D0 prerequisite check passes.
- D0 passes in 110.5 s. KNOWN from serial.log:887-907: the logical page is 4096
  bytes at GPA 0x15e4000, token 1. Lease 1 detaches retaining it, then lease 2
  observes the same quarantined extent with publication denied. B5 again reads
  PCI command 0x0007 and PMC_BOOT_0 0x0f1240a1. No POST or DMA job ran.
- KNOWN: cutoff.json records group 23, device FD 23, mapping generation 1 and
  complete READ/WRITE map coverage of that extent. The raw prefix hash agrees.
  The selected topology and full trace replay pass. The existing source-selected
  GPA/IOVA identity interpretation remains conditional, not payload proof.
- The complete selected final trace parses. An additional offline assertion
  expecting explicit container closure was wrong: no final VFIO close syscall
  is captured. QEMU process exit ends live authority, outside the passive ledger.
  Do not reuse its supplied-record witness after the VM ends. No forced removal,
  physical payload, coherency or GPU-quiescence proof is inferred from this.
- The launcher completed controlled shutdown, the tracer finished, and no QEMU
  guest remains. Filtered before/after logs are identical. This is not a claim
  about all kernel messages. Evidence: results/20261028-d0-mapping-retry-01/.
