#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Decode Linux I2C wire frames and save source-bound response replay inputs.

Read the pinned debug trace. --check compares generated text without writing.
The decoder uses drive edges for bytes and captured sense bits for ACKs.
"""
import argparse
import hashlib
import json
import lzma
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/S1A7I2C/linux-i2c.json"
TRACE = ROOT / "reference/linux-run-debug/mmiotrace.txt.xz"
LOG = ROOT / "reference/linux-run-debug/dmesg.txt.xz"


def decode(rows):
    """Decode START/STOP, eight drive bits and the following sensed ACK."""
    output = 7
    frame = None
    phase = 0
    byte = 0
    pending = None
    frames = []
    for row in rows:
        op, value = row["op"], row["value"]
        if op == "W":
            scl, sda = bool(output & 1), bool(output & 2)
            next_scl, next_sda = bool(value & 1), bool(value & 2)
            if scl and next_scl and sda != next_sda:
                if not next_sda:
                    if frame is not None:
                        raise ValueError("unexpected repeated START")
                    frame = dict(
                        start_line=row["line"], start_us=row["us"], bytes=[], acks=[]
                    )
                    phase = 0
                    byte = 0
                    pending = None
                elif frame is not None:
                    if phase not in (0, 1, 9):
                        raise ValueError("incomplete byte at STOP")
                    frame.update(stop_line=row["line"], stop_us=row["us"])
                    frames.append(frame)
                    frame = None
            if frame is not None and not scl and next_scl:
                phase += 1
                if phase <= 8:
                    byte = (byte << 1) | int(next_sda)
                elif phase == 9:
                    frame["bytes"].append(byte)
                    pending = []
            if frame is not None and scl and not next_scl and phase == 9:
                if not pending:
                    raise ValueError("missing ACK sense")
                levels = {bool(r["value"] & 0x20) for r in pending}
                if len(levels) != 1:
                    raise ValueError("ambiguous ACK level")
                frame["acks"].append(
                    dict(
                        ack=not levels.pop(), sample_lines=[r["line"] for r in pending]
                    )
                )
                phase = 0
                byte = 0
                pending = None
            output = value
        elif frame is not None and phase == 9 and output & 1:
            pending.append(row)
    if frame is not None:
        raise ValueError("unterminated frame")
    return frames


def generate():
    # Debug-run BAR0: MAP record for physical c1000000, corroborated by existing
    # tools/trace_lines.py BARS. busgf119.c:37-61 defines drive/sense bit masks.
    windows = [(11800115, 11806398, "0x19"), (11807684, 11816581, "0x0d")]
    groups = [[] for _ in windows]
    for line, raw in enumerate(lzma.open(TRACE, "rt"), 1):
        p = raw.split()
        if len(p) < 6 or p[0] not in ("R", "W"):
            continue
        us = round(float(p[2]) * 1000000)
        if us > windows[-1][1]:
            break
        if int(p[4], 16) != 0xC100D054:
            continue
        for i, (start, end, register) in enumerate(windows):
            if start <= us < end:
                groups[i].append(dict(line=line, us=us, op=p[0], value=int(p[5], 16)))
    transfers = []
    for rows, (start, end, register) in zip(groups, windows):
        frames = decode(rows)
        if not frames:
            raise ValueError("no sensor frames")
        transfers.append(
            dict(
                pc="0xab8d",
                address7="0x4c",
                register=register,
                value="0x73",
                frames=frames,
            )
        )
    anchors = {}
    for line, raw in enumerate(lzma.open(LOG, "rt"), 1):
        if line in (3185, 3186, 3189, 3193, 3196):
            time = re.search(r"\[\s*([0-9]+)\.([0-9]{6})\]", raw)
            if not time:
                raise ValueError("missing kernel timestamp")
            anchors[line] = dict(
                us=int(time[1]) * 1000000 + int(time[2]), text=raw.strip()
            )
    if len(anchors) != 5:
        raise ValueError("missing timing anchors")
    timing = dict(
        anchors=anchors,
        pre_acquire_gap_us=anchors[3186]["us"] - anchors[3185]["us"],
        first_acquire_release_us=anchors[3189]["us"] - anchors[3186]["us"],
        second_acquire_release_us=anchors[3196]["us"] - anchors[3193]["us"],
    )
    sources = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "reference/nouveau/nvkm/subdev/bios/init.c",
            "reference/nouveau/nvkm/subdev/i2c/busgf119.c",
            "reference/linux-run-debug/mmiotrace.txt.xz",
            "reference/linux-run-debug/dmesg.txt.xz",
            "tools/a7/i2c_capture.py",
        )
    }
    return dict(
        scope="KNOWN Linux capture decode; NOT Haiku error classification",
        sources=sources,
        transfers=transfers,
        timing=timing,
    )


def render():
    return json.dumps(generate(), indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("I2C capture record differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
