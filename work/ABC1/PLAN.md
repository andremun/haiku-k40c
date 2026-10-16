# ABC1: user-directed cardless continuation

2026-10-16. The user explicitly requested completing what is possible across
tracks A/B/C and reporting at the end. This supersedes the one-task-per-session
stop rule for this bounded continuation. No hardware access/push/subagents.

1. Rework A3 from the genuine ROM/independent decoder/log, without reading the
   reviewer implementation or using rejected branch output. Inspect and explain
   disagreements with exact source/ROM evidence; do not infer missing bytecode.
2. Specify the executor/environment and implement/test the safe, source-backed
   subset possible without board decisions, recording unimplemented semantics.
3. Implement the memory/address/publication ownership boundary and host tests.
4. Advance the Haiku backend/tooling as far as a cardless build/test environment
   permits; restore it if practical without host sudo.
5. Decode the initialization trace into named evidence and define the ordered
   machine-specific recipe with domains/waits/faults/rollback. Implement/test
   reusable orchestration without fabricating unknown register sequences.
6. Run full checks for each substantive stage, record exact inputs/results,
   update the actual A/B/C plan states, commit locally, report precise remaining
   gates. Hardware readiness/S1 and A5 user decisions remain unclaimed.
