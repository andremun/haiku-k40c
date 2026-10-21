# Task S1B: Make every generated check run from sources that exist

S1 preparation, host only. No card. This file is the whole task text.
General rules: `AGENTS.md`.

## Why

`tools/devinit_sources.py --check` fails on this machine. It reads
`reference/envytools/nvbios/nvbios.c`, but the envytools cache behind
`reference/envytools` is a sparse checkout of `rnndb/` and `docs/` only.
`tools/restore_verification_refs.py --check` still prints "clean",
because git does not report files that a sparse checkout leaves out.
A check that cannot see a missing input is not a check. Fix both tools.
Do not change the pinned commits. Do not change anything under
`~/llm-server/agent-refs/` (the user decides on that cache).

## Inputs (read these, not more)

- `tools/restore_verification_refs.py` (68 lines).
- `tools/devinit_sources.py` (49 lines).
- `reference/MANIFEST.md` lines 1-20.
- `Makefile` (first 10 lines).

## Facts (KNOWN; the scaffold checked them on 2026-10-21)

- Real sparse lists (`git -C <cache> sparse-checkout list`), no-cone
  mode, with a leading and a trailing `/` on each entry:
  - nouveau (`~/llm-server/agent-refs/linux-v6.12`):
    `drivers/gpu/drm/nouveau`
  - envytools: `rnndb`, `docs`
  - haiku: `headers/os`, `headers/private/kernel`,
    `headers/private/drivers`, `headers/private/graphics`,
    `src/add-ons/kernel/drivers/graphics/nvidia`, `docs/develop`
  - open-gpu-doc: not sparse.
  - mesa: `src/gallium/drivers/nouveau`, `docs/features.txt`,
    `docs/license.rst`, `include/drm-uapi/nouveau_drm.h`
- The lists in `SOURCES` of the restore helper differ from these for
  nouveau (it adds `drivers/hwmon`), envytools (it says "not sparse")
  and mesa (it says `docs`). The real lists agree with `MANIFEST.md`.
- A full envytools checkout exists at `~/haiku-cross/src/envytools`, at
  the pinned commit `f102b82381f3f11cee113d16374c87091db039d9`, with no
  changed tracked files (it has untracked build directories). Its
  `nvbios/nvbios.c` has SHA-256 `7e9f739b...36907f`, the value already
  recorded in `analysis/devinit_sources.json`.
- Paths below `reference/` that the tools read: for nouveau
  `nvkm/subdev/bios/init.c`, `nvkm/subdev/instmem/nv50.c`,
  `nvkm/engine/fifo/gk104.c`, `nvkm/engine/fifo/gf100.c`,
  `nvkm/engine/device/base.c`, `nouveau_dma.c`, `nouveau_dma.h`,
  `nvkm/subdev/mmu`, `nvkm/subdev/fb/gf100.c`, `nvkm/subdev/bar/g84.c`;
  for envytools `rnndb` and `nvbios/nvbios.c`; for open-gpu-doc
  `Devinit/devinit.xml`; for mesa
  `src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h` and
  `src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h`. Only
  `envytools/nvbios/nvbios.c` is missing.

## Outputs

1. `tools/restore_verification_refs.py`:
   - `SOURCES` holds the real sparse lists above.
   - New dict `REQUIRED`: for each source, the paths of the list above,
     relative to the link target (`reference/<name>/`).
   - `--check`, for each sparse source: read `git sparse-checkout list`,
     strip the `/` characters at both ends of each entry, sort, and
     compare with `SOURCES`. On a difference, fail with a message that
     names the source and the missing and extra entries.
   - `--check`: every `REQUIRED` path must exist, except the ones that
     the decoder checkout below supplies. On a missing path, fail with
     a message that names the source, the path and the sparse list.
   - New function `envytools_full()`: returns the path of a full
     envytools checkout. Path: environment variable
     `K40_ENVYTOOLS_FULL`, default `~/haiku-cross/src/envytools`. It
     raises `ValueError` with a clear message when the path does not
     exist, when `HEAD` is not the envytools pin of `MANIFEST.md`, when
     `git status --porcelain --untracked-files=no` is not empty, when
     the checkout is sparse, or when `nvbios/nvbios.c` is missing.
     It never writes, fetches, cleans or resets anything.
   - `--check` calls `envytools_full()` and prints
     `envytools (full, decoder): clean <commit> <path>`.
   - Without `--check`, when the full checkout is absent: print the
     commands that make one (`git clone`, `git checkout --detach <pin>`)
     and exit 1. Do not run them.
2. `tools/devinit_sources.py`: read `nvbios.c` from
   `envytools_full()` (import it from the restore helper). Keep every
   string in the output the same: the key `reference/envytools/nvbios/nvbios.c`
   in `source_sha256` and the `decoder_source` cites are logical names.
   `--check` must pass on the existing `analysis/devinit_sources.json`
   with no change of that file.
3. `Makefile`: `check` also runs, after `tools/check_repo.py`:
   `python3 tools/restore_verification_refs.py --check` and the
   `--check` of `devinit_inventory.py`, `devinit_preflight.py`,
   `devinit_trace_join.py`, `load_trace.py` and `devinit_sources.py`.
4. `work/S1B/RESULT.md`: what you changed and the output of each
   `--check` command.

## How to do it (save points)

1. Part 1. Run `python3 tools/restore_verification_refs.py --check`.
   It must print six "clean" lines and exit 0. Then test the failure:
   `K40_ENVYTOOLS_FULL=/nonexistent python3 tools/restore_verification_refs.py --check`
   must exit non-zero with your message. Commit.
2. Part 2. `python3 tools/devinit_sources.py --check; echo $?` prints 0.
   `git status --short analysis/` is empty. Commit.
3. Part 3, then `make check`. Write the result file, hand off.

## Check

- All six `--check` commands exit 0; `make check` passes.
- `analysis/devinit_sources.json` and `reference/MANIFEST.md` are not
  changed (`git diff main --stat`).
- With `K40_ENVYTOOLS_FULL=/nonexistent`, the restore helper and
  `devinit_sources.py --check` both exit non-zero.
- The reviewer reads the messages and the no-write rule by hand.
