#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Replay decoded Linux slave responses through the actual DedicatedI2c code.

Generation compiles a host fixture. --check runs the existing fixture and
compares exact source-bound output. No card, VM or production key is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.a7 import i2c_capture

OUTPUT = ROOT / "work/S1A7I2C/response-replay.json"
PROBE = ROOT / "build/tests/a7_i2c_replay"


def render():
    captured = i2c_capture.generate()
    cases = []
    for transfer in captured["transfers"]:
        for frame in transfer["frames"]:
            cases.append(
                " ".join(
                    str(v)
                    for v in [
                        int(transfer["address7"], 16),
                        int(transfer["register"], 16),
                        int(transfer["value"], 16),
                        len(frame["bytes"]),
                        *[
                            v
                            for byte, ack in zip(frame["bytes"], frame["acks"])
                            for v in (byte, int(ack["ack"]))
                        ],
                    ]
                )
            )
    # An independent ACK-all control distinguishes a hardcoded NACK fixture.
    cases.append("76 25 115 3 152 1 25 1 115 1")
    result = subprocess.check_output(
        [str(PROBE)], input="\n".join(cases) + "\n", text=True
    )
    names = (
        "src/devinit/I2c.cpp",
        "src/devinit/I2c.h",
        "tests/a7_i2c_replay.cpp",
        "tests/i2c_wire.h",
        "tests/board_fake.h",
        "tools/a7/i2c_replay.py",
        "tools/a7/i2c_capture.py",
    )
    return (
        json.dumps(
            dict(
                scope="HOST captured slave-response replay, not cycle/timing equivalence or Haiku diagnosis",
                capture_sha256=hashlib.sha256(
                    i2c_capture.render().encode()
                ).hexdigest(),
                source_sha256={
                    n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
                    for n in sorted(names)
                },
                probe_sha256=hashlib.sha256(PROBE.read_bytes()).hexdigest(),
                output=result,
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
    if not args.check:
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
                str(PROBE),
            ],
            cwd=ROOT,
            check=True,
        )
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("I2C response replay differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
