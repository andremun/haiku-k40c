# Task D1 Result: Register access abstraction

## Outputs

| File | Lines | Notes |
|---|---|---|
| `src/hw/RegisterIO.h` | 79 | All declarations: Access, RegisterIO, MockMMIO, TraceMMIO, TraceMismatch, parseTrace, formatTrace |
| `src/hw/RegisterIO.cpp` | 193 | All implementations |
| `tests/test_registerio.cpp` | 268 | 43 CHECK lines (15 required) |
| `tests/Makefile` | 26 | Builds both tests, runs them |
| `docs/register-io.md` | 109 | Documentation (40 required) |

## What was implemented

1. **RegisterIO** abstract base class with pure virtual `read32`/`write32`
   and non-virtual `mask32` (read-modify-write: `(old & ~mask) | value`).
2. **MockMMIO** — memory-backed MMIO with:
   - Bounds checking (offset < size, 4-byte aligned, throws `std::out_of_range`)
   - `poke`/`peek` (no logging), `log()`/`clearLog()`
   - `onRead(offset, hook)` — transforms read result without changing stored value
   - `onWrite(offset, hook)` — side-effect callback after write is stored
3. **TraceMMIO** — replay engine:
   - Matches next expected access against offset, type, and value
   - Does not advance position on mismatch
   - Throws `TraceMismatch` with `index()` and formatted offset in message
   - `done()` and `position()` accessors
4. **Trace text** — `parseTrace(istream)` and `formatTrace(vector)` support
   comments (`#`), empty lines, `R/W 0xNNNNNN 0xNNNNNNNN` format.

## Test coverage (own tests)

- Hook that counts writes (side-effect via control→status register)
- `mask32` on TraceMMIO
- Comment-only trace → empty vector
- Uppercase hex in parsed trace
- Non-multiple-of-4 size (integer division)
- Hook overwrite (last registration wins)
- TraceMismatch message format and index
- Empty trace → done() immediately
- TraceMMIO position accuracy through full sequence
- mask32 stores correct new value
- Trailing whitespace in parseTrace
- formatTrace round-trip
- Poke does not trigger write hooks
- Log clear and re-use
- Wrong type mismatch (write when expecting read)
- mask32 bit pattern on full 0xFFFFFFFF

## `make check` result

```
check_repo: 0 failure(s)
test_registerio: 48 checks, 0 failures
d1_accept: 57 checks, 0 failures
```

## Open questions

None.
