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
