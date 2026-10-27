# Rules for this repository (K40c Haiku compute driver)

Goal: a native Haiku kernel driver that runs one verified compute job on a
Tesla K40c (GK110). Design and specification: `docs/design/`. This file
holds rules only. Project knowledge lives in the files below.

These rules apply to Claude Code and Codex (cloud models, run on the T7610).
Claude Code reads them through `CLAUDE.md`. Setup: `docs/AGENT-SETUP.md`.

## Where the project state is

- `docs/STATUS.md`: current phase, current task, last result. Read first.
- `docs/tasks/<ID>.md`: the text of one task (outputs and checks). Read
  only the file of the current task. `docs/PHASES.md` is the index.
- `docs/OPEN_QUESTIONS.md`, `docs/ASSUMPTIONS.md`: unresolved items.
- `work/<task-id>/`: `PLAN.md`, `FINDINGS.md`, `RESULT.md` of each task.
- `escalations/`: problems that need a human decision.
- `reference/`: pinned read-only sources. Commits: `reference/MANIFEST.md`.
- `docs/HAIKU_BUILD_TEST.md`: how to compile a Haiku driver on this machine
  and load it in a test VM (`tools/haiku/`). Read it before any Haiku code.

Do not reconstruct project history from the conversation. The files are
the truth.

## Session protocol

1. Read `docs/STATUS.md` and the current macro task in `docs/tasks/<ID>.md`.
2. Read only the files that the macro task needs.
3. Write `work/<task-id>/PLAN.md` before large work. Commit small working steps directly to `main`.
4. Run `make check` before every commit. Fix failures. Change reviewer checks only when the task requires it.
5. Keep `docs/STATUS.md` and `work/<task-id>/FINDINGS.md` current.
6. At the macro-task handoff, write `work/<task-id>/RESULT.md` (max 40 lines).
   Record questions in `docs/OPEN_QUESTIONS.md` and root needs in `docs/REQUESTS.md`.
7. Report completed macro tasks or grouped review batches. The user requests Claude Code review.
   Authorized sequential host tasks may continue while review is pending (ADR 007).

Claude Code reviews milestone-sized macro tasks, such as the B5 launcher or
board-operation policy and helpers. Small fixes within a macro task need no
separate review. Reviews run read-only in a new session under `REVIEW.md`.
ADR 005 records these rules.

## Hardware safety (never break these)

- Never run as root: no `sudo`, `su`, `doas` or `pkexec`, on the T7610 or
  anywhere else. A step that needs root is a user step in `docs/REQUESTS.md`.
- The K40c at `0000:03:00.0` runs `llm-server`. Never touch it or pass it through.
  Never pass through the Quadro K600 at `0000:82:00.0`.
- The user permits Haiku passthrough of only `0000:04:00.0` for read-only stages (ADR 005).
  Refuse unless it is bound to `vfio-pci`, alone in its IOMMU group, with a writable VFIO group device.
  Only the user changes its host binding. ADR 008 approves planned S1 read-only
  stages when their implementation, review and prerequisites are ready.
- A write stage (A7, the first write of each C3 stage, or any stage whose driver can
  write a GPU register, program the card or start device DMA) needs the user's
  go-ahead each time, before it runs (ADR 007, ADR 008). Present the reviewed stage
  package and wait for an explicit yes. An approval covers one run of one stage.
- No root, module load or unload, `setpci` writes, host BAR or `/dev/mem` access,
  `nvidia-smi` options, or manual GPU reset. The VFIO reset at VM start is permitted.
- `tools/haiku/vm-test.sh` stays cardless. Never change its QEMU command line or add a host device.
  Cardless results are never K40c evidence. The separate card launcher enforces the approved stage and host limits.
- Never run `scripts/passthrough.sh`. The user already bound the development card.
  `tools/guest/linux-run.sh --gpu` needs separate user approval. Linux without `--gpu` is permitted.
- Run one guest at a time, with a disposable overlay, incremental logs, and a ten-minute deadline.
  Ask before shutting down a running VM. Record a hang or panic and stop without a modified retry.
  After any launcher-reported stop, report and ask the user before another run,
  even if diagnosis finds a parser false alarm (ADR 006).
- If a task needs data that only root can read, write the exact read-only
  command into `docs/REQUESTS.md` and continue with other work.

## Evidence rules

- Label every hardware claim KNOWN (read in a capture or directly in
  source), INFERRED (strong indication, not verified) or UNKNOWN.
- Never invent registers, bit fields, command sequences or firmware
  formats. Every hardware constant needs a source: `file:line` in the
  pinned Nouveau tree, an envytools `rnndb` entry, or a capture file.
- Verification status of a constant: SOURCE_ONLY, TRACE_VERIFIED,
  HARDWARE_VERIFIED, HAIKU_VERIFIED. Nouveau use alone is SOURCE_ONLY.
- Study Nouveau and reimplement. Do not copy Nouveau files or large code
  blocks. Record consulted files in `docs/licensing.md`.

## Working on this machine

- Search narrowly (`grep -rn` with specific patterns, `| head -50`,
  `sed -n 'A,Bp'`). Nouveau is inherited code: follow the chain from the
  chipset entry through gk110, gk104 and gf100 implementations.
- Capture file formats are documented in `reference/pci/README.md`. Read
  it before you decode a capture. The captures agree with each other: do
  not re-derive a format, and do not spend more than one attempt on a
  mismatch before you check that file.
- When `make check` verifies a value against a capture, accept it. Do not
  verify the same value again by hand.
- Generate data (JSON/YAML) with scripts in `tools/`, not by hand.
- Write what you learn into `work/<task-id>/FINDINGS.md` as you go.
- `docs/history/` is a record. Current facts are in `docs/STATUS.md` and the
  task files.
- A tool that generates an output file has a `--check` option: it writes
  nothing and exits 0 when the file is what the tool generates. Compare
  the text that would be written with the text of the file. Sort every
  set before use: the output must be the same on every run.
- Sub-agents follow these rules. Hardware and VM commands stay in the main
  session, which owns the task and its commit.

## Escalation

After 3 materially different attempts at the same problem, or when the
evidence contradicts the reference, stop. Write `escalations/ESC-NNN.md`
(Claude Code: `/escalate`) and end the task.

## Definition of done (task)

The task outputs exist in the format that `docs/tasks/<ID>.md` specifies,
`make check` passes, `docs/STATUS.md` is updated and the work is
committed. Never report a task as done while a check fails. Say what is
still open.

## License

Use ASCII "Mario Andres Munoz" in Python and C/C++ comments. Use
"Mario Andrés Muñoz" in prose.

MIT (`LICENSE`). New source files start with a copyright line and "Distributed
under the terms of the MIT License." Record every consulted Nouveau file in
`docs/licensing.md`.

## Git

Use only `main`. Do not create task branches. Commit small working steps after `make check` passes.
Never push. The user pushes. Never rewrite history or delete `reference/`.
Do not use the rejected A3 attempt, retained only as tag `archive/task-a3`.
`reference/HAIKU-TOOLS.json` in `haiku-k40c-llm` may be re-pinned after shared-tool changes.
Other `reference/` content remains read-only.

## Review guidelines

Reviews follow `REVIEW.md`. Report only Important findings (P0, P1) unless the request
asks for more. In Claude Code, run the review with `/pr-review`.
