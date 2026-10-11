# Plan: C2 — Firmware Manifest

## Approach
1. Parse the two `.fuc3.h` headers for `static uint32_t NAME[] = {` arrays,
   extracting name, first/last line, word count, SHA256 of packed words.
2. Parse the two `.fuc3` assembly sources for `#include "..."` directives.
3. Parse `gf100.c` for `gf100_gr_load_fw(gr, "NAME", &gr->FIELD.kind)` lines.
4. Parse `gf100.c` body of `gf100_gr_init_ctxctl_int` for all function calls.
5. Write manifest YAML and README with required sections.

## Outputs
- `tools/fw_manifest.py` — generates `firmware/manifest.yaml` (`--check` / `--extract DIR`)
- `firmware/manifest.yaml` — built_in (4 arrays), external (4 files), load_sequence (17 calls)
- `firmware/README.md` — 50+ lines with all required sections
- No `.bin` files in `firmware/`; use `build/` for extraction testing
