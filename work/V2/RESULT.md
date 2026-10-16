# V2 result: verification environment and decoder reproduction complete

2026-10-16 (Australia/Melbourne). Base: `1b79a2e`.

Continuation of the user's requested revision of possible mistakes by "Local"
and preparation for machine-dependent work. This task completes source/input
restoration and decoder reproduction; it does not implement or accept A3,
B2/B3, the initialization executor, the hardware recipe or S1.

## What now passes

- All five reference trees exist, are clean, and match every recorded pin.
- Full `make check` passes: repository checker 0 failures; existing C++ suites
  (583 reported checks), new controller (58), boundary regressions, Python
  trace tests (17), D4 acceptance (38) and R1 Python acceptance (11) pass.
- Pinned nvbios builds without system installation or sudo. Its full output
  exactly reproduces the saved firmware decode, including warnings. Targeted
  script and board outputs also exit 0. Firmware-derived text stays ignored.

A separate verification issue was corrected: the previous pytest hooks removed
all tests and forced success. An ignored negative-control test containing
`assert False` exited 0 before correction, 1 after correction. The repository
uses standalone checks through `tests/Makefile`, so the redundant pytest call
and suppression-only `conftest.py`/`pyproject.toml` were removed. This does not
remove any standalone test or modify acceptance files. PyYAML is still needed;
pytest is not required by the corrected `make check` entry point.

## Exact reproduction

From the repository root. Network is needed only to acquire absent public
sources/dependencies/packages; source restoration never resets existing trees.

```sh
python3 tools/restore_verification_refs.py
python3 tools/restore_verification_refs.py --check
python3 -m venv build/verification-venv
build/verification-venv/bin/python -m pip install -r tools/verification-requirements.txt
PATH="$PWD/build/verification-venv/bin:$PATH" make check
```

The restoration script reads pins from `reference/MANIFEST.md`, preserves the
existing symlinks, and populates their targets under `~/llm-server/agent-refs/`.
This cache location is separate from `Documents/packages/llm-server`; no server
implementation or running service was changed. Source URLs are recorded in the
script. Linux/Haiku/Mesa use sparse checkout and depth-one commit fetch; NVIDIA
and envytools were initially cloned with blob filtering and checked out at the
exact commits. All clean revision results are in `evidence.json`.

For the decoder, download and extract packages locally (Ubuntu Jammy host):

```sh
mkdir -p build/decoder-tools
(cd build/decoder-tools && apt-get download flex bison m4)
mkdir -p build/decoder-tools/root
for package in build/decoder-tools/*.deb; do
    dpkg-deb -x "$package" build/decoder-tools/root
done
python3 tools/build_nvbios.py
python3 tools/build_nvbios.py --check
```

Versions actually downloaded: flex 2.6.4-8build2, bison
2:3.8.2+dfsg-1ubuntu0.22.04.1, m4 1.4.18-5ubuntu2. Package hashes, build-tool
hashes, the exact expanded GCC/generator argument lists, compiler version and
binary hash are in `evidence.json`. The builder compiles the selected upstream
libraries using their own CMake source lists. This avoids unrelated full-project
dependencies such as PCI access libraries. Sources are not patched. Bison emits
a deprecated `%name-prefix` warning; the build exits 0.

Run the decoder only against the verified offline file:

```sh
rom_path="$HOME/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
build/nvbios/nvbios "$rom_path" > build/nvbios/all.txt 2>&1
build/nvbios/nvbios -p scripts "$rom_path" > build/nvbios/scripts.txt 2> build/nvbios/scripts.stderr
build/nvbios/nvbios -p gpio -p i2c -p extdev "$rom_path" > build/nvbios/board.txt 2> build/nvbios/board.stderr
cmp build/nvbios/all.txt "$HOME/mediaflux/vbios/decoded/all.txt"
python3 tools/s1_verification_inputs.py --rom "$rom_path"
python3 tools/s1_verification_inputs.py --rom "$rom_path" --check
```

Every decode and comparison above exits 0. The generated inventory still says
`external_inputs_complete: false` because the recorded native cross-toolchain
is absent, not because sources/ROM are missing. The nvbios `-p` option accepts
one exact name per occurrence; repeat it as above, rather than passing a
comma-separated name list (see upstream nvbios.c:1027-1031).

For the pytest diagnostic only, pytest 8.3.5 was installed in the isolated venv;
`evidence.json` records its transitive versions. The probe was
`build/v2-pytest-probe/test_must_fail.py`, containing one failing assertion:

```sh
build/verification-venv/bin/python -m pytest -q -o norecursedirs= build/v2-pytest-probe/test_must_fail.py
```

It now exits 1. It is an ignored negative control, not part of the normal suite.
No failure is suppressed by the corrected make entry point.

## Decoder warning interpretation and next gate

The generic BIT parser warns about several tables, including I. The standalone
nvbios front end separately reads the I-entry initialization pointers
(`reference/envytools/nvbios/nvbios.c:1100-1123`) and prints scripts through its
own path (`:1282-1318`). This explains why warnings and script output coexist;
it does not prove that every reachable instruction or branch was decoded.
The no-strap warning also leaves strap-dependent interpretation unresolved.

Next bounded task: rework A3 with the actual ROM, fresh pinned decoder output,
Nouveau interpreter/POST dispatch, and debug log/trace. Account for main scripts,
subroutines, extra script pointer, helpers, executed/skipped instructions and
runtime-dependent reachability. Do not equate decoder line counts with the
logged instruction count or treat a missing listing offset as absent bytecode.
Keep board-control decisions and every hardware write outside that task.

The Haiku compiler/headers/matching-kernel bundle still needs restoration before
native backend validation. ROM availability and host checks are not hardware
readiness or compute support. V1's host-check blocker is now resolved; its
original failure record remains preserved as history.

No physical GPU, VM, reset/passthrough, sudo, host-driver change or running model
service was touched. No push or subagent work occurred. The reviewer tool was
executed only as required by make check; its implementation was not read.
