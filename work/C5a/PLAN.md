# Plan C5a: Shader binary and launch descriptor of the reference run

Steps:
1. Write `tools/shader_extract.py` that reads `compute_test.log` and `compute_test.c`.
2. It finds the last "shader binary code" dump, parses words, QMD fields, renderer/version.
3. Extracts `kSource` lines from `compute_test.c` via regex.
4. Writes `firmware/compute_add1.bin` (little-endian packed words).
5. Writes `analysis/linux_run_shader.json` (log, words, sha256, qmd, etc.).
6. Writes `firmware/compute_add1.md` (Source, How it was made, Code, Launch descriptor, Not known).
7. Supports `--check`: exits 0 if outputs match tool's own generation.
8. Run the tool, verify outputs, run `make check`.
