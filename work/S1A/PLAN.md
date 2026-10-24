# S1A plan

1. Parts 1 and 4: opcode 0x7a sets bit 0 for register 0x000200 (init.c:1901-1902).
   Add `s1a_accept:devinit` to tests/Makefile. Run `build/tests/s1a_accept`
   (expect 8 checks, 0 failed) and `make -s -C tests`.
2. Parts 2 and 3: the 0x91 cites say 2290. The nv50.c cites in Bootstrap.cpp use
   lines 62-63, 81-82, 68, 88, 71 and 91. Run `make -s -C tests`.
3. Part 5: HaikuProbe.c K40c path reads the PCI command register, refuses when
   memory decode is off, and checks PMC_BOOT_0 against 0x0f1240a1.
   Build with tools/haiku/build_backend.sh where ~/haiku-cross exists.
4. RESULT.md, make check, handoff.

Session: Claude Code in a cloud container (ADR 003). No ~/haiku-cross here, so
the Haiku link of part 5 is a step for the T7610.
