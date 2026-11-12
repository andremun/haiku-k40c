#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Record the verified GR host model as an op program for the native driver.

The model (tools/gr/model.py) runs once against a recorder. Each access becomes
one op. Values that only the running driver knows (buffer addresses, register
contents) stay symbolic: they are slots. The result is three stages (power
gating off, engine start, golden context) and the per-channel patch list.

  program.py --check         run the recorded program against the Linux trace
  program.py --output DIR    write ProgramData.cpp and gr_trace.txt (test input)

The generated C++ is build output. It is not stored in the repository: it holds
the Nouveau register tables and the four microcode arrays (MIT, notice kept).
HOST_ONLY: a trace match is not card evidence.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model
import oracle
import tables

KINDS = ("Write", "WriteSlot", "Read", "Expect", "Mask", "MaskSlot", "Poll", "WaitIdle", "Delay", "Hook")
INPUTS = ("Instance", "PagePool", "Bundle", "Attrib", "MmuWrite", "MmuRead")
NONE = 0xFF
# Values that the reference run read on this card (KNOWN, trace lines 616417-616433,
# 616554-616557, 618711). The driver stops when the card answers differently.
KNOWN = {0x409604: 0x00060005, 0x40912C: 0x00081103, 0x409108: 0x20402050,
         0x41A12C: 0x00081103, 0x41A108: 0x20201028, 0x409804: 0x0004EA00}
for _gpc in range(5):
    KNOWN[model.gpc_unit(_gpc, 0x2608)] = 0x00040003
    KNOWN[model.gpc_unit(_gpc, 0x0C30)] = 0x5
    KNOWN[model.gpc_unit(_gpc, 0x0C34)] = 0x2


class Slot:
    """A run-time value: ((slot >> shift) & and) | or, 32 bits."""

    def __init__(self, index, shift=0, and_=0xFFFFFFFF, or_=0):
        self.index, self.shift, self.and_, self.or_ = index, shift, and_, or_

    def __rshift__(self, count):
        if self.and_ != 0xFFFFFFFF or self.or_:
            raise ValueError("shift after mask is not supported")
        return Slot(self.index, self.shift + count)

    def __and__(self, bits):
        if self.or_:
            raise ValueError("and after or is not supported")
        return Slot(self.index, self.shift, self.and_ & bits)

    def __or__(self, bits):
        return Slot(self.index, self.shift, self.and_, self.or_ | bits)

    __ror__ = __or__


class Recorder:
    def __init__(self):
        self.ops, self.patches, self.slots = [], [], len(INPUTS)
        self.falcon = {}  # Data-segment model of the two Falcons for the csdata reads.

    def emit(self, kind, addr=0, a=0, b=0, slot=NONE, shift=0):
        self.ops.append((kind, slot, shift, addr & 0xFFFFFFFF, a & 0xFFFFFFFF, b & 0xFFFFFFFF))

    def new(self):
        if self.slots >= 64:
            raise ValueError("too many slots")
        self.slots += 1
        return Slot(self.slots - 1)

    def data_port(self, addr):
        base = addr & ~0xFFF
        return self.falcon.setdefault(base, dict(pointer=0, flags=0, words={}))

    def rd(self, addr):
        if addr & 0xFFF == 0x1C4 and (addr & ~0xFFF) in (0x409000, 0x41A000):
            port = self.data_port(addr)
            value = port["words"].get(port["pointer"], 0)
            if port["flags"] & 0x02000000:  # Read with increment (gf100.c:1716).
                port["pointer"] += 4
            self.emit("Expect", addr, 0xFFFFFFFF, value)
            return value
        if addr in KNOWN:
            self.emit("Expect", addr, 0xFFFFFFFF, KNOWN[addr])
            return KNOWN[addr]
        slot = self.new()
        self.emit("Read", addr, slot=slot.index)
        return slot

    def wr(self, addr, value):
        if isinstance(value, Slot):
            self.emit("WriteSlot", addr, value.and_, value.or_, value.index, value.shift)
            return
        if addr & 0xFFF == 0x1C0 and (addr & ~0xFFF) in (0x409000, 0x41A000):
            port = self.data_port(addr)
            port["pointer"], port["flags"] = value & 0xFFFC, value & 0xFF000000
        if addr & 0xFFF == 0x1C4 and (addr & ~0xFFF) in (0x409000, 0x41A000):
            port = self.data_port(addr)
            port["words"][port["pointer"]] = value & 0xFFFFFFFF
            if port["flags"] & 0x01000000:  # Write with increment (falcon/v1.c:76).
                port["pointer"] += 4
        self.emit("Write", addr, value)

    def patch(self, addr, value):
        self.wr(addr, value)
        self.patches.append((addr, value))

    def mask(self, addr, clear, value):
        if isinstance(value, Slot):
            if value.shift or value.and_ != 0xFFFFFFFF or value.or_:
                raise ValueError("masked slot expression is not supported")
            self.emit("MaskSlot", addr, clear, slot=value.index)
            return None
        old = self.new()
        self.emit("Mask", addr, clear, value, old.index)
        return old

    def poll(self, addr, bits, want):
        self.emit("Poll", addr, bits, want)

    def wait_idle(self):
        self.emit("WaitIdle")

    def delay(self, microseconds):
        self.emit("Delay", a=microseconds)

    def context_pointer(self):
        self.emit("Hook", a=1)


