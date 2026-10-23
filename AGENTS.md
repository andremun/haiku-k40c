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

1. Read `docs/STATUS.md`. Its line `Current task:` names one task ID.
   Read `docs/tasks/<ID>.md`. Do that task and no other.
2. Read only the files that the task needs.
3. Do one task. Write `work/<task-id>/PLAN.md` before large work.
4. Run `make check`. Fix what fails.
   `make check` runs `tools/check_repo.py`. Do not read that file, with
   any tool or command (`sed`, `grep`, `cat`, Python). It has the
   reviewer's own solution of some tasks, and work that copies it is
   rejected. The messages of `make check` say what is wrong; the task
   text says what is wanted.
5. Run the handoff (Claude Code: `/handoff`): update `docs/STATUS.md`,
   write `work/<task-id>/RESULT.md` (max 40 lines), add open questions to
   `docs/OPEN_QUESTIONS.md` and root needs to `docs/REQUESTS.md`, commit
   with `<task-id>: <summary>`.
6. Stop. The next task starts in a new session.

The review (Claude Code: `/review`) runs in its own new session after the
handoff. It is read-only. It reviews the last finished task (last row of
the task log), not the current task, and ends with ACCEPT or REWORK.

## Hardware safety (never break these)

- The K40c at 0000:03:00.0 runs `llm-server` for other projects. Never
  touch it. The K40c at 0000:04:00.0 is the driver card, but only the user
  changes its state. For both cards: no `sudo`, no module load or unload,
  no `setpci` writes, no BAR or `/dev/mem` access, no `nvidia-smi` with
  options, no GPU reset.
- The Haiku test VM (`tools/haiku/vm-test.sh`) has no GPU. Never give it
  one: no `vfio-pci`, no QEMU host-device options, no change to that
  script's QEMU command line. A VM result is never hardware evidence.
- `scripts/passthrough.sh` and `tools/guest/linux-run.sh --gpu` give a
  real K40c to a VM. They are user steps (`docs/PASSTHROUGH.md`). Never
  run them. You may run the Linux guest without `--gpu`.
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
- Do not read generated files whole (`analysis/*.json`,
  `analysis/callgraph.md`, `registers/*.json`). Use `grep -n`, `head`, or a
  short script that prints counts or a few entries. Let the tools you write
  do the reading.
- Write what you learn into `work/<task-id>/FINDINGS.md` as you go.
- Do not read `docs/history/` for a task.
- A tool that generates an output file has a `--check` option: it writes
  nothing and exits 0 when the file is what the tool generates. Compare
  the text that would be written with the text of the file. Sort every
  set before use: the output must be the same on every run.
- Sub-agents may read and search. They must not edit files or run
  hardware or VM commands. The main session owns the task and its commit.

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

MIT (`LICENSE`). New source files start with a copyright line and "Distributed
under the terms of the MIT License." Record every consulted Nouveau file in
`docs/licensing.md`.

## Git

Commit small working steps. Never push, never rewrite history, never
delete `reference/`.
