#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Compare our per-channel register list with the list of the Linux reference run.

FECS executes this list at the first load of a channel context (fuc/hub.fuc:555-592,
686-690). The card runs s3q (with the list) and s3r (list count 0) differ only in
this list (work/S3DIAG/FINDINGS.md). Linux writes its list into a 0x1000-byte
record (engine/gr/gf100.c:455-479); the trace shows it as writes to MAP 25, lines
811337-811410 of reference/linux-run.

Our list comes from tools/gr/program.py: constant entries, and slot entries whose
value the driver fills in at run time. Slot entries are of two kinds:
- addresses of our own records (page pool, bundle, attribute buffer) in the
  channel address space (engine/gr/ctxgf100.c:1053-1057; ctxgk104.c pagepool and
  bundle). The same registers get the same values in our golden stage, where GR
  ran with them on the card (s3g, s3q).
- values read from the card (engine/gr/ctxgk104.c:863-872, LTC 0x17e91c, 0x17e920).

The two card-read entries must be written after the golden stage reads them: the
driver once wrote the list before, with 0 in both, and FECS wrote 0 into the L2
cache registers at the first load (s3q, s3s; work/S3DIAG/FINDINGS.md). This tool
does not model that order; tests/test_gr_compute.cpp checks the written list.

--check exits 0 when the registers and their order are equal, every constant value
is equal, and every slot entry is of a known kind. The default prints the table.
HOST_ONLY: not card evidence.
"""
import argparse
import lzma
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import launch
import oracle
import program

FIRST, LAST = 811337, 811410  # reference/linux-run, the list writes (work/S3DIAG/FINDINGS.md, 2026-11-16).
LIST_MAP = 25  # the MAP id of the list record in that range.
INPUT_NAMES = program.INPUTS  # slot index -> run input
READ_SLOTS = {0x17E91C, 0x17E920}  # engine/gr/ctxgk104.c:866-872.


def linux_list():
    """[(register, value)] in list order, from the trace writes to the list record."""
    words = {}
    with lzma.open(oracle.TRACE, "rt") as stream:
        for number, line in enumerate(stream, 1):
            if number < FIRST:
                continue
            if number > LAST:
                break
            parts = line.split()
            if parts and parts[0] == "W" and int(parts[3]) == LIST_MAP:
                words[int(parts[4], 16) & 0xFFF] = int(parts[5], 16)
    count = len(words) // 2
    if sorted(words) != [4 * index for index in range(2 * count)]:
        raise ValueError("Linux list words not contiguous")
    return [(words[8 * index], words[8 * index + 4]) for index in range(count)]


def our_list():
    """[(register, value or slot description)] from the recorded program."""
    _, patches, _, _ = program.record()
    layout = launch.layout()
    va = dict(PagePool=layout["PagePool"]["va"], Bundle=layout["Bundle"]["va"], Attrib=layout["Attrib"]["va"])
    rows = []
    for addr, value in patches:
        if isinstance(value, int):
            rows.append((addr, value, "constant"))
            continue
        if value.index < len(INPUT_NAMES) and INPUT_NAMES[value.index] in va:
            name = INPUT_NAMES[value.index]
            ours = ((va[name] >> value.shift) & value.and_) | value.or_
            rows.append((addr, ours, f"address of {name}"))
        elif addr in READ_SLOTS:
            rows.append((addr, None, "read from the card"))
        else:
            rows.append((addr, None, "unknown slot"))
    return rows


def compare():
    linux, ours = linux_list(), our_list()
    if len(linux) != len(ours) or [a for a, _ in linux] != [a for a, _, _ in ours]:
        raise ValueError("register order differs")
    table, problems = [], []
    for (addr, lvalue), (_, value, kind) in zip(linux, ours):
        same = value == lvalue
        if kind == "constant" and not same:
            problems.append(f"{addr:#x}: constant {value:#x}, Linux {lvalue:#x}")
        if kind == "unknown slot":
            problems.append(f"{addr:#x}: unknown slot")
        table.append((addr, lvalue, value, kind, same))
    return table, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    table, problems = compare()
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        sys.exit(1)
    constants = sum(1 for row in table if row[3] == "constant")
    if args.check:
        print(f"register list: {len(table)} entries, order equal to the Linux run, {constants} constants equal, "
              f"{len(table) - constants} run-data entries (6 record addresses, 2 card reads); HOST_ONLY")
        return
    print("index register   Linux       ours        kind")
    for index, (addr, lvalue, value, kind, same) in enumerate(table):
        ours = "(run time)" if value is None else f"{value:#010x}"
        print(f"{index:5d} {addr:#08x}  {lvalue:#010x}  {ours:10s}  {kind}{'' if same or value is None else '  (differs)'}")


if __name__ == "__main__":
    main()
