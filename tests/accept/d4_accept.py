#!/usr/bin/env python3
"""Acceptance test for task D4, written by the scaffold. Do not edit:
`make check` compares this file with a recorded hash.

Run: python3 tests/accept/d4_accept.py   (from the repository root)
"""
import importlib.util
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "compare_register_traces.py")
spec = importlib.util.spec_from_file_location("crt", TOOL)
crt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crt)

checks = failures = 0


def check(cond, what):
    global checks, failures
    checks += 1
    if not cond:
        failures += 1
        print("FAIL:", what)


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


# --- parse_trace: the text format of task D1 -------------------------------
t = crt.parse_trace("# boot\nR 0x000000 0x0f1000a1\n\nW 0x000200 0x00000100  # enable\n")
check(t == [("R", 0x000000, 0x0f1000a1), ("W", 0x000200, 0x00000100)], "parse_trace basic")
check(crt.parse_trace("") == [], "parse_trace empty")
check(raises(ValueError, lambda: crt.parse_trace("X 0x0 0x0\n")), "parse_trace bad op")
check(raises(ValueError, lambda: crt.parse_trace("R 0x0\n")), "parse_trace missing value")
check(crt.format_trace(t) == "R 0x000000 0x0f1000a1\nW 0x000200 0x00000100\n", "format_trace")

# --- convert_mmiotrace: Linux mmiotrace text to that format ------------------
MMIO = """VERSION 20070824
PCIDEV 0300 10de1024 28 f6000000 e000000c 0 f000000c 0 e001 7f000002 1000000 10000000 0 2000000 0 80 80000 nvidia
MAP 12.000100 1 0xf6000000 0xffffc90004000000 0x1000000 0x0 0
R 4 12.000200 1 0xf6000000 0xf1000a1 0x0 0
W 4 12.000300 1 0xf6000200 0x100 0x0 0
R 1 12.000400 1 0xf6000300 0xab 0x0 0
R 4 12.000500 2 0xe0000010 0x1234 0x0 0
W 4 12.000600 1 0xf6002140 0x7fffffff 0x0 0
MARK 12.000700 start fifo
UNMAP 12.000800 1 0x0 0
"""
c = crt.convert_mmiotrace(MMIO, 0xf6000000)
check(c == [("R", 0x000000, 0x0f1000a1), ("W", 0x000200, 0x00000100), ("W", 0x002140, 0x7fffffff)],
      "convert_mmiotrace keeps 4-byte accesses inside the 16 MiB register area")
check(crt.convert_mmiotrace(MMIO, 0xe0000000) == [("R", 0x000010, 0x1234)], "convert_mmiotrace other base")
check(crt.convert_mmiotrace("", 0xf6000000) == [], "convert_mmiotrace empty")

# --- compare ----------------------------------------------------------------
A = [("W", 0x200, 0x100), ("R", 0x100, 0x0), ("W", 0x2140, 0x7fffffff), ("W", 0x2100, 0xffffffff)]
r = crt.compare(A, list(A))
check(r["equal"] is True and r["matched"] == 4 and r["mismatch"] is None, "compare equal")

B = list(A)
B[2] = ("W", 0x2140, 0x7ffffffe)
r = crt.compare(A, B)
check(r["equal"] is False and r["matched"] == 2, "compare value mismatch: matched count")
m = r["mismatch"]
check(m["kind"] == "value" and m["expected_index"] == 2 and m["actual_index"] == 2, "value mismatch position")
check(m["expected"] == ("W", 0x2140, 0x7fffffff) and m["actual"] == ("W", 0x2140, 0x7ffffffe), "value mismatch entries")

B = list(A)
B[2] = ("W", 0x2144, 0x7fffffff)
check(crt.compare(A, B)["mismatch"]["kind"] == "offset", "offset mismatch")
B = list(A)
B[1] = ("W", 0x100, 0x0)
check(crt.compare(A, B)["mismatch"]["kind"] == "op", "op mismatch")

r = crt.compare(A, A[:3])
check(r["mismatch"]["kind"] == "missing" and r["mismatch"]["expected_index"] == 3
      and r["mismatch"]["actual"] is None, "actual trace ends early")
r = crt.compare(A[:3], A)
check(r["mismatch"]["kind"] == "extra" and r["mismatch"]["actual_index"] == 3
      and r["mismatch"]["expected"] is None, "actual trace has more")

