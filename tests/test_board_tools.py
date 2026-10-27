#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Test board trace parsing and C++ hashing without a private ROM or hardware.

Reads synthetic capture records and deterministic temporary byte sequences.
Runs only the compiled host probe. No device, guest, or persistent output is used.
"""

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import board_trace


class BoardToolTests(unittest.TestCase):
    def test_cpp_hash_against_hashlib(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input"
            for size in (0, 1, 55, 56, 63, 64, 65, 119, 120, 255, 256, 4096, 181760):
                with self.subTest(size=size):
                    data = bytes((i * 73 + 11) % 256 for i in range(size))
                    path.write_bytes(data)
                    actual = subprocess.check_output(
                        [str(board_trace.PROBE), "--sha", str(path)], text=True
                    ).strip()
                    self.assertEqual(actual, hashlib.sha256(data).hexdigest())

    def test_rule_table_is_exactly_the_user_decision(self):
        expected = board_trace.read_policy(board_trace.ADR.read_text())
        actual = []
        for row in board_trace.probe("--rules").splitlines():
            digest, offset, opcode = row.split()
            actual.append((digest, int(offset, 16), int(opcode, 16)))
        self.assertEqual(sorted(actual), expected)
        document = board_trace.ADR.read_text()
        with self.assertRaises(ValueError):
            board_trace.read_policy(document.replace("`0x8506`", "`0x850b`"))
        with self.assertRaises(ValueError):
            board_trace.read_policy(document.replace("`IO`", "`UNKNOWN`"))

    def trace(self, base):
        # Same documented mmiotrace field order, with synthetic values.
        metadata = ["PCIDEV", "0", "10de1024", "0"]
        metadata += [hex(base)] + ["0"] * 6
        metadata += ["1000000"] + ["0"] * 6
        return [" ".join(metadata),
                f"R 4 1.0 2 {base + 0x200:#x} 0x10 0 0",
                f"W 1 1.1 2 {base + 0x6013d4:#x} 0x3f 0 0"]

    def test_capture_width_and_relocation(self):
        expected = [("R", 4, 0x200, 0x10), ("W", 1, 0x6013d4, 0x3f)]
        for base in (0xc1000000, 0xe5000000):
            self.assertEqual(board_trace.capture_window(self.trace(base), 2, 3), expected)

    def test_capture_refuses_missing_or_malformed_data(self):
        rows = self.trace(0xc1000000)
        for changed in (rows[:2], ["", *rows[1:]], [*rows[:2], "W 2 0 2 0xc16013d4 1 0 0"],
                        [*rows[:2], "W 1 0 2 0xc16013d4 0x100 0 0"]):
            with self.subTest(rows=changed), self.assertRaises(ValueError):
                board_trace.capture_window(changed, 2, 3)


if __name__ == "__main__":
    unittest.main()
