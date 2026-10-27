#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic direction/width and deterministic check-mode regressions."""
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import post_policy as tool
from test_devinit_closure import image


class PostPolicyTests(unittest.TestCase):
    def test_table_directions(self):
        expected, code = tool.permissions(image(),set())
        self.assertEqual(expected,{(256,0x200,4,0),(261,0x1000,4,1)})
        self.assertEqual(len(code),8)

    def test_source_destination_permissions(self):
        rom=image()
        rom[300:310]=bytes([0x90,0,2,0,0,0,4,0,0,0x71])
        expected,_=tool.permissions(rom,set())
        self.assertIn((300,0x200,4,0),expected)
        self.assertIn((300,0x400,4,1),expected)
        self.assertNotIn((300,0x400,4,0),expected)
        self.assertNotIn((300,0x200,1,0),expected)

    def test_unknown_opcode_refuses(self):
        rom=image();rom[300]=0xfe
        with self.assertRaises(ValueError):
            tool.permissions(rom,set())

    def test_wrong_identity_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            rom=Path(directory)/'rom';rom.write_bytes(image())
            with self.assertRaisesRegex(ValueError,'identity'):
                tool.report(rom)

    def test_check_does_not_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'work/S1POST').mkdir(parents=True)
            report=root/'work/S1POST/policy-check.json';report.write_text('stale')
            before=report.stat().st_mtime_ns
            with patch.object(tool,'ROOT',root),patch.object(tool,'report',return_value={}),patch.object(sys,'argv',['policy','--check']):
                self.assertEqual(tool.main(),1)
                self.assertEqual(report.read_text(),'stale')
                self.assertEqual(report.stat().st_mtime_ns,before)
                report.write_text('{}\n');before=report.stat().st_mtime_ns
                self.assertEqual(tool.main(),0)
                self.assertEqual(report.stat().st_mtime_ns,before)


if __name__=='__main__':
    unittest.main()
