# B6 Plan: Compute launch path (user-space half)

## Inputs (relative to `reference/mesa/`)
- `src/gallium/drivers/nouveau/nvc0/nve4_compute.c` (1010 lines)
- `src/gallium/drivers/nouveau/nvc0/nve4_compute.xml.h` (433 lines)
- `src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h` (660 lines)
- `src/gallium/drivers/nouveau/nvc0/qmda0c0.c`
- `src/gallium/drivers/nouveau/nv_object.xml.h`

## Tool: `tools/compute_launch.py`
1. Read `nv_object.xml.h` → find `NVF0_COMPUTE_CLASS` value (0xa1c0).
2. In `nve4_compute.c`: find `nve4_screen_compute_setup` (~140 lines),
   `nve4_launch_grid` (~110 lines), `nve4_compute_setup_launch_desc` (~50 lines).
3. Parse `BEGIN_NVC0`/`BEGIN_1IC0`/`BEGIN_NIC0` for methods, extract NAME.
4. Parse `SUBC_CP(...)` for non-BEGIN methods. Collect `PUSH_DATA` as values.
5. Look up offsets from `nve4_compute.xml.h` (#define NVE4_COMPUTE_XXX).
6. Parse `NVA0C0_QMDV00_XX_VAL_SET`/`DEF_SET` lines in launch_desc for descriptor fields.
7. Look up `#define NVA0C0_QMDV00_XX` in `cla0c0qmd.h` for bits (MW(hi:lo)).
8. Write `analysis/compute_launch.json` and `analysis/compute_launch.md`.
9. `--check` mode: regenerate JSON and compare (no sort needed, keep source order).

## Checks
- `compute_class` matches `NVF0_COMPUTE_CLASS` from `nv_object.xml.h`.
- Each `file:line` holds the method/field name.
- `LAUNCH_DESC_ADDRESS` then `LAUNCH` in launch order.
- `kernel_needs` not empty.
- `make check` passes.
