# B6: review of the work in progress (2026-10-08) — REWORK

Reviewer: Claude (Anthropic), at the user's request. A session of three
hours wrote `tools/compute_launch.py`, `analysis/compute_launch.json`
and `analysis/compute_launch.md`, and stopped at the time limit with no
handoff. The scaffold committed the files as work in progress.

## What is right

- The class: `0x0000a1c0`, `NVF0_COMPUTE_CLASS`.
- The tool reads the source: 19 setup methods, 6 launch methods with
  `LAUNCH_DESC_ADDRESS` before `LAUNCH`, 22 descriptor fields with their
  bit ranges, and it marks the branches for other chips.
- `--check` exists and passes.

## Defects (`make check` reports the first three as one cause)

| File | Problem | Evidence | Severity |
|---|---|---|---|
| `analysis/compute_launch.json` | Every `file` begins with `reference/mesa/`. The task says that paths are relative to `reference/mesa/`. The check joins the two and finds no file. | `"file": "reference/mesa/src/gallium/..."`. Correct: `"src/gallium/drivers/nouveau/nvc0/nve4_compute.c"`. The same for `class_source`: give `file:line`. | High, small fix |
| `analysis/compute_launch.json` | No `value` in `setup` and `launch` entries. The task asks for the text of the `PUSH_DATA` lines up to the next `BEGIN_`. | 0 of 19 setup entries have `value`. | Medium |
| `analysis/compute_launch.md` | It does not agree with the JSON file: 23 setup rows against 19 entries, and the Offset column says `N/A` where the JSON file has the offset. Method names print as `0x0x2a0`. | Rows 8, 9, 10 and the Offset column. Generate the file from the same data as the JSON file, in the same run. | Medium |
| `analysis/compute_launch.json` | `kernel_needs` is a list of phrases. The task asks for each need with the Mesa call that shows it. | Give `{"need", "file", "line"}`. | Medium |
| `analysis/compute_launch.md` | Two parts are missing: how the shader code reaches the GPU (`CODE_ADDRESS`), and which parts are for other chips. | No such sections. | Medium |
| `work/B6/` | No `RESULT.md`; `docs/STATUS.md` has no B6 row. | The handoff did not run. | Process |

## What the rework needs

1. Fix the paths in the tool. Run `make check`: the three failures go.
2. Add `value`, the two missing parts of the summary and the
   `kernel_needs` entries. Generate both files from one data structure.
3. Extend `--check` to compare both files with what the tool generates.
4. `make check`, then the handoff, then stop.

Do not read the Mesa files whole. The tool already knows where
everything is: change the tool.

# Second review (2026-10-08, commit 9448fde) — REWORK, one defect of content

Reviewer: Claude (Anthropic). The rework took 42 minutes and fixed every
item of the first review: paths, `value`, one data structure for both
files, `kernel_needs` with sources, the two missing parts of the summary,
`RESULT.md` and the handoff. `make check` passes and `--check` passes.

## Defects

| File | Problem | Evidence | Severity |
|---|---|---|---|
| `analysis/compute_launch.json` | The lists do not say which methods the GK110 card receives. Three entries are in branches for newer chips only, and a driver that sends them would be wrong. | `setup`, lines 87 and 90 (`0x2a0`, `0x7b0`): the `else` branch of `if (obj_class < GV100_COMPUTE_CLASS)` at `src/gallium/drivers/nouveau/nvc0/nve4_compute.c:77`. `launch`, line 878 (`0x02c0`): the `else` branch of `if (... < GA102_COMPUTE_CLASS)` at line 874. | High |
| `tools/compute_launch.py` | The tool already works this out and then drops it. `gk110_active` is computed for every method and is not put in the entry. | The line `gk110_active = all(cond_stack) if cond_stack else True`, and the entry that follows it. A later step also keeps only some keys of each entry. | High, small fix |
| `analysis/compute_launch.md` | The first row of "Other-Chip Branches" is wrong. Line 108 is `if (obj_class >= NVF0_COMPUTE_CLASS)`: GK110B takes that branch, and the `0x0248` block that it guards is rightly in the setup list. `SUBC_CP(0x02c4)` is inside a comment and is never sent. The table is written by hand in `other_chip_branches()`. | Lines 108 to 126 of `nve4_compute.c`. | Medium |
| `analysis/compute_launch.json` | `class_source` has no line number. | The task asks for `file:line`. | Low |

## What the rework needs

1. Add `"gk110": true` or `false` to every `setup` and `launch` entry,
   from `gk110_active`. Expected: false for the entries at lines 87, 90
   and 878, true for all others (17 of 19 in `setup`, 5 of 6 in
   `launch`; the first version of this review said 16, a counting error of the reviewer). `make check` will verify these three lines.
2. In the summary, list only the methods with `gk110` true in the two
   sequence tables, and build the other-chip table from the entries with
   `gk110` false and their conditions. Remove the hand-written rows.
3. Add the line number to `class_source`.
4. `make check`, handoff, stop.

# Resolution (2026-10-08, commit 87b195b): accepted

The second rework took 60 minutes. Every entry has the `gk110` mark: 17
of 19 setup methods and 5 of 6 launch methods are sent on GK110, and the
three at lines 87, 90 and 878 are not. The summary lists only the GK110
methods and builds the other-chip table from the data. `class_source`
has its line. `make check` and `--check` pass.

Left as it is: the other-chip table gives the condition as `else` and not
as the condition of the `if` that it belongs to (lines 77 and 874).
