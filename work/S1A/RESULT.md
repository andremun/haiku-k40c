# S1A result

Done on the host. Session: Claude Code in a cloud container, 2026-10-23 (ADR 003).

## Changes

| Part | File | Change |
|---|---|---|
| 1 | `src/devinit/Interpreter.cpp` | Opcode 0x7a sets bit 0 of the value when the register is `0x000200` (cites `init.c:1901-1902`). Only 0x7a. A skipped 0x7a writes nothing (`write()` returns early when not active). |
| 2 | `src/devinit/Interpreter.cpp` | Both cites of 0x91 say `init.c:2290`. |
| 3 | `src/runtime/Bootstrap.cpp` | `nv50.c` cites: masks 62-63 and 81-82, `0x001700` writes 68 and 88, `0x700000` write 71 and read 91. Code without comments is byte-identical. |
| 4 | `tests/Makefile` | `s1a_accept:devinit` next to `test_devinit:devinit`. |
| 5 | `src/os/HaikuProbe.c` | K40c branch: reads `PCI_command` (2 bytes) and prints it. Decode off: `memory decode off; not mapped`, `B_NOT_ALLOWED`. `0xffffffff`: `BAR0 does not answer`, `B_IO_ERROR`. Other than `K40_EXPECTED_BOOT0` (`0x0f1240a1`, `hardware/record.json:37`): value printed, `B_BAD_DATA`. No PCI write. Cardless branch unchanged. |
| - | `docs/register-provenance.md` | New rows for the changed Interpreter lines. Generated with `tools/provenance.py`. Rows that cite Mesa were kept from the committed file, because the Mesa tree is absent here. |

## Checks

- `build/tests/s1a_accept`: `s1a_accept: 8 checks, 0 failed`.
- `make -s -C tests`: all C++ tests pass. `r1_accept.py` has 2 failures, the same as on `main` (absent Mesa tree).
- `git diff main -- tests/accept/s1a_accept.cpp`: empty.
- `make check`: 18 failures, the same set as the base commit `254a96e` on this machine. All come from the absent Mesa tree or the private VBIOS image.
- `tools/haiku/build_backend.sh`: NOT RUN. `~/haiku-cross` does not exist in the cloud container. A syntax-only compile of `HaikuProbe.c` (both branches) and `HaikuBackend.c` against the pinned Haiku headers (`49a0af95`, `headers/config`, `os`, `posix`) with host GCC, `-Wall -Wextra`, gives no warnings. This is not the Haiku cross compiler.

## KNOWN, INFERRED, UNKNOWN

- KNOWN: Nouveau `init_zm_reg` sets bit 0 for `0x000200` (`reference/nouveau/nvkm/subdev/bios/init.c:1901-1902`). The dispatch of 0x91 is line 2290.
- INFERRED: the probe links on Haiku. Not checked here.
- UNKNOWN: the value of the PCI command register of the K40c under Haiku before any driver runs.

## Process note

The session read parts of `tools/check_repo.py` (lines 50-100, and one `grep` for the
provenance check). The rule against it was lifted the same day (ADR 003, item 6): no
agent is under test. No rework needed.

## For the next task and the T7610

1. `HAIKU_CROSS=$HOME/haiku-cross bash tools/haiku/build_backend.sh` must link both probes.
2. The scaffold runs the cardless guest in the review.
3. S1B is next.
