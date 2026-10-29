#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate the bounded read-only fault catalog and host evidence; --check is inert."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "src/memstage/Port.h",
    "src/memstage/Faults.h",
    "src/memstage/Faults.cpp",
    "tests/test_mem_faults.cpp",
    "tools/memstage/fault_report.py",
    "reference/nouveau/nvkm/subdev/top/gk104.c",
    "reference/nouveau/nvkm/subdev/privring/gk104.c",
    "reference/nouveau/nvkm/engine/fifo/gf100.c",
    "reference/nouveau/nvkm/engine/fifo/gk104.c",
    "reference/nouveau/nvkm/subdev/fb/gf100.c",
)
CATALOG = (
    (
        "0x000100",
        "fb/gf100.c:37",
        "reset and post-A7",
        "raw MC aggregate; all nonzero values stop",
    ),
    (
        "0x002100",
        "fifo/gk104.c:658",
        "post-A7",
        "raw FIFO aggregate; read without interrupt-enable mask; nonzero stops",
    ),
    (
        "0x00259c",
        "fifo/gf100.c:723-729",
        "post-A7",
        "pending MMU units; nonzero stops; W1C acknowledgement omitted",
    ),
    (
        "0x002800 + unit*16 + word*4",
        "fifo/gf100.c:699-702",
        "post-A7, pending unit only",
        "unit 0..31, word 0..3; raw instance/address/type; no writes",
    ),
    (
        "0x120058,0x12005c",
        "privring/gk104.c:62-63",
        "post-A7",
        "raw privring pending; nonzero stops; 0x12004c acknowledgement omitted",
    ),
    (
        "0x120070,0x120074,0x120078",
        "privring/gk104.c:64-66",
        "post-A7",
        "hub/ROP/GPC detail bounds; reject >8/16/32",
    ),
    (
        "0x122120/0x124120/0x128120 + i*0x800 + word*4",
        "privring/gk104.c:28-55",
        "post-A7, pending unit only",
        "three raw words per bounded pending unit; no clears",
    ),
    (
        "0x022700 + i*4",
        "top/gk104.c:37-75",
        "once after A7",
        "64 raw topology words; bounded descriptor grouping; no runlist-zero assumption",
    ),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = subprocess.check_output(
        [str(ROOT / "build/tests/test_mem_faults")], text=True, timeout=30
    ).strip()
    if (
        result
        != "memory faults: 25 bounded baseline/routing/clock cases pass; HOST_ONLY"
    ):
        raise ValueError("unexpected fault test result")
    value = dict(
        scope="KNOWN/SOURCE_ONLY read semantics; HOST_ONLY tests; no observed card values",
        reset_profile="MC only; raw read has no clear in reference; applicability before POST is INFERRED",
        catalog=[
            dict(
                expression=e,
                source=s,
                phase=p,
                rule=r,
                access="read-only; no read-to-clear behavior in reference",
            )
            for e, s, p, r in CATALOG
        ],
        coverage="MC/FIFO/MMU/privring and bounded TOP; not whole-chip fault coverage; no PBDMA count probe",
        storage=dict(events=4096, routing=64, diagnostic_budget_us=2000000),
        host_tests=result,
        source_sha256={
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sorted(FILES)
        },
    )
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path = ROOT / "work/S1MEMFAULTS/catalog.json"
    if args.check:
        if path.read_text() != text:
            raise ValueError("fault report differs")
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
