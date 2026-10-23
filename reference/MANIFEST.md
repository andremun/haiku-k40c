# Pinned reference sources (read-only)

The directories here are symbolic links into `.refs/`, an ignored link to the source
cache. `make refs` creates `.refs` (target `$K40_REFS`, default `~/llm-server/agent-refs`)
and fetches each missing source at its pinned commit. Do not edit them. Cite files as `reference/<name>/<path>:<line>`.

| Link | Source | Commit | Date |
|---|---|---|---|
| `nouveau/` | Linux tag v6.12, `drivers/gpu/drm/nouveau` | adc218676eef25575469234709c2d87185ca223a | 2024-11-17 |
| `envytools/` | envytools (sparse: `rnndb`, `docs`) | f102b82381f3f11cee113d16374c87091db039d9 | 2023-10-26 |
| `open-gpu-doc/` | NVIDIA open-gpu-doc | 9fdf5c4062007929d9f4e6cbad9c9771fe61b880 | 2026-06-09 |
| `haiku/` | Haiku (sparse: `headers/os`, `headers/private/{kernel,drivers,graphics}`, `src/add-ons/kernel/drivers/graphics/nvidia`, `docs/develop`) | 49a0af9585d80e42240af63ab66e31e9873f59b8 | 2026-09-28 |
| `mesa/` | Mesa tag mesa-25.2.8, the version in the Linux reference guest (sparse: `src/gallium/drivers/nouveau` with `codegen`, `docs/features.txt`, `docs/license.rst`, `include/drm-uapi/nouveau_drm.h`). The user-space half of a compute job: launch descriptor, compute methods, GK110 shader code emitter. | f97d7dcca0e51d7e20ed4342bb5ea8afea7db7fa | 2025-12-04 |
| `pci/` | Captures from this T7610, 2026-10-07, without root (`scripts/capture_user.sh`) | - | - |

The envytools cache above is sparse and has no `nvbios/`. The decoder source
(`nvbios/nvbios.c`) comes from a full checkout of the same commit, outside
`agent-refs`: `~/haiku-cross/src/envytools` (override: `K40_ENVYTOOLS_FULL`).
`tools/restore_verification_refs.py --check` verifies it (task S1B).

`pci/root/` holds the captures that need root (2026-10-07; PMC_BOOT_0 from 2026-10-05): full config
space, capabilities, setpci reads, `/proc/iomem`, dmidecode, and
PMC_BOOT_0 of 0000:04:00.0. `dmesg-gpu.txt` has no boot-time driver
messages (the kernel log had rotated). Capture again after a reboot if needed.
