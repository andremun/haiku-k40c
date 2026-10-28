#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic CCB omission inventory tests. No firmware, file or device access."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.a7 import omissions


def fixture():
    data = bytearray(512)
    data[0x36:0x38] = (0x80).to_bytes(2, "little")
    data[0x84:0x86] = (0xA0).to_bytes(2, "little")
    data[0x86:0x8A] = bytes.fromhex("cbbddc4e")
    data[0xA0:0xA5] = bytes((0x40, 5, 15, 4, 2))
    for i in range(15):
        if i in (0, 1, 2, 5, 6, 7, 8, 9):
            raw = (5 << 24) | i
            if i >= 6:
                raw |= 0x100 | ((i - 6) << 9)
        elif i in (10, 11, 12, 13):
            raw = (6 << 24) | (i - 10) | 0x100
        else:
            raw = 0xFF << 24
        at = 0xA5 + 4 * i
        data[at : at + 4] = raw.to_bytes(4, "little")
    return data


class OmissionsTests(unittest.TestCase):
    def test_complete_scoped_omissions(self):
        rows = omissions.inventory(fixture(), 0xD054)
        self.assertEqual(rows[0]["registers"], ["0xe50c", "0xe55c", "0xe5ac", "0xe5fc"])
        self.assertEqual(
            rows[1]["registers"],
            ["0xd014", "0xd034", "0xd0b4", "0xd0d4", "0xd0f4", "0xd114", "0xd134"],
        )
        self.assertNotIn("0xd054", rows[1]["registers"])
        self.assertEqual(rows[2]["registers"], ["0x88050"])
        self.assertTrue(
            all(
                row["reason"]
                and row["source"]
                and row["verification"] == "KNOWN / SOURCE_ONLY"
                for row in rows
            )
        )

    def test_bad_table_and_extent_rejected(self):
        for changed in (fixture()[:180], bytearray(512)):
            with self.assertRaises(ValueError):
                omissions.inventory(changed, 0xD054)
        data = fixture()
        data[0xA0] = 0x41
        with self.assertRaises(ValueError):
            omissions.inventory(data, 0xD054)
        with self.assertRaises(ValueError):
            omissions.inventory(fixture(), 0xD194)


if __name__ == "__main__":
    unittest.main()
