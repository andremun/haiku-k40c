#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Pin read-only Haiku installation/discovery sources outside reference/.

Generate a deterministic source record for the fixed project reference revision.
--check compares the complete record without writes or network access. No device.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build/a7/install-sources"
OUTPUT = ROOT / "work/S1A7INSTALL/source-pins.json"
REVISION = "49a0af9585d80e42240af63ab66e31e9873f59b8"
FILES = (
    "src/system/kernel/device_manager/devfs.cpp",
    "src/system/kernel/device_manager/legacy_drivers.cpp",
    "src/system/kernel/fs/vfs.cpp",
)
BASE = "https://raw.githubusercontent.com/haiku/haiku/" + REVISION + "/"


def render():
    return (
        json.dumps(
            dict(
                revision=REVISION,
                scope="KNOWN / SOURCE_ONLY project Haiku reference revision; exact running-kernel source identity not established",
                sources={
                    name: dict(
                        url=BASE + name,
                        sha256=hashlib.sha256((CACHE / name).read_bytes()).hexdigest(),
                    )
                    for name in sorted(FILES)
                },
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


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
                data = response.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise ValueError("source capture bound")
            with path.open("xb") as out:
                out.write(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
