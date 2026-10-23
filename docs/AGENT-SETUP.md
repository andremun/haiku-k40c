# Coding agent setup

Task work uses Claude Code or Codex on the T7610, with cloud models
(`docs/decisions/003-end-local-agent-experiment.md`). Both follow `AGENTS.md`.

## Claude Code

The project settings are in `.claude/settings.json`. They apply to every session in
this directory.

| Rule | Commands or paths |
|---|---|
| Ask first | `sudo` and other root tools, module and PCI tools (`modprobe`, `setpci`), `nvidia-smi`, `dd`, `mount`, `systemctl`, `reboot`, `qemu-system-x86_64`, anything with `vfio`, `scripts/passthrough.sh`, `tools/guest/linux-run.sh --gpu`, `git push`, history rewrites, `rm -rf`, downloads (`curl`, `wget`, `apt`, `pip install`), web fetches. Edits to `AGENTS.md`, `CLAUDE.md`, `docs/design/` and `tools/haiku/`. |
| Deny | Any read or run of `tools/check_repo.py` except through `make check`. Edits to `reference/`, `LICENSE`, `tests/accept/` and `.claude/`. |

Task skills: `/next`, `/handoff`, `/escalate`, `/review` (`.claude/skills/`).

The settings are a guard, not the safety rule. The rules of `AGENTS.md` ("Hardware
safety") apply also where no setting asks first.

## Codex

Codex reads `AGENTS.md` directly. Its settings are per user, in
`~/.codex/config.toml`. Use a sandbox that can write only in the working folder,
with no network, and that asks before it leaves the sandbox:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false
```

The sandbox blocks root tools, PCI writes and edits outside the repository. It cannot
hide `tools/check_repo.py`: the rule in `AGENTS.md` covers that. Codex has no skills
for the task steps. It follows "Session protocol" in `AGENTS.md`.

These keys are from the Codex documentation of 2026. Check them against the installed
version (`codex --help`) before use.

## Cards

The K40c at 0000:04:00.0 is the driver card. The K40c at 0000:03:00.0 runs
`llm-server` in mode `one`. An agent never changes the state of either card.
