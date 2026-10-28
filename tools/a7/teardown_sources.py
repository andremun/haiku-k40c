#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Capture read-only upstream VFIO teardown sources, outside reference/.

This v6.8 baseline is NOT exact Ubuntu -138 source. --check compares current
the entire generated record and source hashes without writing. No devices.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path("/tmp/k40-a7-teardown")
OUTPUT = ROOT / "work/S1A7NATIVE/teardown-sources.json"
FILES = (
    "drivers/vfio/pci/vfio_pci_core.c",
    "drivers/vfio/vfio_main.c",
    "drivers/vfio/vfio_iommu_type1.c",
)
BASE = "https://raw.githubusercontent.com/torvalds/linux/v6.8/"


def render():
    record = dict(
        scope="upstream Linux v6.8 SOURCE_ONLY; not exact running Ubuntu source",
        urls={name: BASE + name for name in FILES},
        sha256={
            name: hashlib.sha256((CACHE / name).read_bytes()).hexdigest()
            for name in FILES
        },
    )
    return json.dumps(record, sort_keys=True, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return 0 if OUTPUT.is_file() and OUTPUT.read_text() == render() else 1
    for name in FILES:
        path = CACHE / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with urllib.request.urlopen(BASE + name, timeout=30) as response:
                path.write_bytes(response.read())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
