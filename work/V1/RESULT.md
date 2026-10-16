# V1 result: partial, external verification inputs blocked

Date: 2026-10-16 (Australia/Melbourne). Starting revision: `637c436`.

This work was undertaken to **revise possible mistakes made by "Local"** and
**get closer to the machine-dependent implementation**, as the user requested.
It is not acceptance of the rejected A3 output, completion of all cardless
tracks, a Haiku driver build, or S1 hardware evidence. Nothing was pushed.

## Changes

- Three independently reproduced helper defects corrected (seven failing
  assertions before correction). Original acceptance files unchanged.
- Added freestanding S1 controller/backend contract and 58 injected host checks.
  It enforces a new pointer transition, ordered publication, fault/deadline
  checks and quiescence-before-release; failed quiescence retains resources.
- Added the deterministic offline source/capture/ROM/toolchain inventory and
  generated `analysis/s1-verification-inputs.json`.
- Added `docs/S1-VERIFICATION.md` with explicit A/B/C gates and machine-specific
  requirements; corrected the S1 firmware/GR claim and indexed V1.

## Commands and results

Run from the repository root. Compiler flags and source lists for the tests
are in `tests/Makefile`; binary/log outputs are ignored under `build/tests`.

| Command | Result |
|---|---|
| `make check` (baseline) | Exit 2, 220 failures. Broken reference links, source-derived checks and dependent acceptance failures; PyYAML check skipped |
| `g++ -std=c++17 -Wall -Wextra -Werror -Isrc -fsanitize=undefined -fno-sanitize-recover=all tests/test_s1_boundaries.cpp src/fifo/PushBuffer.cpp src/hw/RegisterIO.cpp src/mmu/PageTable.cpp -o build/tests/s1_boundaries_before` (before helper corrections) | Exit 0 |
| `build/tests/s1_boundaries_before` | Exit 1, seven failed assertions. Retained negative-control binary, not a rebuilt fixed version |
| `make -C tests ../build/tests/test_s1_boundaries ../build/tests/test_s1_experiment` | Exit 0; UBSan enabled with nonrecovering failures |
| `build/tests/test_s1_boundaries` | Exit 0, no failures after correction |
| `build/tests/test_s1_experiment` | Exit 0, 58 checks, no failures; HOST_ONLY |
| `g++ -std=c++17 -ffreestanding -fno-exceptions -fno-rtti -Wall -Wextra -Werror -Isrc -c src/runtime/S1Experiment.cpp -o build/tests/S1Experiment.freestanding.o` | Exit 0, Linux-host object only |
| `nm -u build/tests/S1Experiment.freestanding.o` | Exit 0, empty output |
| `make -s -C tests` | Exit 2. All C++ binaries pass (583 existing reported checks plus new suites); Python trace test 17/17, D4 37/38, named lookup fails with missing source |
| `python3 tests/accept/r1_accept.py` | Exit 1; 9/11, positive-input cases fail with missing Mesa header |
| `python3 -m pytest -q tests` | Exit 1: interpreter has no pytest |
| `python3 tools/s1_verification_inputs.py` | Exit 0: writes offline inventory, explicitly incomplete |
| `python3 tools/s1_verification_inputs.py --check` | Exit 0: generated inventory matches |
| `python3 tools/s1_verification_inputs.py --check --require-ready` | Exit 2 as intended: external inputs incomplete |
| `python3 -m py_compile tools/s1_verification_inputs.py` | Exit 0 |
| `make check` (after source/test changes) | Exit 2, still 220 failures; no bypass/suppression added |
| `git diff --check` | Exit 0 |

The full check runs the reviewer tool as instructed, but its implementation
was never opened, searched or edited. Two full check attempts are sufficient
to show this environment cannot currently certify repository-wide acceptance.
Existing recorded checks are not rewritten to match missing references.

## Blocking inputs and handoff

1. Restore the exact five source pins in `reference/MANIFEST.md` so provenance,
   register naming, QMD positive-input tests and generation checks can run.
   The inventory records which links fail; it never edits them.
2. Restore pytest and PyYAML in a reproducible verification environment.
3. Restore/rebuild the documented Haiku kernel compiler, headers and matching
   kernel before B3 compile/link/load claims. The host object is not a substitute.
4. User will supply an offline ROM solution later. Expected image: 181760 bytes,
   SHA-256 `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`.
   Do not synthesize missing ROM offsets or trust rejected A3 reachability.
5. After these inputs: rerun full check, rework A3, resolve A4/A5, define B2
   ownership/address/publication interface and C2 source-backed recipe, then
   implement/test the real backend against that recipe. Hardware gates remain
   separate user-reviewed steps under the repository safety rules.

No physical GPU, PCI/reset/passthrough operation, host sudo, host-driver change,
or running host model service was involved. No subagents were used.

## Follow-up: user located the ROM, 2026-10-16

The earlier missing-ROM finding above describes the initial pass, and is now
resolved. Read-only `sha256sum "/home/unimelb.edu.au/mariom1/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"` matched the expected identity; the
inventory checks the exact 181760-byte size too. The saved `decoded/all.txt`
is available, hashed as documented in `reference/vbios/README.md`; its first
14 lines include no-strap and several BIT-table parse warnings. No conclusion
about listing completeness is drawn from the header alone.

Both `python3 tools/s1_verification_inputs.py --rom "/home/unimelb.edu.au/mariom1/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"` and the same
command with `--check` exited 0. The generated report now records
`rom.matches: true`; `external_inputs_complete` remains false because the
source/toolchain inputs are unchanged. No full repository check was repeated
for this input/documentation update. The ROM and decoded firmware content
remain outside Git; neither was uploaded or executed.
