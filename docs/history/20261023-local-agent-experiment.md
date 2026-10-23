# Local agent experiment (2026-10-05 to 2026-10-23)

Closed by `docs/decisions/003-end-local-agent-experiment.md`. This file keeps the text
that described the experiment. Read-only. Not for task work.

## Purpose, as stated in the README until 2026-10-23

This repository held two experiments:

1. **Driver development.** A Haiku kernel driver that runs one verified compute job on
   a Tesla K40c, built from a study of the open-source Nouveau driver.
2. **A test of a local LLM coding agent.** Most task work was done by a language model
   that ran on the same two K40c cards (Qwen3.6-35B-A3B through llama.cpp and
   OpenCode), one task per session, with a human who read its output. The repository
   was set up to measure how far such an agent gets and where it fails.

## Setup

- OpenCode with the project config `opencode.json` and the commands and review agent in
  `.opencode/` (`/next`, `/handoff`, `/check`, `/escalate`, `/review`). Both are in Git
  history: `git show b913a71:opencode.json`, `git show b913a71:.opencode/command/next.md`.
- The config allowed routine commands, asked before risky ones (sudo, module and PCI
  tools, `git push`, downloads, QEMU, VFIO), denied edits to `reference/`,
  `docs/design/`, `LICENSE` and `tests/accept/`, and denied every read of
  `tools/check_repo.py`.
- Model modes of `~/llm-server/llm-mode.sh`: `dual` (one model on both K40c, default),
  `two` (one model per card, two sessions), `one` (model on 03:00.0 only, 04:00.0 free
  for hardware tests).
- The agent had about 25,000 free tokens of context. `AGENTS.md` had rules for that
  limit: no whole reads of generated files or of source files over 200 lines, notes in
  `work/<task>/FINDINGS.md`, no sub-agents.

## Record

| Item | Where |
|---|---|
| Task outputs of the agent | `hardware/`, `analysis/`, `registers/`, `firmware/`, `work/`, commits that start with a task ID |
| Reviews of each task | `work/<task>/REVIEW.md` |
| Task log with reworks | `docs/STATUS.md` |
| A3: stopped after 17 h, the agent read `tools/check_repo.py` | `docs/STATUS.md`, task log |
| Scaffold reviews and handoffs | `docs/S1-PLAN.md`, `docs/history/` |

The record stays unchanged. Agent research continues in `optima-agent-bench`, which can
use this record as a reference.
