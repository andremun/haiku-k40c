#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate conservative POST input coverage, without executing the ROM.

Reads the exact external image and pinned source. --check compares exact text
without writes. This report is not a permission or hardware-readiness token.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

from devinit_preflight import EXPECTED, preflight
from board_trace import read_policy, ADR

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'tools/devinit_closure.py', 'tools/devinit_preflight.py',
    'src/devinit/Interpreter.cpp', 'src/devinit/Interpreter.h',
    'src/devinit/Board.cpp', 'src/devinit/Board.h',
    'src/devinit/I2c.cpp', 'src/devinit/I2c.h',
    'reference/nouveau/nvkm/subdev/bios/init.c',
    'reference/nouveau/nvkm/subdev/bios/ramcfg.c',
    'reference/nouveau/nvkm/subdev/bios/M0203.c',
    'reference/nouveau/nvkm/subdev/bios/dcb.c',
    'reference/nouveau/nvkm/subdev/bios/gpio.c',
    'reference/nouveau/nvkm/subdev/bios/i2c.c',
    'reference/nouveau/nvkm/subdev/i2c/bit.c',
    'reference/nouveau/nvkm/subdev/i2c/busgf119.c',
    'docs/decisions/004-board-operations-and-review.md',
)


class Reader:
    """Read bounded little-endian fields and record referenced input spans."""
    def __init__(self, rom):
        self.rom = rom
        self.spans = []

    def get(self, at, size, role='input'):
        if at < 0 or size < 0 or at > len(self.rom) or size > len(self.rom) - at:
            raise ValueError(f'{role}: out of bounds at {at:#x} length {size}')
        self.spans.append((at, at + size, role))
        return int.from_bytes(self.rom[at:at + size], 'little')


def bit_inputs(reader):
    """Parse reviewed BIT entries. Reject ambiguous signatures/identifiers."""
    rom = reader.rom
    at = rom.find(b'\xff\xb8BIT')
    if at < 0 or rom.find(b'\xff\xb8BIT', at + 1) >= 0:
        raise ValueError('missing or ambiguous BIT signature')
    stride = reader.get(at + 9, 1)
    count = reader.get(at + 10, 1)
    if stride < 6:
        raise ValueError('BIT stride below reviewed entry width')
    entries = {}
    for index in range(count):
        entry = at + 12 + index * stride
        key = chr(reader.get(entry, 1))
        if key in entries:
            raise ValueError('duplicate BIT identifier')
        version = reader.get(entry + 1, 1)
        size = reader.get(entry + 2, 2)
        pointer = reader.get(entry + 4, 2)
        reader.get(pointer, size, 'BIT entry')
        entries[key] = (version, size, pointer)
    if not {'I', 'M'} <= entries.keys():
        raise ValueError('missing BIT I/M')
    iv, il, ip = entries['I']
    mv, ml, mp = entries['M']
    valid_memory = (mv == 1 and ml >= 5) or (mv == 2 and ml >= 3)
    if iv != 1 or il < 14 or not valid_memory:
        raise ValueError('unreviewed BIT I/M layout')
    return entries, (iv, il, ip), (mv, ml, mp)


def ram_groups(reader, memory):
    """Resolve every strap without reading hardware; preserve first-match lookup.

    bios/ramcfg.c:29-90; bios/M0203.c:29-143. A selected invalid group is
    denied, not silently reduced modulo the group count.
    """
    version, length, pointer = memory
    count = reader.get(pointer + (2 if version == 1 else 0), 1, 'RAM group count')
    xlat = reader.get(pointer + (3 if version == 1 else 1), 2, 'RAM translation')
    table = reader.get(pointer + 3, 2, 'M0203 pointer') if version == 2 and length >= 7 else 0
    matches = {}
    mode = 'identity' if not xlat else 'translation'
    if table:
        table_version = reader.get(table, 1, 'M0203 version')
        if table_version == 0x10:
            header = reader.get(table + 1, 1)
            stride = reader.get(table + 2, 1)
            entries = reader.get(table + 3, 1)
            if header < 7 or stride < 2:
                raise ValueError('short M0203 header/entry')
            reader.get(table, header + entries * stride, 'M0203 table')
            kind = reader.get(table + 4, 1)
            if kind != 0:
                raise ValueError('unreviewed M0203 table type')
            for index in range(entries):
                at = table + header + index * stride
                strap = reader.get(at, 1) >> 4
                group = reader.get(at + 1, 1) & 15
                matches.setdefault(strap, group)
            mode = 'M0203 first match, then translation/identity fallback'
        # Unknown M0203 versions fall back in the pinned source.
    mapping = []
    for strap in range(16):
        group = matches.get(strap)
        if group is None:
            group = reader.get(xlat + strap, 1, 'RAM translation entry') if xlat else strap
        mapping.append(dict(strap=strap, group=group, valid=bool(count and group < count)))
    return dict(count=count, mode=mode, candidates=mapping,
                live_selection='UNKNOWN: cache one 0x101000 strap read and validate selected group before writes')


