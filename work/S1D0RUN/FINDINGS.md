# S1D0RUN findings

- Claude accepts S1BOARD through S1D0PACKAGE, with the scope stated in the supplied
  review. ADR 008 was corrected in bdc6317: read-only approval only. Each write
  stage needs an explicit yes for one run.
- The initial user-started reader is live. Its output file is empty and its grep
  pattern omits AER/PCIe classes. No guest was launched. Requested a corrected
  pipeline with the full review filter and -n all for the current boot baseline.
- The development card's sysfs ancestry identifies root port 0000:00:03.0.
  Only sysfs topology was read. No host binding or device register was changed.
- The journal diagnostic confirms a functioning kernel journal, but the selected
  classes have no retained output. The user approved and started a control-entry
  prefix plus filtered follow command. D0 --check passes with a 296-byte baseline.
- The watcher records limited filtered scope, uses the home path or K40_KERNEL_LOG,
  and stops on every new AER/PCIe Bus Error line. It pins the exact full-pattern
  grep process writing the same inode, so filter loss closes the gate immediately.
- Six journal-gate tests and six orchestration tests pass, including SIGPIPE,
  direct filter exit, root-port/card AER and the one-line missing-R5 diagnostic.
- First physical D0 run stops after 124.63 s. The first rejected record is trace
  line 104: task 1617915 successfully maps 16 MiB at IOVA 0xc0000000 through
  container FD 21. The owned QEMU PID is 1617905. The strict observer correctly
  denies the unproved second task's shared-FD history. Capture: KNOWN.
- INFERRED: task 1617915 is a QEMU thread. Its thread group and shared FD-table
  lineage were not captured, so they remain unproved. Do not admit arbitrary TIDs
  or normalize them to the main PID merely because the syscall uses the same FD.
- The saved stream also contains successful main-task setup/maps, device FD 23
  for 0000:04:00.0, and subsequent mapping changes. These are API observations,
  not an attestation of the native allocation or physical payload visibility.
- No guest probe output exists (serial.log is empty), no extent/cutoff was
  attested, and publication remains false. No physical D0 or S1 pass is claimed.
- kernel-before.log and kernel-after.log are byte-identical. KNOWN: no new line
  appeared in the filtered stream during this run. This is not a clean-kernel
  claim. No QEMU guest remains. No modified retry occurred under ADR 006.
- Next prerequisite is a bounded proof of owned task/FD-table sharing before a
  thread-aware parser can accept these mappings. A revised package and explicit
  retry go-ahead are required. A7 follows a successful D0, not more DMA machinery.
