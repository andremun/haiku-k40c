#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Read the GR register tables of the pinned Nouveau tree.

Nouveau keeps the GR set-up data as arrays of {address, count, pitch, data}
(struct gf100_gr_init) grouped in packs (struct gf100_gr_pack). This module
parses them from reference/nouveau/nvkm/engine/gr/*.c. It reads register
facts only: no function body is used. Every row keeps its file and line.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
GR = ROOT / "reference/nouveau/nvkm/engine/gr"
ARRAY = re.compile(
    r"^(?:static\s+)?const\s+struct\s+(gf100_gr_init|gf100_gr_pack)\s*\n(\w+)\[\]\s*=\s*\{\n(.*?)^\};",
    re.M | re.S,
)
ROW = re.compile(r"\{\s*(0x[0-9a-fA-F]+)\s*,\s*(\d+)\s*,\s*(0x[0-9a-fA-F]+)\s*,\s*(0x[0-9a-fA-F]+)\s*\}")
ENTRY = re.compile(r"\{\s*(\w+)\s*(?:,\s*(?:\.type\s*=\s*)?(0x[0-9a-fA-F]+|\d+)\s*)?\}")


def parse():
    """Return (inits, packs).

    inits: name -> list of dict(addr, count, pitch, data, source).
    packs: name -> list of dict(init, type, source); type is the optional
    second member of a pack entry (the object class of a method list).
    """
    inits, packs = {}, {}
    for path in sorted(GR.glob("*.c")):
        text = path.read_text()
        for match in ARRAY.finditer(text):
            kind, name, body = match.groups()
            first = text.count("\n", 0, match.start(3)) + 1
            rows = []
            for offset, line in enumerate(body.split("\n")):
                source = f"nvkm/engine/gr/{path.name}:{first + offset}"
                if kind == "gf100_gr_init":
                    found = ROW.search(line)
                    if found:
                        addr, count, pitch, data = (int(x, 0) for x in found.groups())
                        rows.append(dict(addr=addr, count=count, pitch=pitch, data=data, source=source))
                    elif line.strip() not in ("", "{}"):
                        raise ValueError(f"{source}: unreadable table row: {line.strip()}")
                else:
                    found = ENTRY.search(line)
                    if found:
                        rows.append(dict(init=found.group(1), type=int(found.group(2) or "0", 0), source=source))
                    elif line.strip() not in ("", "{}"):
                        raise ValueError(f"{source}: unreadable pack entry: {line.strip()}")
            target = inits if kind == "gf100_gr_init" else packs
            if name in target:
                raise ValueError(f"table {name} is defined twice")
            target[name] = rows
    return inits, packs


def expand(pack, inits, packs):
    """The ordered (address, data, source) writes of gf100_gr_mmio (gf100.c:1078-1092)."""
    writes = []
    for entry in packs[pack]:
        for row in inits[entry["init"]]:
            for index in range(row["count"]):
                writes.append((row["addr"] + index * row["pitch"], row["data"], row["source"]))
    return writes


if __name__ == "__main__":
    inits, packs = parse()
    print(len(inits), "init tables,", len(packs), "packs,",
          len(expand("gk110b_gr_pack_mmio", inits, packs)), "writes in gk110b_gr_pack_mmio")
