# S1B plan

1. Part 1: `tools/restore_verification_refs.py`. SOURCES holds the real sparse lists. New
   REQUIRED dict. `--check` compares the sparse list of each cache and checks each
   required path. New `envytools_full()` for the full decoder checkout (read-only).
   Without `--check`, an absent full checkout prints the clone commands and exits 1.
   Test: rebuild a cache in a new folder with the tool, then `--check`, then the
   `K40_ENVYTOOLS_FULL=/nonexistent` failure.
2. Part 2: `tools/devinit_sources.py` reads `nvbios.c` from `envytools_full()`. Output
   strings unchanged.
3. Part 3: Makefile `check` runs the restore `--check` and five tool `--check` commands.
   CI cannot run the three that need the private VBIOS. They follow `.check-skip` A3,
   the switch CI already uses. CI clones the full envytools checkout before `make refs`.

Session: Claude Code in a cloud container. No Mesa (proxy), no VBIOS, no ~/haiku-cross.
