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
PGOB = ((616297, 616416), (616434, 616553))  # gk110_pmu_pgob, run twice in the reference run.
ONEINIT = (616417, 616433)
START = (616554, 618711)
GOLDEN = (619424, 730273)
# Accesses of the golden block that belong to the model. Other BAR0 accesses in
# these lines are instance-memory work (BAR flush, TLB invalidate), not GR.
OTHER = (0x000260, 0x000200, 0x002640, 0x17E91C, 0x17E920)


def accesses(first, last, gr_only=False):
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
                if gr_only and not (0x400000 <= address < 0x600000 or address in OTHER):
                    continue
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

    def patch(self, addr, value):
        self.wr(addr, value)  # Context generation: chan->mmio is not set (ctxgf100.c:997-1000).

    def delay(self, microseconds):
        pass

    def context_pointer(self):
        pass  # Instance-memory write, not in BAR0.

    def done(self):
        if self.index != len(self.rows):
            number, op, addr, value = self.rows[self.index]
            raise AssertionError(f"trace continues at line {number}: {op} {addr:06x} {value:x}; {len(self.rows) - self.index} accesses not modelled")


def run():
    inits, packs = tables.parse()
    gating = 0
    for block in PGOB:
        replay = Replay(accesses(*block))
        model.pgob(replay)
        replay.done()
        gating += len(replay.rows)
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
    started = len(one.rows) + len(rows)
    rows = accesses(*GOLDEN, gr_only=True)
    golden = Replay(rows)
    run_data = {addr: value for _, op, addr, value in rows if op == "W" and addr in (0x409500, 0x40800C, 0x408004, 0x418810)}
    model.generate(golden, topology, inits, packs, (run_data[0x409500] & 0x7FFFFFFF) << 12,
                   run_data[0x40800C] << 8, run_data[0x408004] << 8, (run_data[0x418810] & 0x7FFFFFFF) << 12)
    golden.done()
    return dict(
        golden=len(rows), gating=gating,
        gpc=topology.gpc_nr, tpc=topology.tpc_nr, rop=topology.rop_nr, ppc_mask=topology.ppc_mask,
        accesses=started, context_bytes=size,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    result = run()
    print(f"GR power gating off: {result['gating']} trace accesses reproduced (two runs), 0 differences; HOST_ONLY")
    print(f"GR golden context: {result['golden']} trace accesses reproduced, 0 differences; HOST_ONLY")
    print(f"GR engine start: {result['accesses']} trace accesses reproduced, 0 differences; "
          f"{result['gpc']} GPC, TPC {result['tpc']}, {result['rop']} ROP, context image {result['context_bytes']} bytes; HOST_ONLY")


if __name__ == "__main__":
    main()
