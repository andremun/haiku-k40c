# B1: Chipset path and file inventory

## Steps

1. **Identify the chipset**: `nvf1_chipset` (GK110B) selected at `base.c:3218` from
   `case 0x0f1`. Read the full struct at `base.c:1770-1803`.

2. **Resolve all constructor functions**: For each entry in nvf1_chipset, find the
   `.c` file that defines the constructor function (e.g. `gk110_fb_new` → `nvkm/subdev/fb/gk110.c:69`).

3. **Classify each file**:
   - `GK110-specific`: files named `gk110*.c` or `gk110b*.c`
   - `GK104-inherited`: files named `gk104*.c`
   - `GF100-inherited`: files named `gf100*.c`, `gf119*.c`
   - `generic-NVKM`: files named `nv50*.c`, `nv41*.c`, `base.c`
   - `Linux-only`: files using Linux kernel APIs only

4. **Generate outputs**:
   - `tools/nouveau_files.py`: script that produces `analysis/files.json`
   - `analysis/files.json`: list of `{"path", "subsystem", "class", "role"}`

## Verification
- `make check` validates every `path` exists and `class` is in the allowed set.