def instruction_length(reader, pc, op, groups):
    """Reviewed lengths from bios/init.c handlers; not decoder presentation rows."""
    fixed = {0x33: 2, 0x36: 1, 0x38: 1, 0x53: 3, 0x56: 3, 0x5b: 3,
             0x5c: 3, 0x5f: 22, 0x69: 5, 0x6b: 2, 0x6e: 13, 0x6f: 2,
             0x71: 1, 0x72: 1, 0x74: 3, 0x75: 2, 0x7a: 9, 0x8c: 1,
             0x8d: 1, 0x8e: 1, 0x90: 9, 0x97: 13}
    if op == 0x4d:
        return 4 + 2 * reader.get(pc + 3, 1)
    if op in (0x58, 0x91):
        return 6 + 4 * reader.get(pc + 5, 1)
    if op == 0x8f:
        if not groups:
            raise ValueError('RAM group count unavailable')
        return 7 + 4 * reader.get(pc + 6, 1) * groups
    if op == 0xa9:
        return 2 + reader.get(pc + 1, 1)
    if op not in fixed:
        raise ValueError(f'unreviewed instruction length {op:#x}')
    return fixed[op]


def helper_inputs(reader, visited):
    """Validate board-table inputs without issuing helper effects.

    bios/dcb.c:35-60, bios/gpio.c:103-110, bios/i2c.c:32-143;
    gpio/gf119.c:27-64, i2c/base.c:53-64. Unsupported transport layouts deny.
    """
    need_i2c = any(op == 0x4d for op in visited.values())
    need_gpio = any(op == 0xa9 for op in visited.values())
    if not need_i2c and not need_gpio:
        return {}, []
    dcb = reader.get(0x36, 2, 'DCB pointer')
    if not dcb or reader.get(dcb + 1, 1) < 12:
        raise ValueError('missing/short DCB')
    version = reader.get(dcb, 1)
    if not 0x30 <= version <= 0x41 or reader.get(dcb + 6, 4) != 0x4edcbdcb:
        raise ValueError('unreviewed DCB version/signature')
    result, issues = {'dcb_version': hex(version)}, []
    if need_gpio:
        table = reader.get(dcb + 10, 2)
        if not table:
            raise ValueError('missing GPIO table')
        version = reader.get(table, 1)
        header = reader.get(table + 1, 1)
        count = reader.get(table + 2, 1)
        stride = reader.get(table + 3, 1)
        if version != 0x41 or header < 4 or stride < 5:
            raise ValueError('unreviewed GPIO layout')
        reader.get(table, header + count * stride, 'GPIO table')
        for index in range(count):
            at = table + header + index * stride
            raw = reader.get(at, 4)
            if (raw >> 8) & 255 != 255 and raw & 63 >= 32:
                raise ValueError('GPIO line outside selected GK104 range')
        result['gpio'] = dict(version=hex(version), entries=count,
                              semantics='defaults, exclusions, first-match logic, drive/latch/routing')
    if need_i2c:
        table = reader.get(dcb + 4, 2)
        if not table:
            raise ValueError('missing CCB table')
        version = reader.get(table, 1)
        header = reader.get(table + 1, 1)
        count = reader.get(table + 2, 1)
        stride = reader.get(table + 3, 1)
        if version != 0x40 or header < 5 or stride < 4:
            raise ValueError('dedicated host transport requires reviewed CCB 4.0')
        reader.get(table, header + count * stride, 'CCB table')
        defaults = reader.get(table + 4, 1)
        resolved = []
        for pc, op in sorted(visited.items()):
            if op != 0x4d:
                continue
            index = reader.get(pc + 1, 1)
            if index in (0x80, 0xff):
                index = defaults & 15
            elif index == 0x81:
                index = defaults >> 4
            if index >= count:
                raise ValueError('CCB bus index out of bounds')
            raw = reader.get(table + header + index * stride, 4)
            kind, drive = raw >> 24, raw & 15
            share = ((raw >> 9) & 127) if raw & 0x100 else 255
            if kind != 5 or share != 255:
                issues.append(dict(offset=hex(pc), kind='dedicated_i2c_transport_unavailable'))
            resolved.append(dict(offset=hex(pc), index=index, type=kind, drive=drive, share=share))
        result['i2c'] = dict(version=hex(version), resolved=resolved,
                             transport='SOURCE_ONLY internal-bit candidate, host backend only')
    return result, issues


