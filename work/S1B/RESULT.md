# S1B result

Done on the host. Session: Claude Code in a cloud container, 2026-10-23 (ADR 003).

## Changes

| Part | File | Change |
|---|---|---|
| 1 | `tools/restore_verification_refs.py` | `SOURCES` holds the real sparse lists. New `REQUIRED` and `DECODER`. `--check` compares each cache's sparse list (slashes stripped, sorted) with `SOURCES` and names missing and extra entries. It checks every required path, except envytools nvbios/nvbios.c, which the decoder checkout supplies. New `envytools_full()`: `$K40_ENVYTOOLS_FULL`, default `~/haiku-cross/src/envytools`. It raises `ValueError` for an absent path, another commit, changed tracked files, a sparse checkout or a missing `nvbios.c`. It never writes. `--check` prints `envytools (full, decoder): clean <commit> <path>`. Without `--check`, an absent full checkout prints `git clone` and `git checkout --detach` and exits 1. New caches use no-cone sparse mode. |
| 2 | `tools/devinit_sources.py` | Reads `nvbios.c` from `envytools_full()`. Output keys and cites keep the logical name reference/envytools/nvbios/nvbios.c. That path is not in the sparse cache: the file comes from the full checkout. |
| 3 | `Makefile` | `check` runs, after `tools/check_repo.py`: the restore `--check`, then the `--check` of `devinit_trace_join.py`, `load_trace.py`, `devinit_inventory.py`, `devinit_preflight.py` and `devinit_sources.py`. The last three need the private VBIOS image. They report NOT RUN when task A3 is in `.check-skip`, the switch CI already uses. |
| - | `.github/workflows/check.yml` | Makes the full envytools checkout at the pin before `make refs`. Sets `K40_ENVYTOOLS_FULL` for `make refs` and `make check`. |

Deviation from the task text: the A3 switch in the Makefile. Without it, CI fails, because CI has no VBIOS image.

## Check output (this session)

- Caches made with the new lists (four sources, Mesa blocked by the proxy) and a full envytools checkout at `f102b823`:
  `nouveau: clean adc2186...`, `envytools: clean f102b82...`, `haiku: clean 49a0af9...`, `open-gpu-doc: clean 9fdf5c4...`, `envytools (full, decoder): clean f102b82... <path>`. With Mesa this gives the six lines of the task.
- `K40_ENVYTOOLS_FULL=/nonexistent`: `envytools_full()` raises `... /nonexistent does not exist ...`. A sparse checkout as decoder path is refused.
- Old caches (cone mode, with `drivers/hwmon`): `--check` fails with `nouveau: sparse list differs from SOURCES; missing [], extra ['drivers/hwmon']`.
- A required path that is absent: `nouveau: required path nvkm/not-there.c is missing (sparse list: ['drivers/gpu/drm/nouveau'])` (test with a patched `REQUIRED`).
- `devinit_trace_join.py --check` and `load_trace.py --check`: exit 0.
- `devinit_sources.py --check`: NOT RUN here (no VBIOS image). The changed part was checked: the 25 decoder cites computed from the full checkout equal those in `analysis/devinit_sources.json`, and the `nvbios.c` SHA-256 equals the recorded `7e9f739b...36907f`.
- `analysis/devinit_sources.json` and `reference/MANIFEST.md`: not changed.

## KNOWN, INFERRED, UNKNOWN

- KNOWN: the full checkout gives the recorded `nvbios.c` hash and the same decoder lines.
- INFERRED: on the T7610 all six `--check` commands pass. The real sparse lists there match `SOURCES` (scaffold facts of 2026-10-21).
- UNKNOWN: Mesa's no-cone sparse entries for single files fetch as expected in CI. The next CI run shows it.

## For the next step

On the T7610: `make refs` then `make check`. Caches made by an older helper (cloud session caches, not the T7610) fail `--check` until they are made again.
