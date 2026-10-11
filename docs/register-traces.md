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

Linux kernel mmiotrace records MMIO accesses via the `mmiotrace` module.
Enable it on Linux:

1. Load the module: `sudo modprobe mmiotrace`
2. Start tracing: `sudo bash -c 'echo 1 > /proc/driver/mmiotrace/enable'`
3. Run the workload
4. Stop tracing: `sudo bash -c 'echo 0 > /proc/driver/mmiotrace/enable'`
5. Read the log: `cat /proc/driver/mmiotrace/log`

(These steps follow the kernel documentation for mmiotrace; specific
commands may vary with kernel version. If `mmiotrace` is unavailable
on the target kernel, a custom kernel module or ftrace-based approach
may be used instead.)

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
