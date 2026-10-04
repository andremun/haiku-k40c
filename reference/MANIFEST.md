# Pinned reference sources (read-only)

The directories here are symbolic links to `~/llm-server/agent-refs/`.
Do not edit them. Cite files as `reference/<name>/<path>:<line>`.

| Link | Source | Commit | Date |
|---|---|---|---|
| `nouveau/` | Linux tag v6.12, `drivers/gpu/drm/nouveau` | adc218676eef25575469234709c2d87185ca223a | 2024-11-17 |
| `envytools/` | envytools (sparse: `rnndb`, `docs`) | f102b82381f3f11cee113d16374c87091db039d9 | 2023-10-26 |
| `open-gpu-doc/` | NVIDIA open-gpu-doc | 9fdf5c4062007929d9f4e6cbad9c9771fe61b880 | 2026-06-09 |
| `haiku/` | Haiku (sparse: `headers/os`, `headers/private/{kernel,drivers,graphics}`, `src/add-ons/kernel/drivers/graphics/nvidia`, `docs/develop`) | 49a0af9585d80e42240af63ab66e31e9873f59b8 | 2026-09-28 |
| `pci/` | Captures from this T7610, 2026-09-29, without root (copied, not linked) | - | - |

`pci/root/` holds the captures that need root (2026-10-05): full config
space, capabilities, setpci reads, `/proc/iomem`, dmidecode, and
PMC_BOOT_0 of 0000:04:00.0. `dmesg-gpu.txt` has no boot-time driver
messages (the kernel log had rotated). Capture again after a reboot if needed.
