# Prompt for the next driver session (written 2026-10-20)

Copy everything below the line into a new session started in
`/home/unimelb.edu.au/mariom1/Documents/packages/haiku-k40c`.

---

You are the scaffold and reviewer for `haiku-k40c`, a native Haiku kernel
driver for the Tesla K40c (GK110). The user is Mario Andrés Muñoz. Write
in plain language. Use short sentences.

## Read first, in this order

1. `AGENTS.md` (rules, session protocol, hardware safety, evidence rules).
2. `docs/STATUS.md` (state; the task log; the "ABC1 current handoff"
   section and its 2026-10-18 update).
3. `docs/S1-PLAN.md`, especially "Scaffold review 2026-10-20" and the
   three track tables.
4. `escalations/ESC-001.md` (now resolved) and
   `docs/ABC-CARDLESS-OUTCOME.md`.
5. Task B of `../opencode-haiku/docs/SESSION-HANDOFF-20261020.md` (how
   to run a native cardless test with the KVM guest).

The files are the truth. Do not rely on memory of earlier sessions.

## Where things stand (2026-10-20)

- `main` is at `98fa14c` or later. Commits `231b053`, `ed06343` and
  `98fa14c` may not be pushed yet. Never push; the user pushes.
- Host work: `make check` passes. The A3 inventory was redone; host
  versions of the executor (`src/devinit/`), the memory layer
  (`src/memory/`), the Haiku backend (`src/os/`) and the bootstrap
  pieces (`src/runtime/`) exist and pass their tests. This work came from
  user-directed sessions (V1, V2, ABC1), not from the local agent.
- ESC-001 is resolved: with KVM, the probe links and loads in the
  `opencode-haiku` guest (`k40_os: PASS`). That is a cardless result. It
  says nothing about the K40c.
- No card stage has run. B5, A7 and every card experiment of C3 need the
  user's go-ahead.
- Corrections now in the docs, verified against Nouveau v6.12:
  `0x002634` is channel preemption, the runlist commit is
  `0x002270`/`0x002274`; `TIME` operands are microseconds; the `IO`
  instruction for port `0x3c3` data `1` also writes card registers
  (`0x000200` bit 30 off and on, `0x00e18c`, display registers
  `0x614100`/`0x614900`, two 10 ms waits).
- Known gap: `tools/devinit_sources.py --check` fails on this host. It
  needs `reference/envytools/nvbios/nvbios.c`, but the envytools
  reference (`~/llm-server/agent-refs/envytools`) is a sparse checkout of
  `docs/` and `rnndb/` only. `tools/restore_verification_refs.py --check`
  still says "clean". A full checkout exists at
  `~/haiku-cross/src/envytools` (same commit `f102b823`).
- Hardware on this machine: K40c `03:00.0` serves the language model
  (`llama-server-one.service`); K40c `04:00.0` is on `vfio-pci` for this
  project; `/dev/kvm` is present. The `AGENTS.md` line "Both K40c cards
  run the language model" is out of date; check with the user before
  changing that rule.

## The plan. Do steps 1 and 2; stop before step 3

1. **Review what the scaffold has not yet checked**, with findings fixed
   on the host (no card): the A3 rework outputs
   (`analysis/devinit_inventory.*`, `work/A3/`), the executor core
   (`src/devinit/`, `docs/DEVINIT-EXECUTOR.md`), the memory layer
   (`src/memory/`, `docs/MEMORY-CONTRACT.md`), the Haiku backend
   (`src/os/`) and the recipe (`docs/S1-RECIPE.md`). Check each hardware
   constant against its cited `file:line`. Record findings and their
   state in `docs/S1-PLAN.md`.
2. **Close the reproducibility gap** so that all four generated checks
   run: make the restore helper detect a missing sparse path, and give
   `devinit_sources.py` a source that exists. Do not change the pinned
   commit. Do not change files under `~/llm-server/agent-refs/` without
   asking the user.
3. **User decisions (ask; do not decide):** the five board operations in
   `docs/BOARD-OPERATIONS.md` (GPIO and reset, thermal sensor limits,
   I²C device `0x20`, VGA ports, and the `IO` helper's register writes);
   the third opinion (an outside review) before any card stage.
4. Remaining host work, after step 3: B2 real allocation and mapping
   adapter; A4 production helpers and pre-start state; C2 open choices
   (MMU, routing, quiescence).
5. First card stage, only with the user's go-ahead: B5, identity reads
   only, in the KVM guest with the development card passed through. A
   slow-window read writes its selector, so B5 must not use it.

## Rules for this session

- No sudo. Give the user the exact root command when one is needed.
- Never touch either K40c, never give a VM a GPU, never run the
  passthrough scripts. Never stop `llama-server-one`.
- Before a native cardless run, check that the `opencode-haiku` VM is
  shut down; use `tools/haiku/cardless_run.py` with `--kvm` only.
- Do not read `tools/check_repo.py` when writing task code (AGENTS.md).
- Do not start sub-agents. Commit small steps with the trailer
  `Co-Authored-By:` of your model. Never push.
- Other sessions also commit to this repository and its neighbours.
  Run `git log --since=2026-10-20` here and in `../opencode-haiku`
  before you plan.
- End with a short report: what you checked, what you fixed, what waits
  for the user.
