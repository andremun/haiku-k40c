# Host review batch, 2026-10-27

S1B5 was accepted separately. This batch continues under ADR 007.
No physical card stage ran in this batch. The B2 VM had no GPU.

| Macro task | Main implementation | Result |
|---|---|---|
| S1BOARD | 4856782 | Exact ROM policy, board helpers and offline trace comparison |
| S1B2 | 54db484, ed67895 | Native DMA32 adapter and passing cardless memory probe |
| S1A4 | ebb1604 | Selected cold preinit model and persistent caller-owned one-shot state |
| S1C2 | This handoff | Source-backed integration choices and old design corrections |

Read each work/<ID>/RESULT.md, then its PLAN/FINDINGS and required task outputs.
Tests and source-derived reports are host evidence. B2 cardless evidence is
results/20261027-b2-native-memory/. It does not prove device IOVA or GPU access.

Review focus: exact six-instruction ROM policy; publication/release failures;
quarantine lifetime; one-shot owner persistence requirements; selected callback
ordering; separation of source choices from hardware proof. Physical I2C,
native lifetime integration, whole-program executor closure, DMA/VRAM/readiness
and quiescence remain open. No write stage is ready for approval.

Shared VM files were re-pinned in haiku-k40c-llm at 3b9b7e7 to owner 54db484;
its checks passed. A4/C2 change no shared VM file and need no new pin.
No push or remote branch deletion was performed.
