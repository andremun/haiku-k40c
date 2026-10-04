# haiku-k40c

Native Haiku compute driver for the NVIDIA Tesla K40c (GK110). Design:
`docs/design/design.md`. Specification: `docs/design/specification.md`.

## Working with OpenCode

Run `opencode` in this directory. The project config (`opencode.json`)
selects the local model `qwen3.6-dual`, allows routine commands, asks
before risky ones (sudo, module and PCI tools, `git push`, network
downloads) and blocks edits to `reference/` and `docs/design/`.

Commands:

| Command | Use |
|---|---|
| `/next` | Start the current task from `docs/STATUS.md`. |
| `/handoff` | Close the task: check, result, status, commit. |
| `/check` | Run `make check` and report. |
| `/escalate` | Write an escalation and stop the task. |
| `/review` | Read-only review of a task's outputs (`review` agent). |

Model configurations (`~/llm-server/llm-mode.sh`):

| Mode | Use |
|---|---|
| `dual` | One model on both K40c. Default, fastest single session. |
| `two` | One model per K40c. Two sessions at a time: `opencode` and `opencode -m llamacpp/qwen3.6-k40b`. |
| `one` | One model on the K40c at 81:00.0. No process on the K40c at 04:00.0, for hardware tests. |

The project config has no fixed model. It uses the OpenCode default, which
`llm-mode.sh` sets.

Start a new OpenCode session for each task. The repository is the memory:
`docs/STATUS.md`, `docs/PHASES.md`, `work/<task>/`.

## Layout

| Path | Content |
|---|---|
| `AGENTS.md` | Rules for the agent (safety, evidence, protocol). |
| `docs/` | Status, phases, open questions, requests, design documents. |
| `reference/` | Pinned read-only sources (`MANIFEST.md`) and PCI captures. |
| `tools/` | Analysis scripts and `check_repo.py`. |
| `hardware/`, `analysis/`, `registers/`, `firmware/` | Task outputs. |
| `work/` | Per-task plans, findings and results. |
| `escalations/` | Problems that need a decision. |
| `scripts/capture_root.sh` | Read-only PCI captures for the user to run with sudo. |
