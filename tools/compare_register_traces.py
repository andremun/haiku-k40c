#!/usr/bin/env python3
"""Register-trace comparison tool -- Task D4.

Parses trace files (the text format of task D1), converts Linux mmiotrace
output, and compares two traces to find differences.

Standard library only (yaml may be used for --names). No pytest.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
import sys
import os
import argparse

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def parse_trace(text):
    """Parse a trace text into a list of (op, offset, value) tuples.

    Format: one access per line:
        R 0x000200 0x00000100     # read of 0x200, returned value 0x100
        W 0x000200 0x00000100     # write of 0x200, value 0x100
    Lines starting with # and empty lines are skipped.
    Inline comments after the value are ignored.
    Any other line raises ValueError.
    """
    trace = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Remove inline comment
        if " #" in line:
            line = line[:line.index(" #")].strip()
        parts = line.split()
        if len(parts) < 3:
            raise ValueError(f"Invalid trace line: {line!r}")
        op = parts[0]
        if op not in ("R", "W"):
            raise ValueError(f"Invalid op {op!r} in trace line: {line!r}")
        try:
            offset = int(parts[1], 16)
        except ValueError:
            raise ValueError(f"Invalid offset {parts[1]!r}: {line!r}")
        try:
            value = int(parts[2], 16)
        except ValueError:
            raise ValueError(f"Invalid value {parts[2]!r}: {line!r}")
        trace.append((op, offset, value))
    return trace


def format_trace(trace):
    """Format a trace list back to text.

    Offset is 6 hex digits (zero-padded), value is 8.
    """
    lines = []
    for op, offset, value in trace:
        lines.append(f"{op} 0x{offset:06x} 0x{value:08x}")
    return "\n".join(lines) + "\n" if lines else ""


def convert_mmiotrace(text, bar0, size=0x1000000):
    """Convert Linux mmiotrace text to the standard trace format.

    A line like:
        R 4 TIME MAPID 0xADDRESS 0xVALUE 0xPC 0
    is a read of 4 bytes at a physical address.
    Keep only lines with width 4 and bar0 <= address < bar0 + size.
    The offset is address - bar0.
    Skip VERSION, PCIDEV, MAP, UNMAP, MARK and other widths.
    """
    trace = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        # Skip non-access lines (VERSION, PCIDEV, MAP, UNMAP, MARK)
        if parts[0] in ("VERSION", "PCIDEV", "MAP", "UNMAP", "MARK"):
            continue
        # Access lines: R/W <width> <timestamp> <mapid> <address> <value> <pc> <something>
        # Minimum 8 fields for a valid access line
        if len(parts) < 8:
            continue
        width = parts[1]
        if width != "4":
            continue
        op = parts[0]
        if op not in ("R", "W"):
            continue
        try:
            address = int(parts[4], 16)
        except ValueError:
            continue
        try:
            value = int(parts[5], 16)
        except ValueError:
            continue
        if bar0 <= address < bar0 + size:
            offset = address - bar0
            trace.append((op, offset, value))
    return trace


def compare(expected, actual, writes_only=False, ignore_read_values=False,
            ignore=(), masks=None):
    """Compare two traces in order.

    Args:
        expected: list of (op, offset, value)
        actual: list of (op, offset, value)
        writes_only: if True, drop all reads from both traces
        ignore_read_values: if True, compare only the offset of reads
        ignore: set of offsets to drop from both traces
        masks: dict mapping offset -> bitmask of bits to compare

    Returns:
        dict with keys: equal (bool), matched (int),
        mismatch (None or dict with kind, expected_index, actual_index,
        expected, actual)
    """
    if masks is None:
        masks = {}
    ignore = set(ignore)

    # Build filtered traces with original indices preserved
    def filter_trace(trace):
        filtered = []
        for idx, entry in enumerate(trace):
            op, offset, value = entry
            if writes_only and op == "R":
                continue
            if offset in ignore:
                continue
            filtered.append((idx, entry))
        return filtered

    ef = filter_trace(expected)
    af = filter_trace(actual)

    matched = 0
    max_len = max(len(ef), len(af))

    for i in range(max_len):
        e_idx_orig = None
        a_idx_orig = None
        e_entry = None
        a_entry = None

        if i < len(ef):
            e_idx_orig, e_entry = ef[i]
        if i < len(af):
            a_idx_orig, a_entry = af[i]

        # If one trace ended, report missing or extra
        if e_entry is None:
            # Expected ended first; actual has more -> "extra"
            return {
                "equal": False,
                "matched": matched,
                "mismatch": {
                    "kind": "extra",
                    "expected_index": e_idx_orig,
                    "actual_index": a_idx_orig,
                    "expected": None,
                    "actual": a_entry,
                }
            }
        if a_entry is None:
            # Actual ended first; expected has more -> "missing"
            return {
                "equal": False,
                "matched": matched,
                "mismatch": {
                    "kind": "missing",
                    "expected_index": e_idx_orig,
                    "actual_index": a_idx_orig,
                    "expected": e_entry,
                    "actual": None,
                }
            }

        e_op, e_off, e_val = e_entry
        a_op, a_off, a_val = a_entry

        # Compare op first
        if e_op != a_op:
            return {
                "equal": False,
                "matched": matched,
                "mismatch": {
                    "kind": "op",
                    "expected_index": e_idx_orig,
                    "actual_index": a_idx_orig,
                    "expected": e_entry,
                    "actual": a_entry,
                }
            }
        # Then offset
        if e_off != a_off:
            return {
                "equal": False,
                "matched": matched,
                "mismatch": {
                    "kind": "offset",
                    "expected_index": e_idx_orig,
                    "actual_index": a_idx_orig,
                    "expected": e_entry,
                    "actual": a_entry,
                }
            }
        # Then value
        if e_val != a_val:
            # Check if this is a read with ignore_read_values
            if ignore_read_values and e_op == "R":
                matched += 1
                continue
            # Apply masks
            mask = masks.get(e_off, 0xFFFFFFFF)
            e_masked = e_val & mask
            a_masked = a_val & mask
            if e_masked != a_masked:
                return {
                    "equal": False,
                    "matched": matched,
                    "mismatch": {
                        "kind": "value",
                        "expected_index": e_idx_orig,
                        "actual_index": a_idx_orig,
                        "expected": e_entry,
                        "actual": a_entry,
                    }
                }
            matched += 1
        else:
            matched += 1

    return {"equal": True, "matched": matched, "mismatch": None}


def load_names(names_dir):
    """Load register names from YAML files in a directory.

    Returns a dict mapping hex address strings to register names.
    Only includes entries where 'reg' equals 'address'.
    """
    names = {}
    if not _HAS_YAML:
        return names
    for fname in sorted(os.listdir(names_dir)):
        if not fname.endswith(".yaml"):
            continue
        fpath = os.path.join(names_dir, fname)
        with open(fpath, "r") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, list):
            continue
        for entry in data:
            reg = str(entry.get("reg", ""))
            addr = str(entry.get("address", ""))
            name = entry.get("name", "")
            if reg and addr and reg == addr and name:
                names[reg] = name
    return names


def main():
    parser = argparse.ArgumentParser(
        description="Compare register traces or convert mmiotrace output.")
    parser.add_argument("expected", nargs="?", help="Expected trace file")
    parser.add_argument("actual", nargs="?", help="Actual trace file")
    parser.add_argument("--writes-only", action="store_true",
                        help="Compare only writes")
    parser.add_argument("--ignore-read-values", action="store_true",
                        help="Ignore read values")
    parser.add_argument("--ignore", type=str, default="",
                        help="Comma-separated offsets to ignore")
    parser.add_argument("--mask", action="append", default=[],
                        help="Mask entries: 0xOFFSET=0xMASK")
    parser.add_argument("--names", type=str, default=None,
                        help="Directory of register YAML files")
    # Convert mode
    parser.add_argument("--convert-mmiotrace", type=str, default=None,
                        help="Input mmiotrace file")
    parser.add_argument("--bar0", type=str, default=None,
                        help="BAR0 base address for conversion")
    parser.add_argument("--output", type=str, default=None,
                        help="Output file for converted trace")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        sys.exit(2)

    # Convert mode
    if args.convert_mmiotrace is not None:
        if args.bar0 is None:
            print("Error: --bar0 required with --convert-mmiotrace",
                  file=sys.stderr)
            sys.exit(2)
        if args.output is None:
            print("Error: --output required with --convert-mmiotrace",
                  file=sys.stderr)
            sys.exit(2)
        try:
            bar0 = int(args.bar0, 16)
        except ValueError:
            print(f"Error: bad --bar0 value {args.bar0!r}", file=sys.stderr)
            sys.exit(2)
        try:
            with open(args.convert_mmiotrace, "r") as f:
                text = f.read()
        except (OSError, IOError):
            print(f"Error: cannot read {args.convert_mmiotrace}",
                  file=sys.stderr)
            sys.exit(2)
        trace = convert_mmiotrace(text, bar0)
        try:
            with open(args.output, "w") as f:
                f.write(format_trace(trace))
        except (OSError, IOError):
            print(f"Error: cannot write {args.output}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    # Compare mode: both files required
    if args.expected is None or args.actual is None:
        print("Error: two file arguments required for comparison",
              file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.expected, "r") as f:
            expected_text = f.read()
    except (OSError, IOError):
        print(f"Error: cannot read {args.expected}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.actual, "r") as f:
            actual_text = f.read()
    except (OSError, IOError):
        print(f"Error: cannot read {args.actual}", file=sys.stderr)
        sys.exit(2)

    expected_trace = parse_trace(expected_text)
    actual_trace = parse_trace(actual_text)

    # Parse ignore set
    ignore_set = set()
    if args.ignore:
        for part in args.ignore.split(","):
            part = part.strip()
            if part:
                try:
                    ignore_set.add(int(part, 16))
                except ValueError:
                    print(f"Error: bad ignore offset {part!r}",
                          file=sys.stderr)
                    sys.exit(2)

    # Parse masks
    masks = {}
    for mask_spec in args.mask:
        if "=" not in mask_spec:
            print(f"Error: bad mask spec {mask_spec!r}", file=sys.stderr)
            sys.exit(2)
        off_str, val_str = mask_spec.split("=", 1)
        try:
            masks[int(off_str, 16)] = int(val_str, 16)
        except ValueError:
            print(f"Error: bad mask value {mask_spec!r}", file=sys.stderr)
            sys.exit(2)

    result = compare(expected_trace, actual_trace,
                     writes_only=args.writes_only,
                     ignore_read_values=args.ignore_read_values,
                     ignore=ignore_set, masks=masks)

    # Load register names if --names given
    reg_names = {}
    if args.names is not None:
        reg_names = load_names(args.names)

    if result["equal"]:
        print(f"Match: {result['matched']} entries agree.")
        sys.exit(0)

    mismatch = result["mismatch"]
    kind = mismatch["kind"]
    print(f"Mismatch at entry {kind}: {result['matched']} entries matched.")

    # Re-read the original files to show context entries
    try:
        with open(args.expected, "r") as f:
            ctx_expected = parse_trace(f.read())
    except (OSError, IOError):
        ctx_expected = []
    try:
        with open(args.actual, "r") as f:
            ctx_actual = parse_trace(f.read())
    except (OSError, IOError):
        ctx_actual = []

    # Show up to 3 entries before the difference
    exp_idx = mismatch.get("expected_index")
    if exp_idx is not None and ctx_expected:
        ctx_start = max(0, exp_idx - 3)
        for ci in range(ctx_start, exp_idx):
            entry = ctx_expected[ci]
            entry_str = f"{entry[0]} 0x{entry[1]:06x} 0x{entry[2]:08x}"
            e_name = reg_names.get(f"0x{entry[1]:06x}", None)
            if e_name:
                entry_str += f"  ({e_name})"
            print(f"  (context) {entry_str}")

    print(f"  Expected index: {mismatch.get('expected_index')}")
    print(f"  Actual index:   {mismatch.get('actual_index')}")
    if mismatch.get("expected") is not None:
        e = mismatch["expected"]
        e_str = f"{e[0]} 0x{e[1]:06x} 0x{e[2]:08x}"
        e_name = reg_names.get(f"0x{e[1]:06x}", None)
        if e_name:
            e_str += f"  ({e_name})"
        print(f"  Expected: {e_str}")
    else:
        print(f"  Expected: <none>")
    if mismatch.get("actual") is not None:
        a = mismatch["actual"]
        a_str = f"{a[0]} 0x{a[1]:06x} 0x{a[2]:08x}"
        a_name = reg_names.get(f"0x{a[1]:06x}", None)
        if a_name:
            a_str += f"  ({a_name})"
        print(f"  Actual:   {a_str}")
    else:
        print(f"  Actual:   <none>")

    sys.exit(1)


if __name__ == "__main__":
    main()
