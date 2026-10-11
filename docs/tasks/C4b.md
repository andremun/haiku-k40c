# Task C4b: Design documents (MMU, FIFO, GR, firmware)

Phase C: hardware database and firmware. This file is the whole task text. `make check` verifies the
checks named here. General rules: `AGENTS.md`. Paths to Nouveau files in
any output are relative to `reference/nouveau/`; line numbers are 1-based.

- Why: phases A to D produced facts in many files. Before any Haiku
  code is written, the user reviews four short design documents that
  say, for each part of the driver, what Nouveau does, what the Haiku
  driver will do, with which Haiku functions, what is already tested on
  the host, and what is not known. A document that states a guess as a
  fact is worse than no document: the reader cannot tell them apart.
- Outputs: `docs/04-mmu-design.md`, `docs/05-fifo-design.md`,
  `docs/06-gr-design.md`, `docs/07-firmware-analysis.md`.
- Inputs. Each document is written from results that exist. Read these
  and do not read Nouveau source files whole (use `sed -n 'A,Bp'` on the
  lines that the inputs cite):

  | Document | Inputs |
  |---|---|
  | `04-mmu-design.md` | `docs/hardware-model/mmu.md`, `bar.md`, `imem.md`, `fb.md`; `docs/mmu-encoding.md`; `src/mmu/PageTable.h` |
  | `05-fifo-design.md` | `docs/hardware-model/fifo.md`, `chan.md`, `top.md`, `mc.md`; `docs/pushbuffer-encoding.md`; `src/fifo/PushBuffer.h` |
  | `06-gr-design.md` | `docs/hardware-model/gr.md`, `ltc.md`, `privring.md`, `timer.md`; `analysis/min_chain.md`; `analysis/compute_launch.md` |
  | `07-firmware-analysis.md` | `firmware/README.md`, `firmware/manifest.yaml`; the `fecs` and `gpccs` members in `docs/hardware-model/gr.md` |

  For the Haiku side of all four: `analysis/linux_deps.md` (which Haiku
  function replaces which Linux function) and `docs/register-io.md`.
- Each document has these six sections, as `## ` headings with exactly
  these names, in this order:
  1. `Goal`: what this part must achieve for milestone S1 (MMU, FIFO)
     or S3 (GR, firmware), in five lines or fewer. The milestones are in
     `docs/PHASES.md`.
  2. `What Nouveau does`: the steps in order. Every step cites its
     source as `nvkm/path/file.c:LINE` (or `src/gallium/...:LINE` for
     Mesa), 8 citations or more. Take the lines from the hardware model
     documents; open each one with `sed` before you cite it.
  3. `Haiku driver design`: the steps that the Haiku driver will do, as
     a numbered list, each with the step of section 2 that it
     reproduces, and which steps of Nouveau it leaves out and why.
     Name the classes of `src/` that already do part of it.
  4. `Haiku interfaces`: the Haiku kernel functions that the steps need,
     each written as `` `name()` `` with its header, 3 or more. Only
     functions that exist: check each with `grep -rlw NAME
     reference/haiku/headers | head -3`. If you need something and find
     no Haiku function, put it in "Not known".
  5. `Host tests`: which files under `tests/` cover which step, and
     which steps have no host test. For GR and firmware there are no
     host tests yet: name `tests/` and say what a test would need.
  6. `Not known`: a list of 3 items or more. What the analysis does not
     establish, what can only be answered on the card, and every place
     where the inputs disagree. Copy the open points of the reviews in
     `work/B5/REVIEW.md`, `work/C2/REVIEW.md` and `work/C3e/REVIEW.md`
     that belong to the document.
- Rules that the check enforces:
  - 70 lines or more for each document.
  - Every cited `file:LINE` exists.
  - A hex number with exactly 6 digits (`0x002100`) is read as a
    register address and must be in `hardware/registers/*.yaml`. Find
    one with `grep -rn "address: '0x002100'" hardware/registers`. Write
    values that are not registers with another number of digits
    (`0x0000face`) or in words.
  - Every file named in backticks (`` `src/...` ``, `` `tests/...` ``,
    `` `docs/...` ``, `` `analysis/...` ``, `` `firmware/...` ``)
    exists.
  - Every `` `name()` `` in "Haiku interfaces" is a word in the Haiku
    headers.
- Rules that the reviewer enforces:
  - Do not expand an abbreviation unless the source expands it (FECS,
    GPCCS, PPC, TPC, GPC, ROP, RAMFC, CBC, HCE, PRI are not expanded).
  - Do not describe what a register "does" beyond what its name in the
    register database and the code line show. "Writes 0x7fffffff to
    PFIFO.INTR_EN" is a fact; "enables all FIFO interrupts except the
    reserved one" is a guess unless a line says so.
  - Do not give commands for Haiku or Linux that you have not seen in
    this repository.
- How to do it:
  - Write `work/C4b/PLAN.md` (10 lines). Then one document at a time, in
    the order firmware, MMU, FIFO, GR. After each: `make check 2>&1 |
    grep NAME`, fix, `git add -A && git commit -m "C4b: NAME"`, and a
    line in `work/C4b/NOTES.md`. Read that file first when you start or
    when you are not sure what is done.
  - Write each document in two or three steps (sections 1 and 2, then 3
    and 4, then 5 and 6), not in one reply.
  - The work directory is `work/C4b`. In `docs/STATUS.md` the task ID in
    the task log is `C4b`.
- Check: the six sections; the citations, registers, files and Haiku
  functions exist; the lengths. The reviewer reads every statement.
