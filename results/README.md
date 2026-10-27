# Results

Evidence that is not a generated task output. Task outputs stay in `hardware/`,
`analysis/`, `registers/`, `firmware/` and `work/`. Reference captures stay in `reference/`.

| Folder | Claim | Cited by |
|---|---|---|
| `20261018-esc001-native-load/` | The cardless probe links against the guest kernel and loads (`k40_os: PASS`) on a KVM Haiku hrev60207 guest. Cardless, not K40c evidence. | `escalations/ESC-001.md`, `docs/STATUS.md` |
| `20261027-s1a-cardless/` | Pending S1A cardless KVM check passes. No GPU evidence. | `work/S1B5/RESULT.md`, `docs/STATUS.md` |
| `20261027-b5-identity/` | Attempt 02: PMC_BOOT_0 = 0x0f1240a1 under Haiku, identity only (HARDWARE_VERIFIED). First attempt preserves a host-parser false alarm. | `work/S1B5/RESULT.md`, `docs/STATUS.md` |

The folder came from `opencode-haiku/results/t7610-20261018-driver-native/` (commit `dcfd6f2`)
on 23 October 2026 with unchanged bytes. `hashes.txt` lists the file hashes.
