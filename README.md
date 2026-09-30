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
