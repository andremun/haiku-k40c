# Register-Trace Comparison — Task D4

## Trace text format

One access per line. `R` = read, `W` = write. Offsets are 6 hex digits,
values are 8 hex digits. Lines starting with `#` and empty lines are
skipped; inline comments after the value are ignored.

```
R 0x000200 0x00000100     # read of offset 0x200, value 0x100
W 0x000200 0x00000100     # write of offset 0x200, value 0x100
```

Any line that is not a comment, blank line, or `R`/`W` access raises
`ValueError`.

## Linux mmiotrace format

mmiotrace is a tracer of the Linux kernel's ftrace framework (kernel
documentation: `Documentation/trace/mmiotrace.rst`). It is not a module
and has no file under `/proc`. The kernel must be built with
`CONFIG_MMIOTRACE`. It records the accesses of a driver that maps its
registers **after** the tracer is switched on, so the driver (Nouveau)
must be loaded while tracing runs. While it is active the kernel uses one
CPU only.

Steps, all as root (in this project a user step, in the Linux reference
guest of task C5, never on the host that runs the LLM server):

```
echo mmiotrace > /sys/kernel/tracing/current_tracer
cat /sys/kernel/tracing/trace_pipe > trace.txt &
modprobe nouveau
echo "nouveau loaded" > /sys/kernel/tracing/trace_marker
# run the workload, with more trace_marker lines between its phases
echo nop > /sys/kernel/tracing/current_tracer
```

On older kernels the directory is `/sys/kernel/debug/tracing`. The file
`buffer_size_kb` in the same directory sets the buffer size; when it is
too small, events are lost and the trace says so. A `MARK` line in the
trace is a `trace_marker` text. The BAR0 base for `--bar0` is in the
`PCIDEV` line of the trace and in `lspci -v` (the first memory region).

(This section was written by the scaffold. The first version described a
`/proc/driver/mmiotrace` interface that does not exist.)

The tool accepts mmiotrace text and filters it to 4-byte accesses within
a given BAR region, converting addresses to BAR-relative offsets.

## CLI usage

### Compare two traces

```
python3 tools/compare_register_traces.py EXPECTED ACTUAL [OPTIONS]
```

Exit code 0 with a "match" line when traces agree. Exit code 1 on
difference, with a report showing the kind of mismatch, the number of
matching entries, up to three context entries before the difference,
and the differing expected and actual entries. Exit code 2 for usage
errors.

Options:

- `--writes-only` — ignore all read accesses; useful because read values
  depend on hardware state and may differ between runs even when the
  driver logic is correct.
- `--ignore-read-values` — for read accesses, compare only the offset
  and not the value. Also handles hardware-state-dependent reads.
- `--ignore 0x000100,0x000140` — drop specific offsets from both traces
  (e.g. status registers that self-clear or are polled differently).
- `--mask 0x000200=0xfffffff0 ...` — for each listed offset, compare
  only the bits that are set in the mask. Useful for read-modify-write
  sequences where lower bits are reserved or software-controlled.
- `--names hardware/registers` — show register names from the YAML
  database built in task C1 for each offset in the report.

### Convert mmiotrace output

```
python3 tools/compare_register_traces.py --convert-mmiotrace INPUT \
    --bar0 0xf6000000 --output OUTPUT
```

Filters to 4-byte accesses within the BAR region and writes the standard
trace format.

## Example report

```
Mismatch at entry value: 2 entries matched.
  (context) W 0x000200 0x00000100
  (context) R 0x000100 0x00000000
  Expected index: 2
  Actual index:   2
  Expected: W 0x002140 0x7fffffff
  Actual:   W 0x002140 0x7ffffffe
```

## When to use which options

- **Full comparison** (`no flags`): strictest check. Use when comparing
  a controlled workload where read values are deterministic.
- **`--writes-only`**: compares only the write sequence. Reads (which
  often poll status registers) are ignored. Best for comparing driver
  init sequences.
- **`--ignore-read-values`**: compares write sequence and read offsets.
  Useful when you care about which registers are read but not the
  values (hardware-dependent).
- **`--ignore` + `--mask`**: refine the comparison for known
  non-deterministic registers (counters, timestamps, status bits).
