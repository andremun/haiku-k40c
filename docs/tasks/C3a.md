# Task C3a: Subsystem models, part 1 (mc, bar, imem, mmu, fb, top)

Phase C: hardware database and firmware. This file is the whole task text. `make check` verifies the
checks named here. General rules: `AGENTS.md`. Paths to Nouveau files in
any output are relative to `reference/nouveau/`; line numbers are 1-based.

- Why: for each subsystem that the card needs, the Haiku driver must
  know which functions Nouveau uses on this chip and what each one does
  to the hardware. Nouveau says which functions in a function table: the
  constructor of the subsystem passes it on. This task reads the table
  of six subsystems and describes every member, with a quoted source
  line as evidence.
- Subsystems and constructors (from `nvf1_chipset`): `mc`
  `gk104_mc_new`, `bar` `gf100_bar_new`, `imem` `nv50_instmem_new`,
  `mmu` `gk104_mmu_new`, `fb` `gk110_fb_new`, `top` `gk104_top_new`.
- Outputs: `tools/hwmodel.py`, `analysis/hwmodel/<subsystem>.json` and
  `docs/hardware-model/<subsystem>.md` for the six subsystems.
- `<subsystem>.json`:

  ```json
  {"subsystem": "mc",
   "constructor": {"name": "gk104_mc_new", "file": "nvkm/subdev/mc/gk104.c", "line": 63},
   "table": {"name": "gk104_mc", "file": "nvkm/subdev/mc/gk104.c", "line": 52},
   "members": [
     {"member": "init", "value": "nv50_mc_init", "kind": "function",
      "file": "nvkm/subdev/mc/nv50.c", "line": 0, "parent": null,
      "accesses": [{"file": "...", "line": 0, "op": "wr32", "reg": "0x000140"}],
      "role": "init", "needed_for_compute": true,
      "what": "...", "certainty": "KNOWN",
      "evidence": {"line": 0, "quote": "nvkm_wr32(device, 0x000140, 0x00000001);"}}],
   "depends_on": ["top"],
   "summary": "..."}
  ```

- What the tool computes (the check computes the same):
  - Definitions: in every `.c` file under `reference/nouveau/nvkm` (walk
    with `followlinks=True`), a line that matches `^(\w+)\(` defines a
    function, and a line that matches `^(\w+) = \{` defines a table.
    Keep the first definition of each name. A body ends at the first
    later line that starts with `}`.
  - `table`: the first `&NAME` in the body of the constructor where NAME
    is a table.
  - `members`: each line of the table body that matches
    `\s*\.([\w.]+)\s*=\s*&?(\w+)` gives `member` and `value`, in source
    order. `kind` is `function` when `value` is a defined function,
    `table` when it is a defined table, else `value`. `file` and `line`
    are the definition (null for `value`). When a member of the main
    table is a table, its own members follow it, with `parent` set to
    the member name; do not go deeper. `mc` has 15 members, `bar` 11,
    `imem` 7, `mmu` 3, `fb` 9, `top` 1.
  - `accesses`: for a function, the entries of
    `registers/mmio_accesses.json` with the same `function` and `file`,
    sorted by line, with the keys `file`, `line`, `op`, `reg`. Else `[]`.
- What you decide, for every member (a table in the tool or a file that
  it reads):
  - `role`: `init`, `interrupt`, `teardown`, `runtime` or `data`.
  - `needed_for_compute`: true when one compute job on a started card
    cannot work without it.
  - `what`, 6 words or more: what it does to the hardware. Read the
    function first: `sed -n 'A,Bp' file` from its line to the next `}`.
    Most are under 30 lines.
  - `certainty`: `KNOWN` when the code or its comments say it, `INFERRED`
    when you conclude it from names and context, `UNKNOWN` when you
    cannot tell. `UNKNOWN` is a correct answer; a guess marked `KNOWN`
    is a defect.
  - `evidence`, for a function with `KNOWN` or `INFERRED`: `line` is a
    line inside the function and `quote` is 10 characters or more copied
    from that line. Choose the line that supports `what`.
- `depends_on`: the other subsystems that the functions call
  (`device->NAME` or `nvkm_NAME_...`). `summary`, 30 words or more: what
  the subsystem is for and what the Haiku driver has to reproduce.
- Do not expand abbreviations that you have not seen expanded in the
  source. `mc` is the master control (engine enable bits and
  interrupts), `imem` is instance memory, `top` is the device topology
  table, `bar` is the BAR1 and BAR2 address-space setup.
- `<subsystem>.md`: the tool writes it from the JSON, with the sections
  `Purpose` (the summary), `Nouveau files`, `Members` (table: member,
  function, role, needed, registers), `Dependencies`, `KNOWN`,
  `INFERRED`, `UNKNOWN` (the `what` texts by certainty, each with its
  `file:line`).
- How to do it (a first session filled its context three times and lost
  its work each time: it wrote decisions into the generated JSON files,
  which the tool then overwrote, and it read whole source files):
  - `tools/hwmodel.py` exists and its structure is right. Do not rewrite
    it. Do not read it whole.
  - Your decisions go in `analysis/hwmodel/decisions/<subsystem>.json`,
    one file for each subsystem. You write these files; the tool reads
    them and never writes them:

    ```json
    {"summary": "...", "depends_on": ["top"],
     "members": {
       "init": {"role": "init", "needed_for_compute": true, "what": "...",
                "certainty": "KNOWN",
                "evidence": {"line": 0, "quote": "..."}},
       "intr.pending": {"role": "interrupt", "needed_for_compute": false,
                        "what": "...", "certainty": "INFERRED",
                        "evidence": {"line": 0, "quote": "..."}}}}
    ```

    The key of a nested member is `parent.member`. Never edit
    `analysis/hwmodel/<subsystem>.json` or a `.md` file by hand: run
    `python3 tools/hwmodel.py` to write them.
  - Work on one subsystem at a time, in this order: `top`, `mmu`, `mc`,
    `imem`, `bar`, `fb`. For each one:
    1. `python3 -c "import json; [print(m['parent'], m['member'],
       m['value'], m['kind'], m['file'], m['line']) for m in
       json.load(open('analysis/hwmodel/NAME.json'))['members']]"`
       lists the members. Do not open the JSON file.
    2. For each function: `sed -n 'LINE,+25p' reference/nouveau/FILE`.
       Never read a source file whole. A member of kind `value` or
       `table` needs no evidence.
    3. Write `analysis/hwmodel/decisions/NAME.json`.
    4. `python3 tools/hwmodel.py && make check 2>&1 | grep NAME`.
    5. When no failure names this subsystem: `git add -A && git commit
       -m "C3a: NAME"` and add one line to `work/C3a/NOTES.md`
       ("NAME done"). Read `work/C3a/NOTES.md` first when you start or
       when you are not sure what is done.
  - Do not read `tools/check_repo.py`: the failure messages say what is
    wrong.
  - `tools/hwmodel.py --check` writes nothing and exits 0 when all JSON
    and Markdown files are what the tool generates.
  - The work directory is `work/C3a`. In `docs/STATUS.md` the task ID in
    the task log is `C3a`.
- Check: constructor, table, members, kinds, definitions and accesses
  against the source; role, certainty and evidence as described; a
  member named `intr...` has role `interrupt`, and `dtor` and `fini`
  have role `teardown`. The reviewer reads the `what` texts against the
  quoted lines.
