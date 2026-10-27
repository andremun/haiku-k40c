#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Compare the compiled exact-ROM access policy with independent input decoding.

Generates aggregate evidence only, never firmware payloads. --check writes
nothing and compares exact text. This cannot approve hardware execution.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess

from devinit_preflight import preflight, EXPECTED
from board_trace import read_policy, ADR

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'build/tests/post_probe'
SOURCES = ('src/devinit/PostImage.h', 'src/devinit/PostImage.cpp',
           'src/devinit/BoundPost.h', 'src/devinit/BoundPost.cpp',
           'src/devinit/BoardPolicy.h', 'src/devinit/BoardPolicy.cpp',
           'src/devinit/Board.cpp', 'src/devinit/Board.h',
           'src/devinit/Interpreter.cpp', 'src/devinit/Interpreter.h',
           'src/devinit/Sha256.cpp', 'src/devinit/Sha256.h',
           'tests/post_probe.cpp', 'tests/board_fake.h', 'tools/post_policy.py',
           'docs/decisions/004-board-operations-and-review.md')


def permissions(rom, approved):
    """Decode access directions independently from the C++ permission methods.

    init.c:479-491,1037-1050,1281-1300,1636-1655,1734-1748,
    1855-1946,1982-2052,2154-2182; gpio/gf119.c:27-64.
    """
    structure, code = preflight(rom)
    if structure['issues']:
        raise ValueError('incomplete structural inputs')
    def u(at, size=4):
        if at < 0 or at > len(rom) or size > len(rom) - at:
            raise ValueError('policy input outside ROM')
        return int.from_bytes(rom[at:at+size], 'little')
    result = set()
    def access(pc, reg, read=False, write=False, width=4):
        if read:
            result.add((pc, reg, width, 0))
        if write:
            result.add((pc, reg, width, 1))
    for pc, op in sorted(code.items()):
        if op in (0x6e, 0x97):
            access(pc, u(pc+1), True, True)
        elif op == 0x7a:
            access(pc, u(pc+1), write=True)
        elif op == 0x90:
            access(pc, u(pc+1), read=True)
            access(pc, u(pc+5), write=True)
        elif op == 0x5f:
            access(pc, u(pc+1), read=True)
            access(pc, u(pc+14), True, True)
        elif op in (0x58, 0x8f):
            stride, count = (4, u(pc+5, 1)) if op == 0x58 else (u(pc+5, 1), u(pc+6, 1))
            for index in range(count):
                access(pc, u(pc+1)+stride*index, write=True)
        elif op == 0x91 and u(pc+5, 1):
            access(pc, u(pc+1), write=True)
        elif op == 0x6f and int(structure['macro_table'], 16):
            access(pc, u(int(structure['macro_table'], 16)+8*u(pc+1, 1)), write=True)
        elif op in (0x56, 0x75) and int(structure['condition_table'], 16):
            access(pc, u(int(structure['condition_table'], 16)+12*u(pc+1, 1)), read=True)
        if (pc, op) not in approved:
            continue
        if op == 0x53:
            for reg in (0x6013d4, 0x6013d5):  # engine/disp/vga.c:104-108.
                access(pc, reg, write=True, width=1)
        elif op == 0x69:
            access(pc, 0x601000+u(pc+1, 2), True, True, width=1)  # disp/vga.c:49-52.
            for reg in (0x614100, 0x614900, 0x000200, 0x00e18c):  # bios/init.c:1640-1655.
                access(pc, reg, True, True)
        elif op == 0x4d:
            ccb = u(u(0x36, 2)+4, 2)  # bios/dcb.c:35; bios/i2c.c:32-62.
            index = u(pc+1, 1)
            if index == 0x80:
                index = u(ccb+4, 1) & 15
            elif index == 0x81:
                index = u(ccb+4, 1) >> 4
            raw = u(ccb+u(ccb+1, 1)+index*u(ccb+3, 1))
            access(pc, 0x00d014+(raw & 15)*0x20, True, True)  # i2c/busgf119.c:93.
        elif op == 0xa9:
            gpio = u(u(0x36, 2)+10, 2)
            excluded = {u(pc+2+i, 1) for i in range(u(pc+1, 1))}
            for index in range(u(gpio+2, 1)):
                raw = u(gpio+u(gpio+1, 1)+index*u(gpio+3, 1))
                function, line, selector = (raw >> 8) & 255, raw & 63, (raw >> 24) & 31
                if function == 255 or function in excluded:
                    continue
                access(pc, 0x00d610+line*4, True, True)  # gpio/gf119.c:49,60.
                access(pc, 0x00d604, True, True)  # gpio/gf119.c:61.
                if selector:
                    access(pc, 0x00d740+(selector-1)*4, True, True)  # gpio/gf119.c:51.
    return result, code


def report(path):
    """Bind exhaustive candidate checks and artificial runs to source hashes."""
    rom = path.read_bytes()
    if hashlib.sha256(rom).hexdigest() != EXPECTED:
        raise ValueError('wrong ROM identity')
    policy = read_policy(ADR.read_text())
    expected, code = permissions(rom, {(pc, op) for identity, pc, op in policy if identity == EXPECTED})
    queries = set(expected)
    for pc, reg, _, _ in sorted(expected):
        for offset in (-4, 0, 4, 256):
            if reg+offset < 0:
                continue
            for width in (1, 2, 4, 8):
                for write in (0, 1):
                    queries.add((pc, reg+offset, width, write))
                    queries.add((pc+1, reg+offset, width, write))
    queries = sorted(queries)
    text = ''.join(f'{pc:x} {reg:x} {width:x} {write:x}\n' for pc, reg, width, write in queries)
    output = subprocess.check_output([str(PROBE), str(path), '--policy'], input=text, text=True, timeout=60)
    observed = output.splitlines()
    if len(observed) != len(queries) or any(row not in ('0', '1') for row in observed):
        raise ValueError('compiled policy returned incomplete results')
    for query, row in zip(queries, observed):
        if (row == '1') != (query in expected):
            raise ValueError(f'compiled access policy differs for {query}')
    exercise = subprocess.check_output([str(PROBE), str(path), '--exercise'], text=True, timeout=60).strip()
    return dict(scope='HOST_ONLY binding and per-instruction policy; not a hardware permission',
                rom_sha256=EXPECTED, potential_starts=len(code), policy_queries=len(queries),
                allowed_accesses=len(expected), directions=dict(sorted(Counter('write' if q[3] else 'read' for q in expected).items())),
                widths=dict(sorted(Counter(str(q[2]) for q in expected).items())),
                compiled_comparison='pass', artificial_exercise=exercise,
                production_eligible=False,
                source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(SOURCES)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path(os.environ.get('K40_VBIOS',str(
        Path.home()/'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser())
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(report(args.rom), indent=2, sort_keys=True)+'\n'
    output = ROOT/'work/S1POST/policy-check.json'
    if args.check:
        return 0 if output.is_file() and output.read_text() == text else 1
    output.write_text(text)
    print('Bound POST policy: compiled comparison passes (HOST_ONLY)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
