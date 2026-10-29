#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind physical-window test evidence to implementation and primary sources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "src/memstage/Port.h",
    "src/memstage/Faults.h",
    "src/memstage/Upload.h",
    "src/memstage/Upload.cpp",
    "src/memory/VramArena.h",
    "src/memory/VramArena.cpp",
    "tests/test_mem_upload.cpp",
    "tools/memstage/upload_report.py",
    "reference/nouveau/nvkm/subdev/instmem/nv50.c",
    "reference/nouveau/nvkm/subdev/bar/g84.c",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = subprocess.check_output(
        [str(ROOT / "build/tests/test_mem_upload")], text=True, timeout=60
    ).strip()
    if (
        result
        != "memory upload: 20 ordering/window/alias/failure cases pass; HOST_ONLY"
    ):
        raise ValueError("unexpected upload test result")
    value = dict(
        scope="SOURCE_ONLY protocol; HOST_ONLY independent physical-storage oracle",
        protocol=[
            "explicit UC profile and active private native gate",
            "owned token validation and window transaction lock",
            "selector 0x1700 and data 0x700000 + physical low 20 bits",
            "CPU store fence, BAR flush 0x70000=1, busy bit 2 clear, CPU load fence",
            "write both full pages, verify both; repeat complement then original",
        ],
        bounds=dict(bulk_us=5000000, flush_us=2000000, poll_count=100000),
        claim="scoped staged/readback only; no DMA payload publication, GPU-VA or channel proof",
        tests=result,
        source_sha256={
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sorted(FILES)
        },
    )
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path = ROOT / "work/S1MEMUPLOAD/host-check.json"
    if args.check:
        if path.read_text() != text:
            raise ValueError("upload report differs")
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