def closure(rom, policy):
    """Audit all structurally reachable inputs; never infer feasible conditions."""
    reader = Reader(rom)
    entries, init, memory = bit_inputs(reader)
    _, init_length, init_pointer = init
    ram = ram_groups(reader, memory)
    pointers = {name: reader.get(init_pointer + offset, 2, 'BIT I ' + name)
                for name, offset in [('scripts', 0), ('macro_index', 2), ('macros', 4),
                                     ('conditions', 6), ('io_conditions', 8),
                                     ('io_flag_conditions', 10), ('functions', 12)]}
    pointers['extra'] = reader.get(init_pointer + 14, 2) if init_length >= 16 else 0
    pointers['xlat'] = reader.get(init_pointer + 16, 2) if init_length >= 18 else 0
    structural, visited = preflight(rom)
    if not structural['structural_coverage_complete']:
        raise ValueError('structural preflight incomplete')
    source = (ROOT / 'src/devinit/Interpreter.cpp').read_text()
    supported = {int(op, 16) for op in re.findall(r'case (0x[0-9a-f]+):', source)}
    digest = hashlib.sha256(rom).hexdigest()
    permissions = {(offset, opcode) for identity, offset, opcode in policy if identity == digest}
    reader.get(pointers['scripts'], 2 * (len(structural['main_scripts']) + 1), 'script pointer table')
    helpers, helper_issues = helper_inputs(reader, visited)
    issues, references, board, instruction_spans, shifts = helper_issues, [], [], [], []
    conditions, macros = set(), set()

    def register(at, role, owner):
        encoded = reader.get(at, 4, role)
        # init.c:144-178: low-bit normalization and display-context encoding.
        contextual = bool(encoded & 0xe0000000)
        unknown = bool(encoded & ~0xe0ffffff)
        references.append(dict(offset=hex(owner), role=role, register=hex(encoded & ~3),
                               normalize_low_bits=bool(encoded & 3), context_required=contextual,
                               unknown_bits=unknown))
        if contextual or unknown:
            issues.append(dict(offset=hex(owner), kind='register_context_or_bits_unresolved', role=role))

    for pc, op in sorted(visited.items()):
        length = instruction_length(reader, pc, op, ram['count'])
        reader.get(pc, length, 'instruction')
        instruction_spans.append((pc, pc + length))
        if op not in supported:
            issues.append(dict(offset=hex(pc), kind='core_opcode_unsupported', opcode=hex(op)))
        if op in (0x56, 0x75):
            conditions.add(reader.get(pc + 1, 1))
        if op == 0x6f:
            macros.add(reader.get(pc + 1, 1))
        if op in (0x6e, 0x7a, 0x97, 0x58, 0x91, 0x8f, 0x90, 0x5f):
            register(pc + 1, 'operand', pc)
        if op == 0x90:
            register(pc + 5, 'destination', pc)
        if op == 0x5f:
            register(pc + 14, 'destination', pc)
            shift = reader.get(pc + 5, 1)
            if (shift if shift < 128 else 256 - shift) >= 32:
                shifts.append(hex(pc))
        if op in (0x58, 0x8f):
            base = reader.get(pc + 1, 4)
            stride = 4 if op == 0x58 else reader.get(pc + 5, 1)
            count = reader.get(pc + (5 if op == 0x58 else 6), 1)
            for index in range(count):
                address = base + index * stride
                if address > 0xffffffff or address & ~0x00fffffc:
                    issues.append(dict(offset=hex(pc), kind='generated_register_unreviewed'))
                    break
        if op in (0x4d, 0x53, 0x69, 0x8e, 0xa9):
            allowed = (pc, op) in permissions
            board.append(dict(offset=hex(pc), opcode=hex(op), allowed=allowed,
                              runtime='helper when active; IO waits even when skipped' if allowed
                              else 'DENY if active; condition feasibility not proved'))
    for index in sorted(conditions):
        if pointers['conditions']:
            at = pointers['conditions'] + 12 * index
            reader.get(at, 12, 'condition entry')
            register(at, 'condition', at)
    for index in sorted(macros):
        if pointers['macros']:
            at = pointers['macros'] + 8 * index
            reader.get(at, 8, 'macro entry')
            register(at, 'macro', at)
    for left, right in zip(instruction_spans, instruction_spans[1:]):
        if left[1] > right[0]:
            issues.append(dict(offset=hex(right[0]), kind='overlapping_instructions'))
    # Tables used by execution cannot alias instruction payloads in this reviewed subset.
    for start, end, role in sorted(set(reader.spans)):
        if role in ('condition entry', 'macro entry', 'M0203 table', 'RAM translation entry', 'GPIO table', 'CCB table', 'script pointer table'):
            if any(start < b and a < end for a, b in instruction_spans):
                issues.append(dict(offset=hex(start), kind='table_instruction_overlap', role=role))
    input_spans = sorted({(a, b, role) for a, b, role in reader.spans
                          if role in ('condition entry', 'macro entry', 'M0203 table', 'RAM translation entry', 'GPIO table', 'CCB table', 'script pointer table')})
    for i, (a, b, role) in enumerate(input_spans):
        for c, d, other in input_spans[i + 1:]:
            if c >= b:
                break
            if role != other and a < d:
                issues.append(dict(offset=hex(c), kind='input_table_overlap', role=other))
    issues += [dict(offset=pc, kind='invalid_shift') for pc in shifts]
    return dict(
        scope='conservative POST inputs; not feasible paths, display scripts, permission or readiness',
        evidence='KNOWN from ROM/source; SOURCE_ONLY semantics',
        bit_entries={k: dict(version=v, length=n, offset=hex(p))
                     for k, (v, n, p) in sorted(entries.items()) if k in ('I', 'M')},
        input_pointers={k: hex(v) for k, v in sorted(pointers.items())},
        post_roots=structural['main_scripts'] + ([structural['extra_script']]
                   if int(structural['extra_script'], 16) else []),
        potential_instruction_count=len(visited),
        opcode_counts=dict(sorted(Counter(f'0x{op:02x}' for op in visited.values()).items())),
        ram=ram, condition_indices=sorted(conditions), macro_indices=sorted(macros),
        missing_table_behavior=dict(conditions='false', macros='no-op'),
        register_summary=dict(references=len(references),
                              distinct_registers=len({r['register'] for r in references}),
                              low_bit_normalizations=sum(r['normalize_low_bits'] for r in references),
                              contextual=sum(r['context_required'] for r in references),
                              unknown_bits=sum(r['unknown_bits'] for r in references),
                              roles=dict(sorted(Counter(r['role'] for r in references).items()))),
        board_operations=board, helper_inputs=helpers,
        issues=sorted(issues, key=lambda row: (int(row['offset'], 16), row['kind'], row.get('role', ''))),
        input_bounds_valid=not issues,
        post_entry_semantics='fresh execute flags per main root, then extra root (init.c:2331-2344)',
        control_flow_limitations='conservative starts, not condition feasibility, call-depth or termination proof; runtime budgets remain mandatory',
        production_eligible=False,
        remaining_gates=[
            'Denied board operation must stop if a changed condition enables it',
            'Native immutable ROM/table binding and cached live RAM selection',
            'Physical register normalization/stage policy and bounded transports',
            'I2C internal algorithm choice not verified against capture configuration',
            'Native boot-persistent owner, DMA/visibility, VRAM ownership and readiness',
            'Display/encoder scripts outside POST roots are excluded, not proved unnecessary',
        ],
    )


def render(rom):
    """Bind aggregate evidence to the exact approved ROM, policy and source files."""
    if hashlib.sha256(rom).hexdigest() != EXPECTED:
        raise ValueError('ROM identity mismatch')
    report = closure(rom, read_policy(ADR.read_text()))
    report['rom_sha256'] = EXPECTED
    report['source_sha256'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(SOURCES)}
    return json.dumps(report, indent=2, sort_keys=True) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path(os.environ.get('K40_VBIOS', str(
        Path.home() / 'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser())
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render(args.rom.read_bytes())
    path = ROOT / 'analysis/devinit_closure.json'
    if args.check:
        return 0 if path.is_file() and path.read_text() == text else 1
    path.write_text(text)
    report = json.loads(text)
    print(f"POST input closure: {report['potential_instruction_count']} starts; "
          f"{len(report['issues'])} unresolved input issues; production eligible: false")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
