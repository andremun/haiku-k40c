#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind the VRAM ledger's host oracle to its sources; --check writes nothing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "src/memory/VramArena.h",
    "src/memory/VramArena.cpp",
    "tests/test_vram_arena.cpp",
    "tools/memstage/arena_report.py",
    "reference/nouveau/nvkm/subdev/fb/ramgf108.c",
    "reference/nouveau/nvkm/subdev/fb/ramgf100.c",
    "reference/nouveau/nvkm/subdev/fb/gf100.c",
    "reference/nouveau/nvkm/subdev/mmu/vmmgk104.c",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = subprocess.check_output(
        [str(ROOT / "build/tests/test_vram_arena")], text=True, timeout=30
    ).strip()
    if (
        output
        != "VRAM arena: 48 layout/oracle cases; stale/partial/capacity/retention checks pass; HOST_ONLY"
    ):
        raise ValueError("unexpected oracle result")
    report = dict(
        scope="HOST_ONLY; native object compilation is not hardware evidence",
        checks=output,
        source_sha256={
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sorted(FILES)
        },
        release="no release API; failed or referenced records retained",
        profile="uniform FBP only; head/tail/A7 scratch excluded; no DMA visibility claim",
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    path = ROOT / "work/S1MEMARENA/host-check.json"
    if args.check:
        if path.read_text() != text:
            raise ValueError("arena report differs")
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
