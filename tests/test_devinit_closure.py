#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic input mutations for the host POST closure audit."""
import sys
import hashlib
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import devinit_closure as tool
from devinit_closure import closure, Reader, ram_groups, render


def image():
    rom = bytearray(2048)
    rom[32:37] = b'\xff\xb8BIT'
    rom[41:43] = bytes([6, 2])
    rom[44:50] = bytes([ord('I'), 1, 18, 0, 80, 0])
    rom[50:56] = bytes([ord('M'), 2, 3, 0, 112, 0])
    rom[80:82] = (144).to_bytes(2, 'little')
    rom[84:86] = (600).to_bytes(2, 'little')
    rom[86:88] = (640).to_bytes(2, 'little')
    rom[112] = 2
    rom[144:146] = (256).to_bytes(2, 'little')
    # Main root calls a conditional subroutine, then a separate extra root.
    rom[94:96] = (300).to_bytes(2, 'little')
    rom[256:264] = bytes([0x75, 1, 0x5b, 0x10, 1, 0x6f, 2, 0x71])
    rom[272:274] = bytes([0x8c, 0x71])
    rom[300:302] = bytes([0x8d, 0x71])
    rom[652:656] = (0x200).to_bytes(4, 'little')
    rom[616:620] = (0x1000).to_bytes(4, 'little')
    return rom


class ClosureTests(unittest.TestCase):
    def test_roots_tables_and_no_permission_token(self):
        result = closure(image(), [])
        self.assertEqual(result['post_roots'], ['0x100', '0x12c'])
        self.assertEqual(result['potential_instruction_count'], 8)
        self.assertEqual(result['condition_indices'], [1])
        self.assertEqual(result['macro_indices'], [2])
        self.assertEqual(result['register_summary']['references'], 2)
        self.assertTrue(result['input_bounds_valid'])
        self.assertFalse(result['production_eligible'])

    def test_missing_condition_macro_tables(self):
        rom = image()
        rom[84:88] = bytes(4)
        result = closure(rom, [])
        self.assertEqual(result['register_summary']['references'], 0)
        self.assertEqual(result['missing_table_behavior'], {'conditions': 'false', 'macros': 'no-op'})

    def test_condition_bounds(self):
        rom = image()
        rom[86:88] = (2040).to_bytes(2, 'little')
        with self.assertRaisesRegex(ValueError, 'condition entry'):
            closure(rom, [])

    def test_context_and_table_instruction_overlap(self):
        rom = image()
        rom[652:656] = (0x80000200).to_bytes(4, 'little')
        result = closure(rom, [])
        self.assertFalse(result['input_bounds_valid'])
        self.assertEqual(result['register_summary']['contextual'], 1)
        rom = image()
        rom[86:88] = (244).to_bytes(2, 'little')
        self.assertIn('table_instruction_overlap', {i['kind'] for i in closure(rom, [])['issues']})

    def test_policy_does_not_allow_other_locations(self):
        rom = image()
        rom[300:302] = bytes([0x8e, 0x71])
        self.assertFalse(closure(rom, [])['board_operations'][0]['allowed'])
        self.assertTrue(closure(rom, [(hashlib.sha256(rom).hexdigest(), 300, 0x8e)])['board_operations'][0]['allowed'])
        self.assertFalse(closure(rom, [('wrong digest', 300, 0x8e)])['board_operations'][0]['allowed'])
        self.assertFalse(closure(rom, [(hashlib.sha256(rom).hexdigest(), 301, 0x8e)])['board_operations'][0]['allowed'])

    def test_ambiguous_inputs_and_identity(self):
        for mutator in (
            lambda r: r.__setitem__(slice(90, 95), b'\xff\xb8BIT'),
            lambda r: r.__setitem__(50, ord('I')),
            lambda r: r.__setitem__(51, 3),
            lambda r: r.__setitem__(45, 2),
        ):
            rom = image()
            mutator(rom)
            with self.assertRaises(ValueError):
                closure(rom, [])
        with self.assertRaisesRegex(ValueError, 'identity'):
            render(image())

    def test_m0203_first_match_and_fallback(self):
        rom = image()
        rom[112:119] = bytes([2, 0, 0, 0x20, 3, 0, 0])
        rom[800:811] = bytes([0x10, 7, 2, 2, 0, 0, 0, 0x33, 1, 0x33, 0])
        result = ram_groups(Reader(rom), (2, 7, 112))
        self.assertEqual(result['candidates'][3]['group'], 1)
        self.assertTrue(result['candidates'][3]['valid'])
        self.assertFalse(result['candidates'][2]['valid'])
        rom[801] = 3
        with self.assertRaisesRegex(ValueError, 'short M0203'):
            ram_groups(Reader(rom), (2, 7, 112))

    def test_helper_input_layouts_and_bus_denial(self):
        rom = image()
        rom[54:56] = (100).to_bytes(2, 'little')  # Move BIT M away from DCB pointer.
        rom[100:103] = bytes([2, 0, 0])
        rom[0x36:0x38] = (1000).to_bytes(2, 'little')
        rom[1000:1002] = bytes([0x40, 12])
        rom[1004:1006] = (1200).to_bytes(2, 'little')
        rom[1006:1010] = (0x4edcbdcb).to_bytes(4, 'little')
        rom[1010:1012] = (1100).to_bytes(2, 'little')
        rom[1100:1109] = bytes([0x41, 4, 1, 5, 0, 1, 0, 0, 0])
        rom[1200:1209] = bytes([0x40, 5, 1, 4, 0, 2, 0, 0, 5])
        rom[300:307] = bytes([0x4d, 0x80, 0x98, 1, 0x19, 0x73, 0x71])
        report = closure(rom, [])
        self.assertEqual(report['helper_inputs']['i2c']['resolved'][0]['drive'], 2)
        rom[1206] = 1  # Sharing bit 8.
        self.assertIn('dedicated_i2c_transport_unavailable', {r['kind'] for r in closure(rom, [])['issues']})
        rom[1206] = 0
        rom[300:303] = bytes([0xa9, 0, 0x71])
        self.assertEqual(closure(rom, [])['helper_inputs']['gpio']['entries'], 1)
        rom[1104] = 32
        with self.assertRaisesRegex(ValueError, 'GPIO line'):
            closure(rom, [])
        rom[1104] = 0
        rom[1103] = 4
        with self.assertRaisesRegex(ValueError, 'GPIO layout'):
            closure(rom, [])

    def test_check_compares_text_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'analysis').mkdir()
            rom = root / 'input.rom'
            rom.write_bytes(b'test input')
            report = root / 'analysis/devinit_closure.json'
            report.write_text('stale report')
            before = report.stat().st_mtime_ns
            with patch.object(tool, 'ROOT', root), patch.object(tool, 'render', return_value='new report'), \
                    patch.object(sys, 'argv', ['closure', '--rom', str(rom), '--check']):
                self.assertEqual(tool.main(), 1)
                self.assertEqual(report.read_text(), 'stale report')
                self.assertEqual(report.stat().st_mtime_ns, before)
                report.write_text('new report')
                before = report.stat().st_mtime_ns
                self.assertEqual(tool.main(), 0)
                self.assertEqual(report.stat().st_mtime_ns, before)

    def test_m1_translation(self):
        rom = image()
        rom[1100:1105] = bytes([0, 0, 2, 0x60, 4])
        rom[1120:1136] = bytes([1, 0] * 8)
        result = ram_groups(Reader(rom), (1, 5, 1100))
        self.assertEqual([c['group'] for c in result['candidates']], [1, 0] * 8)


if __name__ == '__main__':
    unittest.main()
