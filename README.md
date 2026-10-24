# haiku-k40c

Native Haiku compute driver for the NVIDIA Tesla K40c (GK110B). Design:
`docs/design/design.md`. Specification: `docs/design/specification.md`.
License: MIT (`LICENSE`, `docs/licensing.md`). Changes: `CHANGELOG.md`.

## Disclaimer

This is research code. It is not production code.

I made it as part of a project that tests the Tesla K40c hardware under Haiku. I like
unusual operating systems, and Haiku is an interesting one. That is the main reason this
project exists.

The code is not meant for inclusion in Haiku, HaikuPorts or any other Haiku project.
AI coding agents generated most of it ("vibe coding"). I understand that the Haiku
project does not want such packages, and I do not submit them. If the research is
useful to someone, I am glad.

Use it at your own risk. The license gives no warranty.

## Purpose

A Haiku kernel driver that runs one verified compute job on a Tesla K40c, built from a
study of the open-source Nouveau driver. It is a hobby project. It is not production
software and it may never reach the goal.

Until 23 October 2026 the repository was also a test of a local LLM coding agent. That
experiment is closed (`docs/decisions/003-end-local-agent-experiment.md`). Its record is
in `work/`, the task log of `docs/STATUS.md` and
`docs/history/20261023-local-agent-experiment.md`.

| Part | Written by | Trust |
|---|---|---|
| `AGENTS.md`, `docs/PHASES.md`, `docs/design/`, `.claude/`, `tools/check_repo.py`, `tools/haiku/`, `scripts/`, `reference/pci/` | The user, with Claude (Anthropic) as assistant | Reviewed |
| Task outputs to 2026-10-23: `hardware/`, `analysis/`, `registers/`, `firmware/`, `work/` | The local agent. Commits start with the task ID (`A1: ...`). | As labelled. A claim is KNOWN, INFERRED or UNKNOWN, and a register is SOURCE_ONLY until it is verified. `make check` verifies format and some facts, not completeness. |
| Task outputs from 2026-10-23, later the driver source | Claude Code or Codex, with cloud models. Same commit and evidence rules. | As above |
| `docs/STATUS.md`, `docs/OPEN_QUESTIONS.md` | Both | Check against the task log and the reviews |

Agent output can contain confident errors, including citations of files
that do not exist. Do not use a register value or a command sequence from
this repository on real hardware without checking its source.

## Cards

| Card | Use |
|---|---|
| K40c 0000:04:00.0 | The driver: captures, passthrough (`docs/PASSTHROUGH.md`), hardware tests. No model process. |
| K40c 0000:03:00.0 | `llm-server` in mode `one`, for `optima-agent-bench`. Not for driver work. |

## Working with Claude Code or Codex

Run `claude` or `codex` in this directory. Both read `AGENTS.md` (Claude Code through
`CLAUDE.md`). Setup and permissions: `docs/AGENT-SETUP.md`.

Start a new session for each task. The repository is the memory:
`docs/STATUS.md`, `docs/tasks/<task>.md`, `work/<task>/`. The task steps are in
`AGENTS.md` ("Session protocol"). Claude Code also has them as skills: `/next`,
`/handoff`, `/escalate` and `/review`. Review a branch or pull request with
`/pr-review` ([REVIEW.md](REVIEW.md)).

## Layout

| Path | Content |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Rules for coding agents (safety, evidence, protocol). `CLAUDE.md` points to `AGENTS.md`. |
| `.claude/` | Claude Code permissions and skills: task steps and `/pr-review`. |
| `REVIEW.md` | What a review reports and how severe it is. |
| `docs/` | Status, phases, open questions, requests, design documents. |
| `reference/` | Pinned read-only sources (`MANIFEST.md`) and PCI captures. |
| `tools/` | Analysis scripts and `check_repo.py`. |
| `tools/haiku/` | Cross-compile a Haiku driver on Linux and load it in a test VM (`docs/HAIKU_BUILD_TEST.md`). `setup.sh` builds the toolchain and VM in `~/haiku-cross`. |
| `hardware/`, `analysis/`, `registers/`, `firmware/` | Task outputs. |
| `work/` | Per-task plans, findings and results. |
| `escalations/` | Problems that need a decision. |
| `results/` | Evidence that is not a task output, with an index (`results/README.md`). |
| `docs/history/` | Dated handoffs and old status text. Read-only. Not for task work. |
| `docs/decisions/` | Architecture decision records. |
| `docs/design/layout.md` | Target layout for the next cleanup phase. |
| `scripts/capture_user.sh`, `scripts/capture_root.sh` | Read-only PCI captures: without root, and for the user to run with sudo. Run both after a hardware change, then `tools/hardware_record.py`. |
