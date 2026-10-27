#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate source-bound host owner/POST evidence. No firmware bytes are written.

The compiled probe tests resident image/latch/quarantine lifetime. This does not
establish native execution, DMA, physical pin behavior or stage permission.
--check compares exact generated text without writing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from devinit_preflight import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'work/S1OWNERPOST/host-check.json'
PROBE = ROOT / 'build/tests/owner_post_probe'
SOURCES = (
    'src/os/NativeOwner.h', 'src/os/NativeOwner.cpp', 'src/os/OwnerPostSimulation.cpp',
    'src/os/HaikuOwnerModule.h', 'src/os/HaikuOwnerModule.cpp',
    'src/os/OwnerClient.h', 'src/os/OwnerClient.cpp',
    'src/os/HaikuMemory.h', 'src/os/HaikuMemory.cpp', 'src/runtime/BootState.h',
    'src/devinit/BoundPost.h', 'src/devinit/BoundPost.cpp',
    'src/devinit/PostImage.h', 'src/devinit/PostImage.cpp',
    'src/devinit/BoardCore.h', 'src/devinit/BoardCore.cpp',
    'src/devinit/BoardPolicy.h', 'src/devinit/BoardPolicy.cpp',
    'src/devinit/Interpreter.h', 'src/devinit/Interpreter.cpp',
    'src/devinit/I2c.h', 'src/devinit/I2c.cpp', 'src/devinit/Sha256.h', 'src/devinit/Sha256.cpp',
    'tests/owner_post_probe.cpp', 'tests/i2c_wire.h', 'tests/board_fake.h',
    'tests/test_native_owner.cpp', 'tests/native_owner_post_gate.cpp', 'tests/Makefile', 'tools/owner_post_check.py',
)


def report(rom):
    if hashlib.sha256(rom.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError('ROM identity differs')
    output = subprocess.check_output([str(PROBE), str(rom)], text=True, timeout=60).strip()
    match = re.fullmatch(r'owner_post host_cases (\d+) assertions (\d+) failures 0 native_execution 0 hardware_execution 0', output)
    if not match or int(match[1]) < 9 or int(match[2]) < 100:
        raise ValueError('owner POST probe did not complete all expected cases')
    return dict(scope='HOST_ONLY persistent owner binding/latch simulation',
                rom_sha256=EXPECTED, cases=int(match[1]), assertions=int(match[2]),
                failures=0, native_execution=False, hardware_execution=False,
                production_eligible=False, compiled_exercise=output,
                source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(SOURCES)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path(os.environ.get('K40_VBIOS', str(
        Path.home()/'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser())
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(report(args.rom), indent=2, sort_keys=True)+'\n'
    if args.check:
        return 0 if OUTPUT.is_file() and OUTPUT.read_text() == text else 1
    OUTPUT.write_text(text)
    print('Owner POST host lifetime checks pass; no native/hardware execution')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
