# 003. End the local agent experiment

Date: 2026-10-23. Status: accepted (user decision).

## Context

This repository had two goals: the driver, and a test of a local LLM coding agent
(Qwen3.6-35B-A3B through llama.cpp and OpenCode) that ran on both K40c cards. The
second goal had three costs. The driver had no card of its own: hardware tests needed
the model moved to one card first. The task protocol was shaped by the small context
of the local model. Agent failures appeared in the project state next to driver
results.

Agent research now has its own project, `optima-agent-bench`, with its own hardware.

## Decision

1. The repository has one goal: the driver.
2. Task work is done with Claude Code and Codex, which run on the T7610 and use cloud
   models. `AGENTS.md` is the shared rule file. `CLAUDE.md` points to it.
3. The K40c at 0000:04:00.0 belongs to the driver. No model process runs on it.
   The K40c at 0000:03:00.0 stays with `llm-server` (mode `one`), which
   `optima-agent-bench` needs.
4. `opencode.json` and `.opencode/` are removed. Their safety rules move to
   `.claude/settings.json` and to the Codex settings in `docs/AGENT-SETUP.md`.
5. The evidence rules, the hardware safety rules, the task files, `make check` and the
   rule that `tools/check_repo.py` is not read during task work stay. They protect the
   correctness of the driver, not the experiment.
6. The rules that only served the local model go: the context-size limits, the ban on
   sub-agents and the model-mode instructions.
7. The record of the experiment stays unchanged: `work/`, the task log and
   `docs/history/20261023-local-agent-experiment.md`.

## Consequences

- Passthrough and hardware tests on 04:00.0 do not need a model switch first. The
  `llm-server` mode must stay `one`. After a reboot the router starts in `dual-t1k`
  and uses both cards, so the user runs `llm-mode.sh one` (see `llm-server`
  `docs/STATUS.md`).
- The trust table of the README changes: new task work comes from Claude Code or Codex
  under the same evidence rules.
- `docs/S1-PLAN.md` and `docs/GATE-REVIEW.md` keep their limits for "the agent". They
  now apply to Claude Code and Codex.
