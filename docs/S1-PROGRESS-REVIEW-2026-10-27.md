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

## D0 attempt and present gate

The user started the R5 stream. Its reviewed updates and host tests pass.
The exact current command is in docs/REQUESTS.md and docs/D0-STAGE-REVIEW.md.
The stream saves one kernel control entry and the retained/live filtered classes.
The first physical D0 attempt stopped after 124.63 s on an unproved second task's
mapping. No native extent, cutoff or probe output was attested. S1 is incomplete.

The next prerequisite is owned thread/FD-table lineage proof. Do not accept
arbitrary TIDs just to pass. No modified retry occurred. ADR 006 requires explicit
user go-ahead before another run. The filtered before/after logs match, which
establishes no new captured filtered line, not a clean complete kernel log.
Evidence and exact hashes are in results/20261028-d0-mapping/.

## Remaining path

D0 must first observe actual structural coverage for retained native storage.
After D0, prepare native POST integration and an A7 package for an explicit
per-run yes. D1 and its separate DMA/publication questions follow POST. Do not
build more mapping or visibility machinery before A7. Neither an address equality nor a BAR completion bit proves payload
visibility. Native POST, VRAM ownership, readiness and the selected FIFO path
still need concrete integration and physical verification. S1 requires a consumed
NOP with GET advancement, no faults and source-backed teardown.

Do not interpret the number of host tests, source pins or linked objects as S1
success. Keep unknown physical behavior labeled UNKNOWN until captured.
