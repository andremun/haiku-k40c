# S1 progress for review, 2026-10-27

S1 is incomplete. Only the B5 identity read has real-card evidence. No native
POST, device payload transfer, FIFO NOP consumption or clean physical teardown
has been demonstrated. S2/S3 preparation remains conditional on actual S1 success.

The user authorized sequential tasks, one task per commit, and planned hardware
access. ADRs 007 and 008 record that scope. No push or root command was run.
Claude accepted S1BOARD through S1D0PACKAGE on 2026-10-28. The supplied review
covers the progress document, ADRs, D0 and paths that can reach the card. It is
not a line-by-line review of every batch file. See work/S1D0RUN/CLAUDE-REVIEW.md.

## Review batch

| Tasks | Delivered scope | Evidence and limits |
|---|---|---|
| S1BOARD, S1A4, S1A6 | Board policy, bounded helpers, immutable POST inputs | Source/host tests. No physical executor claim. |
| S1B2, S1NATIVE, S1OWNERTEST | Native allocation and permanent owner | Cardless allocation and retained reload. No device DMA proof. |
| S1POST, S1HELPERS, S1OWNERPOST | Bound POST and resident host integration | Native link and host scenarios. Simulation is excluded from the native module. |
| S1C2 | FIFO setup and lifetime choices | Source design only. |
| S1DMACONTRACT, S1DMAMODEL | Conditional mapping chain and bounded interval ledger | Source and host model. Q7 remains open. |
| S1D0OBSERVER | Exact-source userspace decoder and normalization | Inert owned-child capture. No successful VFIO call. |
| S1D0PACKAGE | Closed mapping stage, native client and live observation checks | Native link, host fault tests, two cardless fixtures. No physical D0 run. |

Each task has PLAN.md, FINDINGS.md and RESULT.md under work/. The status task
log gives its scope. Each task has its own commit. Start the D0 review at
[the concrete stage package](D0-STAGE-REVIEW.md). Its source/artifact SHA-256 values
are generated in work/S1D0PACKAGE/stage.json. The package self-review is explicitly
not a Claude acceptance.

## D0 results and present gate

The first physical D0 attempt stopped on unproved task/FD sharing. The user then
authorized a correction and one retry. S1D0THREAD adds syscall-stop TGID and
KCMP_FILES proof, tested with real shared/private-table threads and a fork.
It also rejects exec/split operations that could change the FD namespace.

The authorized retry passes in 110.5 s. A retained 4096-byte native allocation
at GPA 0x15e4000 has complete structural mapping coverage at the recorded cutoff.
The selected final trace parses and the guest exits. The passive ledger does
not observe implicit FD closure at process exit and supplies no post-exit authority.
The filtered logs match. This is not a claim of a clean full kernel log.
Evidence: results/20261028-d0-mapping-retry-01/ and work/S1D0RETRY/RESULT.md.

D0 proves no physical payload or coherency. Publication stays denied and Q7
remains open. The next package is native POST/A7, not D1. A7 requires an explicit
yes for one run after its concrete command, binaries, writes and limits are ready.

## Remaining path

D0 has observed structural coverage for retained native storage.
After D0, prepare native POST integration and an A7 package for an explicit
per-run yes. D1 and its separate DMA/publication questions follow POST. Do not
build more mapping or visibility machinery before A7. Neither an address equality nor a BAR completion bit proves payload
visibility. Native POST, VRAM ownership, readiness and the selected FIFO path
still need concrete integration and physical verification. S1 requires a consumed
NOP with GET advancement, no faults and source-backed teardown.

Do not interpret the number of host tests, source pins or linked objects as S1
success. Keep unknown physical behavior labeled UNKNOWN until captured.

## Native POST prerequisite decision and package

Claude's supplied 2026-10-28 review resolves ESC-002. The arm-only reference
precedes POST; a readback and second arming write follow POST. D1 stays after
POST and Q7 remains open. S1A7NATIVE implements the distinct retained type,
authenticated same-run structural witness, native owner/physical permit, bounded
readiness and closed single-use launcher. Native cross-links and host fixtures
pass. No A7 guest has run.

The current concrete review packet is `docs/A7-REVIEW-PACKAGE.md`, with source
and artifact hashes, full possible write inventory, stop rules and teardown
limits in `work/S1A7NATIVE/`. Review is pending. A write run still requires an
explicit yes for that exact package under amended ADR 008. S1 is incomplete.