# reads return what the hardware holds: a read value may differ between runs
B = list(A)
B[1] = ("R", 0x100, 0x55)
check(crt.compare(A, B)["equal"] is False, "read value differs: mismatch by default")
check(crt.compare(A, B, ignore_read_values=True)["equal"] is True, "ignore_read_values")
# writes only
B = [a for a in A if a[0] == "W"]
check(crt.compare(A, B)["equal"] is False, "reads missing: mismatch by default")
r = crt.compare(A, B, writes_only=True)
check(r["equal"] is True and r["matched"] == 3, "writes_only")
# ignored offsets are dropped from both sides
B = [("W", 0x200, 0x100), ("W", 0x9999 & ~3, 0x1), ("R", 0x100, 0x0), ("W", 0x2140, 0x7fffffff),
     ("W", 0x2100, 0xffffffff)]
check(crt.compare(A, B)["equal"] is False, "extra write: mismatch by default")
check(crt.compare(A, B, ignore={0x9998})["equal"] is True, "ignore offsets")
# a mask selects the bits that are compared
B = list(A)
B[0] = ("W", 0x200, 0x101)
check(crt.compare(A, B)["equal"] is False, "bit differs")
check(crt.compare(A, B, masks={0x200: 0xfffffff0})["equal"] is True, "mask hides the bit")
check(crt.compare(A, B, masks={0x200: 0x0000000f})["equal"] is False, "mask keeps the bit")
# indices refer to the traces as given, also when entries are skipped
B = [a for a in A if a[0] == "W"]
B[2] = ("W", 0x2100, 0xfffffffe)
m = crt.compare(A, B, writes_only=True)["mismatch"]
check(m["expected_index"] == 3 and m["actual_index"] == 2 and m["kind"] == "value", "indices with writes_only")

# --- command line -------------------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    def write(name, text):
        p = os.path.join(d, name)
        with open(p, "w") as f:
            f.write(text)
        return p

    def run(*args):
        return subprocess.run([sys.executable, TOOL] + list(args), capture_output=True, text=True)

    exp = write("linux.txt", crt.format_trace(A))
    same = write("same.txt", "# haiku\n" + crt.format_trace(A))
    bad = list(A)
    bad[2] = ("W", 0x2140, 0x7ffffffe)
    diff = write("diff.txt", crt.format_trace(bad))
    r = run(exp, same)
    check(r.returncode == 0 and "match" in r.stdout.lower(), "CLI equal: exit 0")
    r = run(exp, diff)
    check(r.returncode == 1, "CLI mismatch: exit 1")
    check("0x002140" in r.stdout and "0x7fffffff" in r.stdout and "0x7ffffffe" in r.stdout,
          "CLI mismatch: shows offset, expected value and actual value")
    check("0x000100" in r.stdout, "CLI mismatch: shows the entries before it (context)")
    r = run(exp, diff, "--mask", "0x002140=0xfffffff0")
    check(r.returncode == 0, "CLI --mask")
    r = run(exp, diff, "--ignore", "0x002140")
    check(r.returncode == 0, "CLI --ignore")
    wo = write("wo.txt", crt.format_trace([a for a in A if a[0] == "W"]))
    check(run(exp, wo).returncode == 1 and run(exp, wo, "--writes-only").returncode == 0, "CLI --writes-only")
    rd = list(A)
    rd[1] = ("R", 0x100, 0x77)
    rdf = write("rd.txt", crt.format_trace(rd))
    check(run(exp, rdf).returncode == 1 and run(exp, rdf, "--ignore-read-values").returncode == 0,
          "CLI --ignore-read-values")
    check(run(exp, os.path.join(d, "nofile.txt")).returncode == 2, "CLI missing file: exit 2")
    check(run(exp).returncode == 2, "CLI missing argument: exit 2")
    mm = write("mmio.txt", MMIO)
    out = os.path.join(d, "conv.txt")
    r = run("--convert-mmiotrace", mm, "--bar0", "0xf6000000", "--output", out)
    check(r.returncode == 0 and os.path.exists(out)
          and open(out).read() == "R 0x000000 0x0f1000a1\nW 0x000200 0x00000100\nW 0x002140 0x7fffffff\n",
          "CLI --convert-mmiotrace")
    # register names from the database of task C1
    r = run(exp, diff, "--names", os.path.join(ROOT, "hardware", "registers"))
    check(r.returncode == 1 and "PFIFO.INTR_EN" in r.stdout, "CLI --names shows the register name")

print(f"d4_accept: {checks} checks, {failures} failures")
sys.exit(0 if failures == 0 else 1)
