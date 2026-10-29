#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Independent I2C capture controls and host response replay. No guest or card."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.a7 import i2c_capture, i2c_replay


def frame(ack):
    rows = []

    def row(op, value):
        rows.append(dict(op=op, value=value, line=len(rows) + 1, us=len(rows)))

    row("W", 5)
    row("W", 4)
    for bit in (1, 0, 0, 1, 1, 0, 0, 0):
        row("W", 4 + 2 * bit)
        row("W", 5 + 2 * bit)
        row("W", 4 + 2 * bit)
    row("W", 6)
    row("W", 7)
    row("R", 0x17 if ack else 0x37)
    row("W", 6)
    row("W", 4)
    row("W", 5)
    row("W", 7)
    return rows


class CaptureTests(unittest.TestCase):
    def test_ack_and_nack_are_distinct(self):
        for ack in (True, False):
            decoded = i2c_capture.decode(frame(ack))
            self.assertEqual(decoded[0]["bytes"], [0x98])
            self.assertEqual(decoded[0]["acks"][0]["ack"], ack)
        rows = frame(True)
        rows = [r for r in rows if r["op"] != "R"]
        with self.assertRaises(ValueError):
            i2c_capture.decode(rows)

    def test_capture_and_actual_engine_replay(self):
        captures = i2c_capture.generate()["transfers"]
        self.assertEqual([t["register"] for t in captures], ["0x19", "0x0d"])
        for transfer in captures:
            self.assertEqual(len(transfer["frames"]), 4)
            for item in transfer["frames"]:
                self.assertEqual(item["bytes"], [0x98])
                self.assertEqual([a["ack"] for a in item["acks"]], [False])
        with tempfile.TemporaryDirectory() as d:
            probe = Path(d) / "replay"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-fsanitize=undefined",
                    "-fno-sanitize-recover=all",
                    "-Isrc",
                    "-Itests",
                    "tests/a7_i2c_replay.cpp",
                    "src/devinit/I2c.cpp",
                    "-o",
                    str(probe),
                ],
                cwd=ROOT,
                check=True,
            )
            with patch.object(i2c_replay, "PROBE", probe):
                output = json.loads(i2c_replay.render())["output"]
            self.assertEqual(
                output.count(
                    "success 0 primary 5 cleanup 0 phase 2 bit 8 transmitted 1"
                ),
                8,
            )
            self.assertIn("case 9 success 1 primary 0 cleanup 0", output)


if __name__ == "__main__":
    unittest.main()
