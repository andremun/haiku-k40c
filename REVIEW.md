# Review instructions

These rules apply to every review of a change in this repository: Claude Code Review,
the local `/pr-review` skill and Codex (through `AGENTS.md`, "Review guidelines").
Project rules are in `AGENTS.md`. This file says what a review reports and how severe
it is.

## What Important means here

Report as Important (red) only:

- A change that can touch a card: a write to a PCI configuration register, a BAR,
  a GPU reset, a module load, or a VM with a host device, outside
  `scripts/passthrough.sh` and `tools/guest/linux-run.sh --gpu`. Any change that
  uses the K40c at 0000:03:00.0 (it runs `llm-server`, ADR 003).
- A hardware constant (register, bit field, value, command sequence, firmware
  format) without a source: `file:line` in the pinned Nouveau tree, an `rnndb` entry
  or a capture file.
- A claim labelled KNOWN that its cited source does not state. A register marked
  better than SOURCE_ONLY without trace, hardware or Haiku evidence.
- A cardless or VM result presented as K40c evidence.
- Code copied from Nouveau (more than a few lines in sequence), or a consulted
  Nouveau file missing from `docs/licensing.md`.
- A change to `reference/` or `LICENSE`. A change to `tests/accept/` or
  `tools/check_repo.py` that the task does not ask for.
- A task marked DONE while `make check` fails, or without `work/<ID>/RESULT.md`.
- A generated file edited by hand, or a generator whose `--check` no longer matches.
- A wrong result: a logic error, a wrong unit, an off-by-one, unsorted output where the
  output must be stable.

Everything else is Nit (yellow) at most.

## Cap the nits

Report at most five Nits per review. Prefer the ones that a reader would act on.

## Do not report

- Anything that `make check` or CI already enforces (syntax, lint, format, the facts
  that the repository check verifies).
- `docs/history/` and the evidence folders under `results/`. They are records. Do not
  ask to rewrite them.
- `work/*/REVIEW.md` of closed tasks and RESOLVED escalations. They are records.
- The pinned trees behind `reference/` and the captures in `reference/linux-run*/`
  and `reference/pci/`.
- Non-ASCII characters in output string literals of the generator tools. They keep
  the generated files stable (`docs/design/layout.md`, Section 5).
- The 18 known `make check` failures without the Mesa tree or the private VBIOS
  image.

## Always check

### Evidence and provenance (scientific-computing)

- Every new result has a dated folder `results/YYYYMMDD-topic/` (or the folder that
  `AGENTS.md` names) with the command, the input pins and the output. The folder index
  lists it.
- A results table or number in a document names the tool or script that produced it.
  Per-number links are not required.
- Machine-specific values (paths, card addresses, cache folders) come from a setting or
  an environment variable, not from literals in scripts.
  `git grep -l '/home/unimelb.edu.au'` lists only records and provenance files.
- Tools create their output folders (`mkdir -p`, `os.makedirs(..., exist_ok=True)`).

### Code (scientific-computing)

- New Python and shell files start with a copyright line, "Distributed under the terms
  of the MIT License." and a header that says what the file does, what it reads and
  what it writes. MIT is the license of this repository. It overrides the PolyForm
  default of the scientific-computing skill.
- Python comments and docstrings are ASCII. PEP 8, one statement per line.
- Shell uses `set -eu` (or `set -euo pipefail` in bash) and passes
  `shellcheck -S error`.
- A fix comes with a test that fails without it, or the review says why none is
  possible.

### Prose (ste-writing)

Applies to documentation, README text, comments, commit messages and PR text. It does
not apply to code, identifiers, logs or quoted sources.

- Commit title and procedure steps: strict mode. Imperative, at most 20 words.
- Other prose: STE-flavored mode. Active voice. At most 25 words in a descriptive
  sentence. No semicolons. No contractions. American spelling.
- No marketing words (robust, seamless, powerful, comprehensive). Short common words
  (use, start, make sure, before, about).
- One name for one thing. A file, task, model or setting has the same name everywhere.
- Technical names stay unchanged.
- Report prose problems as Nit, unless the text gives a wrong instruction or a wrong
  fact. Then they are Important.

### This repository

- A tool that writes a generated file has a `--check` option. Sets are sorted.
- C and C++ build with `-Wall -Wextra` and add no warnings.
- Task work follows `docs/tasks/<ID>.md` and changes no other task's outputs.

### Documentation follows the code

- A change of behavior, layout or a command updates `README.md` or `docs/STATUS.md` in
  the same change. A milestone adds one line to `CHANGELOG.md`.
- A decision that changes a rule has an ADR in `docs/decisions/`.
- Links and paths in changed documents exist.

## Evidence for findings

A finding about behavior cites `file:line` in this repository or in a pinned source.
Do not infer behavior from a name. If the evidence is not available, say UNKNOWN and
do not report the finding as Important.
