# Task C5a: The shader binary and the launch descriptor of the reference run

Phase C: hardware database and firmware. This file is the whole task text. `make check` verifies the
checks named here. General rules: `AGENTS.md`.

- Why: the reference job (`output[i] = input[i] + 1`) ran on the K40c
  under Linux on 2026-10-13 (Nouveau, Mesa 25.2.8, result PASS). The log
  has the machine code that Mesa generated for the compute shader and
  the launch descriptor (Mesa prints it as "Queue Meta Data") that Mesa
  sent to the card. The Haiku driver of milestone S3 sends the same code
  and a descriptor with the same fields. This task takes both out of the
  log into files that later tasks use.
- Input (read these, not more): `reference/linux-run/compute_test.log`
  (160 lines; `sed -n '100,160p'` shows the part that matters),
  `reference/linux-run/RESULT.txt`, and the string `kSource` in
  `tools/guest/files/compute_test.c` (the shader source).
- What is in the log:
  - Mesa prints `shader binary code (0xNN bytes):` and then the code as
    32-bit words in hex, 8 words on a line. It prints this for 5
    programs. The compute shader is the LAST one, directly before the
    line `Queue Meta Data:`. Its size is `0xa0` bytes.
  - After `Queue Meta Data:` each line is `   NAME : VALUE` (three
    spaces, a name that can end in an index like `(7)`, a colon, a
    value). The values are hex numbers, `TRUE`, `FALSE` or a word.
    The list ends at the line `elements: 1024, wrong: 0`.
- Outputs:
  - `tools/shader_extract.py`. It reads the log and writes the three
    files below. Standard library only. The same output on every run.
    `tools/shader_extract.py --check` writes nothing and exits 0 when
    the three files are what the tool generates, and 1 when not.
  - `firmware/compute_add1.bin`: the code words of the compute shader,
    each word as 4 bytes, least significant byte first (little-endian),
    in the order of the log. The size is the size that the log gives.
  - `analysis/linux_run_shader.json`, an object with:
    `"log"` (the path of the log), `"log_line"` (the 1-based line of the
    `shader binary code` line that was used), `"size_bytes"`,
    `"words"` (the words as strings like `"0xa0a09c80"`, in order),
    `"sha256"` (of the `.bin` file), `"renderer"` and `"version"` (the
    text after `renderer: ` and `version: ` in the log),
    `"source"` (the lines of the shader source, a list of strings
    without the `\n`), and `"qmd"`: a list with one object for each
    line after `Queue Meta Data:`, in the order of the log:
    `{"name": "PROGRAM_OFFSET", "value": "0x7f100"}`. Name and value
    are the text of the log without the spaces around them.
  - `firmware/compute_add1.md`, with these sections (`## ` headings):
    "Source" (the shader source in a code block, and the file it is
    in), "How it was made" (the renderer, the Mesa version, the
    command, the environment variables `NV50_PROG_DEBUG=1` and
    `NV50_PROG_CHIPSET=0xf1`, the log file and line), "Code" (size,
    sha256, and the words in a code block, 8 on a line), "Launch
    descriptor" (a table `| Field | Value |` with only the fields
    whose value is not `0x0` and not `FALSE`, in the order of the
    log), "Not known" (a list: what this file does not tell, for
    example what each instruction word means; do not explain the
    instructions).
- How to do it:
  - Write `work/C5a/PLAN.md` (10 lines). Write the tool. Run it. Look
    at the output files. Run `make check`.
  - Do not type the words or the fields by hand: the tool reads them.
  - Do not read the other files of `reference/linux-run/` (the trace
    is 900,000 lines; it is for the next task).
  - The work directory is `work/C5a`. In `docs/STATUS.md` the task ID in
    the task log is `C5a`. Write `work/C5a/RESULT.md` (what was made,
    the numbers: size, sha256, number of fields, number in the table).
- Check: `reference/linux-run/RESULT.txt` says PASS; the `.bin` file is
  the words of the last code dump of the log; the JSON agrees with the
  log (words, every descriptor field in order); the document has the
  sections, the sha256 and a table row for each field that is not zero
  or false and no other row; `--check` passes twice.
