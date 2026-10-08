# B6 Result: Compute launch path (user-space half)

## Outputs

- `tools/compute_launch.py` — tool that reads pinned Mesa source and produces
  both JSON and Markdown outputs.
- `analysis/compute_launch.json` — structured extraction.
- `analysis/compute_launch.md` — human-readable summary.

## What was fixed (rework 2 — GK110 branch marking)

1. **`gk110` flag on every entry**: Added `"gk110": true/false` to every setup
   and launch entry. Three entries are `gk110: false` (setup line 87: `0x2a0`,
   setup line 90: `0x7b0`, launch line 878: `0x02c0`). These are in else
   branches for newer chips. The tool computes `gk110_active` from the
   condition stack for each entry.

2. **MD sequence tables filtered to GK110**: The setup and launch tables in
   the markdown only list entries with `gk110: true` (17 setup, 5 launch).

3. **Other-chip table from data**: The "Other-Chip Branches" table is now
   built from entries with `gk110: false` and their conditions (extracted
   from the condition stack), replacing the hand-written rows.

4. **`class_source` line number**: Changed from
   `"src/gallium/drivers/nouveau/nv_object.xml.h"` to
   `"src/gallium/drivers/nouveau/nv_object.xml.h:209"`.

5. **Condition parsing fixes**: Extended `COND_PAT` to match `->` in variable
   names (e.g. `screen->compute->oclass`) and handle `>=`/`<=` operators.
   Added `unlikely()` wrapper handling: when the inner expression is not a
   comparison, the branch is assumed taken (gk110: true).

## What was fixed (rework from previous session)

1. **Path prefix**: Changed all `file` values from reference/mesa/... to
   `src/...` (paths are relative to reference/mesa/). The check_repo.py
   validator joins the file field with reference/mesa/ to locate source lines.

2. **PUSH_DATA `value` field**: Added extraction of PUSH_DATA text between
   each BEGIN_ call and the next BEGIN_. Every setup and launch entry now
   includes a `value` field with the text of PUSH_DATA arguments.

3. **Markdown–JSON agreement**: Both files are now generated from a single
   data structure. The markdown tables match the JSON entries exactly (19
   setup, 6 launch, 22 descriptor fields). Method names display correctly
   (hex values like `0x2a0` no longer show as `0x0x2a0`).

4. **Structured `kernel_needs`**: Changed from plain strings to
   `{"need", "file", "line"}` entries with source references.

5. **Missing MD sections**: Added "Shader Code Delivery (CODE_ADDRESS)"
   and "Other-Chip Branches" sections describing how the shader code
   reaches the GPU and which Mesa branches are not taken on GK110.

6. **`--check` mode**: Extended to compare both JSON and MD files, not just
   the JSON.

## Extraction results

- **Compute class**: `0x0000a1c0` (`NVF0_COMPUTE_CLASS`)
- **Setup methods**: 19 entries from `nve4_screen_compute_setup`
- **Launch methods**: 6 entries from `nve4_launch_grid` (GK110 path),
  `LAUNCH_DESC_ADDRESS` before `LAUNCH` in order
- **Descriptor fields**: 22 entries from `nve4_compute_setup_launch_desc`
  (6 DEF_SET + 16 VAL_SET)
- **Other-chip branches**: 4 branches not taken on GK110 (GM107, GV100,
  GP100, GA102)
- **Kernel needs**: 8 structured entries with source references

## Verification

`make check` passes with 0 failures. `python3 tools/compute_launch.py --check`
exits 0.

## Open questions

- Q1 remains open (unrelated to B6): determining the PMC_BOOT_0 for card
  03:00.0 when the model is not running on it.
