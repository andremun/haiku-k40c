# Task S1A: Fix the defects of the scaffold review of 2026-10-21

S1 preparation, host only. No card. This file is the whole task text.
General rules: `AGENTS.md`.

## Why

The scaffold reviewed the executor, the bootstrap code and the Haiku
probe against the pinned Nouveau tree (`docs/S1-PLAN.md`, "Scaffold
review 2026-10-21"). It found one defect that changes a card register
value, some wrong source lines in comments, and a gap in the identity
probe that the first card stage (B5) needs closed. Fix them.

## Inputs (read these, not more)

- `src/devinit/Interpreter.cpp` lines 80-110 and 155-200.
- `src/runtime/Bootstrap.cpp` lines 10-70.
- `src/os/HaikuProbe.c` (74 lines) and `src/os/HaikuBackend.h`.
- `tests/accept/s1a_accept.cpp` (the scaffold's test; do not change it).
- `reference/nouveau/nvkm/subdev/bios/init.c` lines 1892-1905 and
  2286-2292.
- `reference/nouveau/nvkm/subdev/instmem/nv50.c` lines 57-96.
- `reference/haiku/headers/os/drivers/PCI.h` lines 130-140, 240, 685.

## Facts (KNOWN; do not check them again)

- Nouveau `init_zm_reg` (opcode 0x7a) sets bit 0 of the value when the
  register is `0x000200` (`init.c:1901-1902`). No other opcode does
  this. The K40c ROM has `ZM_REG R[0x000200] = 0x00002020` at ROM
  offset `0x8638`. The Linux run wrote `0x2021`
  (`reference/linux-run-debug/mmiotrace.txt.xz`, line 45511). Our
  executor writes `0x2020` today: that clears bit 0 of the master
  enable register.
- The dispatch line of opcode 0x91 is `init.c:2290`, not 2289.
- In `nv50.c` the base and offset masks are at lines 62-63 and 81-82,
  the `0x001700` writes at 68 and 88, the `0x700000` write at 71 and the
  `0x700000` read at 91.
- The recorded PMC_BOOT_0 of the development card is `0x0f1240a1`
  (`hardware/record.json` line 37). A read of `0xffffffff` means that
  the BAR does not answer (memory decode off or card absent).
- Haiku's own nvidia driver turns on memory decode before it maps the
  BAR (`reference/haiku/src/add-ons/kernel/drivers/graphics/nvidia/driver.c:543-550`).
  Our probe must not write PCI configuration. It may read it.

## Outputs

1. `src/devinit/Interpreter.cpp`: opcode 0x7a sets bit 0 of the value
   when the register is `0x000200`, with a comment that cites
   `init.c:1901-1902`. Only opcode 0x7a. A skipped 0x7a writes nothing.
2. `src/devinit/Interpreter.cpp`: the two cites of 0x91 say `2290`.
3. `src/runtime/Bootstrap.cpp`: every `nv50.c:` cite uses the line
   numbers above. Values and code do not change.
4. `tests/Makefile`: add `s1a_accept:devinit` to the program list, next
   to `test_devinit:devinit`. Change nothing else in that file.
5. `src/os/HaikuProbe.c`, K40c path only (the `#else` branch):
   - Before `k40_os_map_readonly`, read the 2-byte PCI command register
     with `os.pci->read_pci_config(info.bus, info.device, info.function,
     PCI_command, 2)`. Print it with `dprintf`.
   - If bit `PCI_command_memory` is 0: print
     `k40_os: memory decode off; not mapped`, set status to
     `B_NOT_ALLOWED` and go to `failed`. Do not write the register.
   - After the read of offset 0: if the value is `0xffffffff`, print
     `k40_os: BAR0 does not answer` and fail with `B_IO_ERROR`. If it
     is not `0x0f1240a1`, print the value and fail with `B_BAD_DATA`.
     Put the expected value in one named constant with a comment that
     cites `hardware/record.json:37`.
   - The cardless branch (`K40_CARDLESS_TEST`) does not change.
6. `work/S1A/RESULT.md`: what you changed, file by file, and the output
   of the commands in "Check".

## How to do it (save points)

1. Parts 1 and 4. Build and run the test:
   `make -s -C tests ../build/tests/s1a_accept && build/tests/s1a_accept`.
   It must print `8 checks, 0 failed`. Then run `make -s -C tests`.
   Commit.
2. Parts 2 and 3. Run `make -s -C tests`. Commit.
3. Part 5. Compile both probes:
   `HAIKU_CROSS=$HOME/haiku-cross bash tools/haiku/build_backend.sh`.
   It must link both probes. Do not start a VM: the scaffold runs the
   cardless guest in the review. Commit.
4. Write `work/S1A/RESULT.md`, run `make check`, hand off.

## Check

- `build/tests/s1a_accept` prints `8 checks, 0 failed`, and all other
  tests still pass.
- `git diff main -- tests/accept/s1a_accept.cpp` is empty.
- `tools/haiku/build_backend.sh` links both probes.
- `make check` passes.
- The reviewer reads part 5 and the cites by hand.
