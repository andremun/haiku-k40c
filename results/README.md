# Results

Evidence that is not a generated task output. Task outputs stay in `hardware/`,
`analysis/`, `registers/`, `firmware/` and `work/`. Reference captures stay in `reference/`.

| Folder | Claim | Cited by |
|---|---|---|
| `20261018-esc001-native-load/` | The cardless probe links against the guest kernel and loads (`k40_os: PASS`) on a KVM Haiku hrev60207 guest. Cardless, not K40c evidence. | `escalations/ESC-001.md`, `docs/STATUS.md` |
| `20261027-s1a-cardless/` | Pending S1A cardless KVM check passes. No GPU evidence. | `work/S1B5/RESULT.md`, `docs/STATUS.md` |
| `20261027-b5-identity/` | Attempt 02: PMC_BOOT_0 = 0x0f1240a1 under Haiku, identity only (HARDWARE_VERIFIED). First attempt preserves a host-parser false alarm. | `work/S1B5/RESULT.md`, `docs/STATUS.md` |
| `20261027-b2-native-memory/` | Cardless Haiku DMA32 allocation, aligned byte readback, denied IOVA publication, and cleanup pass. No GPU evidence. | `work/S1B2/RESULT.md`, `docs/STATUS.md` |

The folder came from `opencode-haiku/results/t7610-20261018-driver-native/` (commit `dcfd6f2`)
on 23 October 2026 with unchanged bytes. `hashes.txt` lists the file hashes.

| Folder | Claim | Cited by |
|---|---|---|
| `20261027-d0-owner-readiness/` | Enlarged resident owner reload passes in a cardless guest. No GPU evidence. | `work/S1D0PACKAGE/RESULT.md` |
| `20261027-d0-topology-fixture/` | Actual Q35 cardless QMP formatting and bounded owned-child tracing. No GPU evidence. | `docs/D0-STAGE-REVIEW.md` |

| `20261028-d0-mapping/` | First physical D0 attempt stopped on unproved second-task FD sharing. No extent/cutoff or probe output. | `work/S1D0RUN/RESULT.md` |

| `20261028-d0-mapping-retry-01/` | D0 structural mapping cutoff passes for retained storage. No payload/coherency or S1 proof. | `work/S1D0RETRY/RESULT.md` |

| `20261028-a7-post/` | First approved A7 run stopped before request/grant. POST/readiness not reached. Empty filtered R5 delta and host command 0x0002 after exit. | `work/S1A7RUN/RESULT.md`, `docs/STATUS.md` |
| `20261028-a7-fad36717/` | Original immutable launcher evidence for the same single A7 launch. Canonical folder contains identical raw copies. | `results/20261028-a7-post/summary.json` |

| `20261028-a7-post-02/` | Second individually approved A7 run stopped at stream-device open. No request/grant or POST. Shell error captured; empty R5 delta; mastering disabled after exit. | `work/S1A7RUN2/RESULT.md` |
| `20261028-a7-4ac95d19/` | Original immutable launcher evidence for the same second approved launch. | `results/20261028-a7-post-02/summary.json` |

| `20261028-a7-post-03/` | Third approved A7 run stopped at hard-link publication before B5 or native A7. No grant/POST. R5 unchanged; mastering disabled. ESC-003. | `work/S1A7RUN3/RESULT.md` |
| `20261028-a7-c07e1db9/` | Original immutable launcher evidence for the same third approved launch. | `results/20261028-a7-post-03/summary.json` |
