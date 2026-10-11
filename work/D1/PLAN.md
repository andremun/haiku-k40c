# Task D1 Plan: Register access abstraction

## Steps

1. Write `src/hw/RegisterIO.h` — all declarations (Access, RegisterIO, MockMMIO,
   TraceMMIO, TraceMismatch, parseTrace, formatTrace). Tabs, `f` prefix.
2. Write `src/hw/RegisterIO.cpp` — implementations of parseTrace/formatTrace,
   RegisterIO::mask32, MockMMIO methods, TraceMMIO methods, TraceMismatch.
3. Compile acceptance test: `g++ -std=c++17 -Wall -Wextra -Werror -Isrc
   tests/accept/d1_accept.cpp src/hw/*.cpp`. Fix any failures.
4. Write `tests/test_registerio.cpp` — 15+ CHECK lines covering hooks counting
   writes, mask32 on TraceMMIO, comment-only trace, uppercase hex, bad size,
   etc.
5. Write `tests/Makefile` — builds both test programs, runs them.
6. Write `docs/register-io.md` (40+ lines).
7. Run `make check`, fix failures.

## Checks
- `check_repo.py` verifies hash, compile, acceptance test, no kernel headers,
  15+ own CHECKs, `make -s -C tests` passes.
