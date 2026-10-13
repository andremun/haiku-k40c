#!/usr/bin/env python3
"""Print a part of the register trace of the reference run, with names.

    tools/trace_lines.py FIRST LAST          lines FIRST..LAST of the trace
    tools/trace_lines.py FIRST LAST --bar0   only the accesses to BAR 0
    tools/trace_lines.py --reg 0x409504      the job-phase accesses of one register
    tools/trace_lines.py --runs FIRST LAST   the runs (docs/tasks/C5b.md) that
                                             have a line in FIRST..LAST

Output, one line for each access:
    LINE TIME R|W BAR:OFFSET VALUE NAME
NAME is the name of tools/rnndb.py for BAR 0, "-" when the database has
none, and "bar3"/"bar1" for the other BARs (instance memory and the
channel control area: the trace does not say what the offset means).
At most 120 lines are printed; a longer range prints the first 60 and the
last 60 and says how many were left out. Runs of the same BAR 3 mapping
are shortened to one line with a count.

Written by the scaffold (2026-10-13). The trace is
reference/linux-run/mmiotrace.txt.xz; line numbers are those of
analysis/linux_run_trace.md.
"""
import json
import lzma
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import rnndb  # noqa: E402

TRACE = os.path.join(ROOT, "reference", "linux-run", "mmiotrace.txt.xz")
BARS = {0: 0xc1000000, 1: 0x800000000, 3: 0x810000000}
SIZES = {0: 0x1000000, 1: 0x10000000, 3: 0x2000000}


def bar_of(phys):
    for b, base in BARS.items():
        if base <= phys < base + SIZES[b]:
            return b, phys - base
    return None, phys


def accesses(first, last, reg=None):
    names = {}
    for n, line in enumerate(lzma.open(TRACE, "rt"), 1):
        if n > last:
            break
        if n < first:
            continue
        p = line.split()
        if not p:
            continue
        if p[0] in ("MAP", "UNMAP", "MARK"):
            if reg is None:
                yield n, None, "%d %s" % (n, " ".join(p))
            continue
        if p[0] not in ("R", "W"):
            continue
        bar, off = bar_of(int(p[4], 16))
        if reg is not None and (bar != 0 or off != reg):
            continue
        if bar == 0:
            if off not in names:
                r = rnndb.lookup(off)
                names[off] = r["name"] if r else "-"
            name = names[off]
            where = "0:0x%06x" % off
        else:
            name = "bar%s" % bar
            where = "%s:0x%x" % (bar, off)
        yield n, (bar, p[3]), "%d %s %s %s %s %s" % (n, p[2], p[0], where, p[5], name)


def main(argv):
    if len(argv) >= 3 and argv[0] == "--runs":
        j = json.load(open(os.path.join(ROOT, "analysis", "linux_run_trace.json")))
        a, b = int(argv[1]), int(argv[2])
        for i, r in enumerate(j["job_runs"], 1):
            if r["last_line"] >= a and r["first_line"] <= b:
                print("run %d lines %d-%d %s reads %d writes %d" % (
                    i, r["first_line"], r["last_line"], r["domain"], r["reads"], r["writes"]))
        return 0
    bar0_only = "--bar0" in argv
    argv = [x for x in argv if x != "--bar0"]
    if len(argv) == 2 and argv[0] == "--reg":
        j = json.load(open(os.path.join(ROOT, "analysis", "linux_run_trace.json")))
        ph = j["phases"]["job"]
        rows = [t for _, _, t in accesses(ph["first_line"], ph["last_line"], int(argv[1], 16))]
    elif len(argv) == 2:
        rows, prev = [], None
        for n, key, text in accesses(int(argv[0]), int(argv[1])):
            if key is not None and key[0] != 0:
                if bar0_only:
                    continue
                if prev is not None and prev[0] == key:
                    prev[1] += 1
                    rows[-1] = "%s   (+%d more accesses of mapping %s, to line %d)" % (
                        prev[2], prev[1], key[1], n)
                    continue
                prev = [key, 0, text]
            else:
                prev = None
            rows.append(text)
    else:
        print(__doc__)
        return 2
    if len(rows) > 120:
        left = len(rows) - 120
        rows = rows[:60] + ["... %d lines left out ..." % left] + rows[-60:]
    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
