#!/usr/bin/env python3
"""Own tests for the register-trace comparison tool (task D4).

Run: python3 tests/test_compare_traces.py   (from the repository root)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import compare_register_traces as crt

checks = failures = 0


def check(cond, what):
    global checks, failures
    checks += 1
    if not cond:
        failures += 1
        print("FAIL:", what)


# --- parse_trace extras -------------------------------------------------------
# Hex in upper case
t = crt.parse_trace("R 0XABC 0XDEAD\n")
check(t == [("R", 0xABC, 0xDEAD)], "parse_trace upper-case hex")

# Multiple comments and blank lines
t = crt.parse_trace("# header\n\nR 0x100 0x1\n# mid\n\n\nW 0x200 0x2\n")
check(t == [("R", 0x100, 0x1), ("W", 0x200, 0x2)],
      "parse_trace multiple comments and blanks")

# --- convert_mmiotrace extras -------------------------------------------------
# mmiotrace line with too few fields (should be skipped silently)
MMIO_SHORT = """R 4 12.000200 1 0xf6000000
W 4 12.000300 1 0xf6000200 0x100 0x0 0
"""
c = crt.convert_mmiotrace(MMIO_SHORT, 0xf6000000)
check(c == [("W", 0x000200, 0x100)],
      "convert_mmiotrace skips too-short line")

# mmiotrace with width 1 and 2 (should be skipped)
MMIO_WIDTHS = """R 1 12.000200 1 0xf6000000 0xab 0x0 0
R 2 12.000300 1 0xf6000000 0xabcd 0x0 0
W 4 12.000400 1 0xf6000000 0x1234 0x0 0
"""
c = crt.convert_mmiotrace(MMIO_WIDTHS, 0xf6000000)
check(c == [("W", 0x0, 0x1234)],
      "convert_mmiotrace skips non-4-byte widths")

# mmiotrace address outside the BAR range (should be skipped)
# BAR0 = 0xf6000000, default size = 0x1000000 → valid range [0xf6000000, 0xf7000000)
MMIO_OUTSIDE = """W 4 12.000200 1 0xf7000000 0x555 0x0 0
W 4 12.000300 1 0xf6000200 0x100 0x0 0
"""
c = crt.convert_mmiotrace(MMIO_OUTSIDE, 0xf6000000)
check(c == [("W", 0x000200, 0x100)],
      "convert_mmiotrace skips address outside range")

# --- compare extras -----------------------------------------------------------
# Mask and writes_only together
A = [("W", 0x200, 0x100), ("R", 0x100, 0x0), ("W", 0x2140, 0x7fffffff),
     ("W", 0x2100, 0xffffffff)]
B = list(A)
B[0] = ("W", 0x200, 0x101)  # bit 0 differs
B[2] = ("W", 0x2140, 0x80000000)  # top bit differs
r = crt.compare(A, B, writes_only=True, masks={0x200: 0xFFFFFFF0, 0x2140: 0x0})
check(r["equal"] is True and r["matched"] == 3,
      "mask + writes_only together: both filters apply")

# Mismatch at index 0
A = [("W", 0x200, 0x100), ("R", 0x100, 0x0)]
B = [("W", 0x200, 0x999)]
r = crt.compare(A, B)
m = r["mismatch"]
check(m["kind"] == "value" and m["expected_index"] == 0 and m["actual_index"] == 0,
      "mismatch at index 0")

# Empty expected trace
A = [("W", 0x200, 0x100)]
r = crt.compare([], A)
check(r["equal"] is False and r["mismatch"]["kind"] == "extra"
      and r["mismatch"]["expected_index"] is None,
      "empty expected trace: extra")

# Empty actual trace
r = crt.compare(A, [])
check(r["equal"] is False and r["mismatch"]["kind"] == "missing"
      and r["mismatch"]["actual_index"] is None,
      "empty actual trace: missing")

# Both traces empty
r = crt.compare([], [])
check(r["equal"] is True and r["matched"] == 0,
      "both traces empty: equal")

# --- format_trace extras ------------------------------------------------------
# format_trace on empty trace
check(crt.format_trace([]) == "", "format_trace empty trace")

# format_trace produces consistent output (round-trip)
t = [("R", 0x0, 0), ("W", 0xFFFFF, 0xFFFFFFFF)]
formatted = crt.format_trace(t)
re_parsed = crt.parse_trace(formatted)
check(re_parsed == t, "format_trace round-trip")

# --- compare with masks (more) ------------------------------------------------
A = [("W", 0x100, 0xABCDEF01)]
B = [("W", 0x100, 0xABCDEF02)]
# Mask keeps only bit 2 (hides bits 0 and 1 where they differ)
r = crt.compare(A, B, masks={0x100: 0xFFFFFFFC})
check(r["equal"] is True, "mask hides all differing bits")
r = crt.compare(A, B, masks={0x100: 0x1})
check(r["equal"] is False, "mask keeps the differing bit")

# --- CLI extras ---------------------------------------------------------------
import subprocess
import tempfile

with tempfile.TemporaryDirectory() as td:
    def write(name, text):
        p = os.path.join(td, name)
        with open(p, "w") as f:
            f.write(text)
        return p

    def run(*args):
        return subprocess.run([sys.executable,
                               os.path.join(os.path.dirname(__file__),
                                            "..", "tools",
                                            "compare_register_traces.py")]
                              + list(args),
                              capture_output=True, text=True)

    # --mask with wrong format
    exp = write("exp.txt", "W 0x100 0x1\n")
    act = write("act.txt", "W 0x100 0x2\n")
    r = run(exp, act, "--mask", "badvalue")
    check(r.returncode == 2, "CLI bad --mask value: exit 2")

    # --convert-mmiotrace without --bar0
    mm = write("mmio.txt", "W 4 12.000200 1 0xf6000000 0x100 0x0 0\n")
    r = run("--convert-mmiotrace", mm)
    check(r.returncode == 2, "CLI --convert-mmiotrace without --bar0: exit 2")

    # CLI missing output file dir
    r = run("--convert-mmiotrace", mm, "--bar0", "0xf6000000",
            "--output", "/nonexistent/dir/out.txt")
    check(r.returncode == 2, "CLI --convert-mmiotrace unwritable output: exit 2")

print(f"test_compare_traces: {checks} checks, {failures} failures")

if __name__ == "__main__":
    sys.exit(0 if failures == 0 else 1)