def record():
    """Return dict(stage -> ops), the patch list and the slot count."""
    inits, packs = tables.parse()
    inputs = {name: Slot(index) for index, name in enumerate(INPUTS)}
    stages, recorder = {}, Recorder()

    def stage(name):
        stages[name] = recorder.ops
        recorder.ops = []

    model.pgob(recorder)
    stage("gating")
    topology = model.Topology(recorder)
    for reg in (0x40912C, 0x409108, 0x41A12C, 0x41A108):
        recorder.rd(reg)
    model.init(recorder, topology, inits, packs, inputs["MmuWrite"], inputs["MmuRead"])
    if model.ctxctl(recorder, inits, packs) != KNOWN[0x409804]:
        raise ValueError("context size")
    stage("start")
    recorder.patches = []
    model.generate(recorder, topology, inits, packs, inputs["Instance"], inputs["PagePool"],
                   inputs["Bundle"], inputs["Attrib"])
    stage("golden")
    return stages, recorder.patches, recorder.slots, topology


class Interpreter:
    """Reference semantics of the ops; the native Runner (src/gr/Runner.cpp) is the same."""

    def __init__(self, io, slots, inputs):
        self.io, self.slots = io, [0] * slots
        self.slots[: len(inputs)] = inputs

    def run(self, ops):
        io, slots = self.io, self.slots
        for kind, slot, shift, addr, a, b in ops:
            if kind == "Write":
                io.wr(addr, a)
            elif kind == "WriteSlot":
                io.wr(addr, ((slots[slot] >> shift) & a) | b)
            elif kind == "Read":
                slots[slot] = io.rd(addr)
            elif kind == "Expect":
                value = io.rd(addr)
                if value & a != b:
                    raise AssertionError(f"expected {b:x} at {addr:06x}, read {value:x}")
            elif kind == "Mask":
                old = io.rd(addr)
                io.wr(addr, (old & ~a & 0xFFFFFFFF) | b)
                if slot != NONE:
                    slots[slot] = old
            elif kind == "MaskSlot":
                io.wr(addr, (io.rd(addr) & ~a & 0xFFFFFFFF) | (slots[slot] & 0xFFFFFFFF))
            elif kind == "Poll":
                model.poll(io, addr, a, b, "poll")
            elif kind == "WaitIdle":
                model.wait_idle(io)
            elif kind in ("Delay", "Hook"):
                pass
            else:
                raise ValueError(kind)


def trace_inputs():
    """The run data of the reference run, in INPUTS order."""
    def last(block, wanted):
        # The context register lists write some of these registers first with
        # table values; the run data is the last write of the block.
        return {addr: value for _, op, addr, value in oracle.accesses(*block) if op == "W" and addr in wanted}

    start = last(oracle.START, (0x4188B4, 0x4188B8))
    golden = last(oracle.GOLDEN, (0x409500, 0x40800C, 0x408004, 0x418810))
    return [(golden[0x409500] & 0x7FFFFFFF) << 12, golden[0x40800C] << 8, golden[0x408004] << 8,
            (golden[0x418810] & 0x7FFFFFFF) << 12, start[0x4188B4] << 8, start[0x4188B8] << 8]


def blocks():
    """Trace accesses per stage, in the order the program meets them."""
    start = oracle.accesses(*oracle.ONEINIT) + oracle.accesses(*oracle.START)
    return dict(gating=oracle.accesses(*oracle.PGOB[0]), start=start,
                golden=oracle.accesses(*oracle.GOLDEN, gr_only=True))


def check():
    stages, patches, slots, _ = record()
    inputs, total = trace_inputs(), 0
    interpreter = None
    for name, rows in blocks().items():
        replay = oracle.Replay(rows)
        if interpreter is None:
            interpreter = Interpreter(replay, slots, inputs)
        interpreter.io = replay
        interpreter.run(stages[name])
        replay.done()
        total += len(rows)
    return stages, patches, slots, total


def cpp(stages, patches, slots):
    lines = [
        "// Generated by tools/gr/program.py. Do not edit. Build output, not repository content.",
        "// Register tables and microcode words come from the Linux kernel Nouveau driver,",
        "// drivers/gpu/drm/nouveau/nvkm/engine/gr (MIT License; Copyright Red Hat Inc. and others;",
        "// microcode: Copyright 2013 Red Hat Inc., author Ben Skeggs). Pin: reference/MANIFEST.md.",
        '#include "gr/Program.h"',
        "namespace k40::gr {",
        f"const unsigned slotCount={slots};",
    ]
    for name, ops in stages.items():
        lines.append(f"static const Op {name}Ops[]={{")
        for kind, slot, shift, addr, a, b in ops:
            lines.append(f"{{Kind::{kind},{slot},{shift},0x{addr:x},0x{a:x},0x{b:x}}},")
        lines.append("};")
        lines.append(f"const Stage {name}={{{name}Ops,{len(ops)}}};")
    lines.append("const Patch patchList[]={")
    for addr, value in patches:
        if isinstance(value, Slot):
            lines.append(f"{{0x{addr:x},{value.index},{value.shift},0x{value.and_:x},0x{value.or_:x}}},")
        else:
            lines.append(f"{{0x{addr:x},{NONE},0,0,0x{value & 0xFFFFFFFF:x}}},")
    lines.append("};")
    lines.append(f"const unsigned patchCount={len(patches)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def fixture():
    """Trace accesses and run data for the native Runner host test."""
    lines = ["I " + " ".join(f"{value:x}" for value in trace_inputs())]
    for name, rows in blocks().items():
        lines.append("S " + name)
        lines.extend(f"{op} {addr:x} {value:x}" for _, op, addr, value in rows)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args()
    stages, patches, slots, total = check()
    count = sum(len(ops) for ops in stages.values())
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "ProgramData.cpp").write_text(cpp(stages, patches, slots))
        (args.output / "gr_trace.txt").write_text(fixture())
    print(f"GR program: {count} ops in 3 stages, {len(patches)} patch entries, {slots} slots; "
          f"{total} trace accesses reproduced by the recorded program, 0 differences; HOST_ONLY")


if __name__ == "__main__":
    main()
