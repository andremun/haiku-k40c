# Rules for this repository (K40c Haiku compute driver)

Goal: a native Haiku kernel driver that runs one verified compute job on a
Tesla K40c (GK110). Design and specification: `docs/design/`. This file
holds rules only. Project knowledge lives in the files below.

## Where the project state is

- `docs/STATUS.md`: current phase, current task, last result. Read first.
- `docs/PHASES.md`: phases, tasks, outputs and acceptance checks.
- `docs/OPEN_QUESTIONS.md`, `docs/ASSUMPTIONS.md`: unresolved items.
- `work/<task-id>/`: `PLAN.md`, `FINDINGS.md`, `RESULT.md` of each task.
- `escalations/`: problems that need a human decision.
- `reference/`: pinned read-only sources. Commits: `reference/MANIFEST.md`.
- `docs/HAIKU_BUILD_TEST.md`: how to compile a Haiku driver on this machine
  and load it in a test VM (`tools/haiku/`). Read it before any Haiku code.

Do not reconstruct project history from the conversation. The files are
the truth.

## Session protocol

1. Read `docs/STATUS.md` and the current task in `docs/PHASES.md`.
2. Read only the files that the task needs.
3. Do one task. Write `work/<task-id>/PLAN.md` before large work.
4. Run `make check`. Fix what fails.
5. Run the handoff (`/handoff`): update `docs/STATUS.md`, write
   `work/<task-id>/RESULT.md`, record open questions, commit.
6. Stop. The next task starts in a new session.

`/review` runs in its own new session after the handoff. It reviews the
last finished task (last row of the task log), not the current task.

## Hardware safety (never break these)

- Both K40c cards run the language model you are running on. Never touch
  them: no `sudo`, no module load or unload, no `setpci` writes, no BAR or
  `/dev/mem` access, no `nvidia-smi` with options, no GPU reset.
- The Haiku test VM (`tools/haiku/vm-test.sh`) has no GPU. Never give it
  one: no `vfio-pci`, no QEMU host-device options, no change to that
  script's QEMU command line. A VM result is never hardware evidence.
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
- Do not start sub-agents.

## Escalation

After 3 materially different attempts at the same problem, or when the
evidence contradicts the reference, stop. Write `escalations/ESC-NNN.md`
(use `/escalate`) and end the task.

## Definition of done (task)

The task outputs exist in the format that `docs/PHASES.md` specifies,
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
