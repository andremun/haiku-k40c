# Host review batch, 2026-10-27

S1B5 was accepted separately. This batch continues under ADR 007.
No physical card stage ran in this batch. Both B2 and S1OWNERTEST VMs had no GPU.

| Macro task | Main implementation | Result |
|---|---|---|
| S1BOARD | 4856782 | Exact ROM policy, board helpers and offline trace comparison |
| S1B2 | 54db484, ed67895 | Native DMA32 adapter and passing cardless memory probe |
| S1A4 | ebb1604 | Selected cold preinit model and persistent caller-owned one-shot state |
| S1C2 | a833165 | Source-backed integration choices and old design corrections |
| S1A6 | 22865da | POST input audit and bounded host I2C transport |
| S1NATIVE | d9b158f | Permanent owner/client API, host tests and native link; DMA denied |
| S1OWNERTEST | 45923d6 + handoff | Native cardless owner/client reload passes; DMA denied |

Read each work/<ID>/RESULT.md, then its PLAN/FINDINGS and required task outputs.
Tests and source-derived reports are host evidence. B2 cardless evidence is
results/20261027-b2-native-memory/. Owner reload evidence is
results/20261027-owner-reload/. Neither proves device IOVA or GPU access.

Review focus: exact six-instruction ROM policy; publication/release failures;
quarantine lifetime; one-shot owner persistence requirements; selected callback
ordering; separation of source choices from hardware proof. Physical I2C,
production executor binding and physical-reference lifetime, DMA/VRAM/readiness
and quiescence remain open. No write stage is ready for approval.

Latest shared-tool pin: haiku-k40c-llm 0d59079, owner 45923d6.
It includes fixed owner staging and the reload probe. Application checks pass.
This tooling pin supplies no application GPU evidence.
No push or remote branch deletion was performed.
