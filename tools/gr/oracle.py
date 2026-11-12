#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Trace oracle: run the GR host model against the Linux reference trace.

The model reads from the trace and its writes are compared with the trace, in
order, access by access. Timer reads (0x9400, 0x9410: kernel wait loops) are
skipped. The first difference stops the comparison. --check writes nothing
and exits 0 only with zero differences. HOST_ONLY, not card evidence.
"""
import argparse
import lzma
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model
import tables

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "reference/linux-run/mmiotrace.txt.xz"
BAR0 = 0xC1000000  # mmiotrace line 10: MAP of 16 MiB.
TIMER = (0x9400, 0x9410)  # timer/nv04.c read by nvkm_msec wait loops.
# Blocks of the reference run (work/S3GR/FINDINGS.md).
ONEINIT = (616417, 616433)
START = (616554, 618711)


def accesses(first, last):
    rows = []
    with lzma.open(TRACE, "rt") as trace:
        for number, line in enumerate(trace, 1):
            if number < first:
                continue
            if number > last:
                break
            part = line.split()
            if part and part[0] in ("R", "W") and len(part) >= 6:
                address = int(part[4], 16) - BAR0
                if 0 <= address < 0x1000000 and address not in TIMER:
                    rows.append((number, part[0], address, int(part[5], 16)))
    return rows


class Replay:
    """Io for the model: every access must be the next access of the trace."""

    def __init__(self, rows):
        self.rows, self.index = rows, 0

    def step(self, op, addr, value=None):
        if self.index >= len(self.rows):
            raise AssertionError(f"model continues after the trace block: {op} {addr:06x}")
        number, top, taddr, tvalue = self.rows[self.index]
        if (top, taddr) != (op, addr) or (op == "W" and tvalue != value):
            got = f"{op} {addr:06x}" + (f" {value:x}" if op == "W" else "")
            raise AssertionError(f"access {self.index}: trace line {number} is {top} {taddr:06x} {tvalue:x}, model gives {got}")
        self.index += 1
        return tvalue

    def rd(self, addr):
        return self.step("R", addr)

    def wr(self, addr, value):
        self.step("W", addr, value & 0xFFFFFFFF)

    def done(self):
        if self.index != len(self.rows):
            number, op, addr, value = self.rows[self.index]
            raise AssertionError(f"trace continues at line {number}: {op} {addr:06x} {value:x}; {len(self.rows) - self.index} accesses not modelled")


def run():
    inits, packs = tables.parse()
    one = Replay(accesses(*ONEINIT))
    topology = model.Topology(one)
    one.done()
    rows = accesses(*START)
    start = Replay(rows)
    # gf100_gr_init_ctxctl reads the Falcon capabilities before init (trace 616554-616557).
    for reg in (0x40912C, 0x409108, 0x41A12C, 0x41A108):
        start.rd(reg)
    # The addresses of the two MMU fault pages are run data: take them from the trace.
    by = {addr: value for _, op, addr, value in rows if op == "W" and addr in (0x4188B4, 0x4188B8)}
    model.init(start, topology, inits, packs, by[0x4188B4] << 8, by[0x4188B8] << 8)
    size = model.ctxctl(start, inits, packs)
    start.done()
    return dict(
        gpc=topology.gpc_nr, tpc=topology.tpc_nr, rop=topology.rop_nr, ppc_mask=topology.ppc_mask,
        accesses=len(one.rows) + len(rows), context_bytes=size,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    result = run()
    print(f"GR engine start: {result['accesses']} trace accesses reproduced, 0 differences; "
          f"{result['gpc']} GPC, TPC {result['tpc']}, {result['rop']} ROP, context image {result['context_bytes']} bytes; HOST_ONLY")


if __name__ == "__main__":
    main()
