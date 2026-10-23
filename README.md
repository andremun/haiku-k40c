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

A second question drives the work: can Haiku be a suitable sandbox for AI coding
agents? I do not know of specific vulnerabilities of Haiku for this use. An uncommon
system can also be a useful barrier. This is a question to test, not a claim of
security. The target use is agents that test scientific software, such as GNU Octave,
scientific Python and perhaps R.

Use it at your own risk. The license gives no warranty.

## Purpose: two experiments in one repository

1. **Driver development.** The goal is a Haiku kernel driver that runs one
   verified compute job on a Tesla K40c, built from a study of the
   open-source Nouveau driver. It is a hobby project. It is not production
   software and it may never reach the goal.
2. **A test of a local LLM coding agent.** Most task work is done by a
   language model that runs on the same two K40c cards (Qwen3.6-35B-A3B
   through llama.cpp and OpenCode), one task per session, with a human who
   reads its output. The repository is set up to measure how far such an
   agent gets and where it fails.

Read the content with the second purpose in mind:

| Part | Written by | Trust |
|---|---|---|
| `AGENTS.md`, `docs/PHASES.md`, `docs/design/`, `.opencode/`, `tools/check_repo.py`, `tools/haiku/`, `scripts/`, `reference/pci/` | The user, with Claude (Anthropic) as assistant | Reviewed |
| Task outputs: `hardware/`, `analysis/`, `registers/`, `firmware/`, `work/`, later the driver source | The local agent. Commits start with the task ID (`A1: ...`). | As labelled. A claim is KNOWN, INFERRED or UNKNOWN, and a register is SOURCE_ONLY until it is verified. `make check` verifies format and some facts, not completeness. |
| `docs/STATUS.md`, `docs/OPEN_QUESTIONS.md` | Both | Check against the task log and the reviews |

Agent output can contain confident errors, including citations of files
that do not exist. Do not use a register value or a command sequence from
this repository on real hardware without checking its source.

## Working with OpenCode

Run `opencode` in this directory. The project config (`opencode.json`)
allows routine commands, asks
before risky ones (sudo, module and PCI tools, `git push`, network
downloads) and blocks edits to `reference/` and `docs/design/`.

Commands:

| Command | Use |
|---|---|
| `/next` | Start the current task from `docs/STATUS.md`. |
| `/handoff` | Close the task: check, result, status, commit. `/next` ends with these steps. |
| `/check` | Run `make check` and report. |
| `/escalate` | Write an escalation and stop the task. |
| `/review` | Read-only review of the last finished task, in a new session after the handoff (`review` agent). |

Model configurations (`~/llm-server/llm-mode.sh`):

| Mode | Use |
|---|---|
| `dual` | One model on both K40c. Default, fastest single session. |
| `two` | One model per K40c. Two sessions at a time: `opencode` and `opencode -m llamacpp/qwen3.6-k40b`. |
| `one` | One model on the K40c at 03:00.0. No process on the K40c at 04:00.0, for hardware tests. |

The project config has no fixed model. It uses the OpenCode default, which
`llm-mode.sh` sets.

Start a new OpenCode session for each task. The repository is the memory:
`docs/STATUS.md`, `docs/tasks/<task>.md`, `work/<task>/`.

## Layout

| Path | Content |
|---|---|
| `AGENTS.md` | Rules for the agent (safety, evidence, protocol). |
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
