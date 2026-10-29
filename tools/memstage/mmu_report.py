#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate the bounded BAR1/gk104 operation report; --check writes nothing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    "reference/nouveau/nvkm/subdev/mmu/gk104.c",
    "src/memstage/Port.h",
    "src/memstage/Mapper.h",
    "src/memstage/Mapper.cpp",
    "src/memstage/Tables.h",
    "src/memstage/Tables.cpp",
    "src/memstage/Upload.h",
    "src/memstage/Upload.cpp",
    "src/memstage/Faults.h",
    "src/memstage/Faults.cpp",
    "src/memory/VramArena.h",
    "src/memory/VramArena.cpp",
    "tests/test_mem_mmu.cpp",
    "tests/memstage_device.h",
    "tools/memstage/mmu_report.py",
    "reference/nouveau/nvkm/subdev/mmu/vmmgk104.c",
    "reference/nouveau/nvkm/subdev/mmu/vmmgf100.c",
    "reference/nouveau/nvkm/subdev/bar/gf100.c",
    "reference/nouveau/nvkm/subdev/bar/g84.c",
    "reference/nouveau/nvkm/subdev/fb/ramgk104.c",
    "reference/nouveau/nvkm/subdev/fb/gf100.c",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = subprocess.check_output(
        [str(ROOT / "build/tests/test_mem_mmu")], text=True, timeout=60
    ).strip()
    if (
        result
        != "memory MMU: 4096 independent encoding cases; 21 lifecycle/fault cases pass; HOST_ONLY"
    ):
        raise ValueError("unexpected MMU test result")
    value = dict(
        scope="SOURCE_ONLY gk104 17/12 BAR1 experiment; HOST_ONLY tests, native objects only",
        geometry=dict(
            virtual_bits=40,
            small_page_shift=12,
            small_index_bits=15,
            directory_index_bits=13,
            entry_bytes=8,
        ),
        table_profile="VRAM, read-only data PTEs, kind 0, no VOL/compression/large table",
        effects=[
            dict(
                register="0x100c80",
                value="old & ~1, verify bit 0 clear",
                source="fb/gf100.c:66-77",
            ),
            dict(
                register="0x100cb8",
                value="owned PGD physical >> 8, uint32 fit, VRAM target 0",
                source="mmu/vmmgf100.c:180-218",
            ),
            dict(
                register="0x100cbc",
                value="0x80000005 PAGE_ALL | HUB_ONLY; never ALL_PDB",
                source="mmu/vmmgf100.c:221-233",
            ),
            dict(
                register="0x001704",
                value="0x80000000 | owned instance physical >> 12; clear bit 31 only after all witnesses pass",
                source="bar/gf100.c:46-58",
            ),
            dict(
                register="0x070000",
                value="1, busy mask 2 clear; twice after enable",
                source="bar/g84.c:29-39; bar/gf100.c:38-44",
            ),
        ],
        witness=[
            "VA0=A,VA1=B",
            "SPTE0=B; staged readback; this-PDB invalidation; VA0=B,VA1=B",
            "SPTE0=A; same protocol; VA0=A,VA1=B",
            "disable owned BAR1; raw final faults; retain all",
        ],
        guest_mapping="explicit UC read-only 8192-byte BAR1 prefix; discovered full aperture bounds VMM",
        exclusions=[
            "BAR2/0x1714",
            "host DMA payload proof",
            "channel translation/PBDMA fetch",
            "Q11 echo test",
            "unknown-pointer rollback",
        ],
        tests=result,
        source_sha256={
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sorted(FILES)
        },
    )
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path = ROOT / "work/S1MEMMMU/host-check.json"
    if args.check:
        if path.read_text() != text:
            raise ValueError("MMU report differs")
    else:
        path.write_text(text)


if __name__ == "__main__":
    main()
