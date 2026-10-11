# Register I/O Abstraction — Task D1

## Purpose

The `RegisterIO` abstraction provides a uniform interface for all
register accesses in the K40c driver. Every piece of driver logic
(page-table setup, FIFO start, GR engine init) calls `read32()`,
`write32()` and `mask32()` on a `RegisterIO&` rather than on a
specific hardware device. This makes two testing approaches possible:

* **MockMMIO** — a memory-backed MMIO space that records every access
  in a log. Logic routines run on the mock, their access sequence is
  captured, and the results are verified against expected values.
* **TraceMMIO** — a replay engine that plays back a recorded access
  sequence. When the same routine runs on a TraceMMIO, it must produce
  exactly the same access pattern; any deviation throws `TraceMismatch`.

In production, a third implementation (`RealMMIO`) will wrap Haiku's
PCI config-space BAR mappings. It is not written in this task.

## Classes

### RegisterIO (abstract base)

Pure virtual interface: `read32(offset)`, `write32(offset, value)`.
Also provides a non-virtual `mask32(offset, mask, value)` that reads
the register, writes `(old & ~mask) | value`, and returns `old`.

### MockMMIO

In-memory MMIO space. Constructor takes size in bytes (all zeroed).
Access offsets must be aligned to 4 bytes and strictly below the size;
otherwise `std::out_of_range` is thrown.

* `poke(offset, value)` / `peek(offset)` — direct memory access without
  logging. Used to prime the space or probe side-effect targets.
* `log()` — returns the ordered list of all `read32`/`write32` calls.
* `clearLog()` — empties the log without changing memory.
* `onRead(offset, hook)` — registers a callback that transforms the
  read value. The stored memory value is unchanged. Use for status
  registers that report completion bits.
* `onWrite(offset, hook)` — registers a callback invoked after a
  write is stored. Receives a reference to the MockMMIO and the value.
  Use for control registers that trigger side effects.

### TraceMMIO

Replays a fixed sequence of expected accesses. Constructor takes the
vector of `Access` objects. `read32` matches the next expected access
against offset and type (READ); `write32` also checks the value. Any
mismatch throws `TraceMismatch` and does **not** advance the position.

* `done()` — true when all expected accesses have been consumed.
* `position()` — number of accesses consumed so far.
* `TraceMismatch::index()` — index of the expected access that did not
  match. `TraceMismatch::what()` contains the offset as `0x%06x`.

## Trace text format

`parseTrace()` reads a text stream and returns a `vector<Access>`.
`formatTrace()` serialises a vector back to text.

One access per line:

```
R 0x000200 0x00000100     # read of 0x200, returned value 0x100
W 0x000200 0x00000100     # write of 0x200, value 0x100
```

`R` = read, `W` = write. Offsets are 6 hex digits (zero-padded),
values are 8 hex digits. Lines starting with `#` and empty lines are
skipped; inline comments after the value are ignored. Invalid lines
throw `std::invalid_argument`.

## Testing pattern

A routine is written once against the `RegisterIO&` interface:

```cpp
bool start_engine(RegisterIO& io)
{
    io.write32(0x10c, 0);
    io.write32(0x100, 2);
    for (int i = 0; i < 5; i++)
        if (io.read32(0x800) & 0x80000000u)
            return true;
    return false;
}
```

1. Run on **MockMMIO** with a read hook that simulates the status
   register becoming ready after N polls.
2. Capture the log with `formatTrace(mock.log())`.
3. Replay on **TraceMMIO** with the same routine and assert it also
   returns true and `done()` is true.

This pattern verifies both the logic flow and the exact register
sequence against the recorded trace.

## RealMMIO (future, Haiku version)

The real implementation will:

* Map the PCI BAR containing the engine MMIO registers via Haiku's
  PCI config space API.
* Use `readl()` / `writel()` (or the Haiku equivalent) for access.
* Pass through all offsets unchanged (no bounds checking — the kernel
  handles address safety).
* Not implement hooks or tracing (those are test-only features).
