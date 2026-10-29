#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Measure saved POST paths and specified waits, without running a guest.

Read exact ROM and immutable run5/run6 serial captures. --check compares exact
text without writes. Serial rate estimates are scenarios, not QEMU time bounds.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "work/S1A7STARTUP/path-analysis.json"
ROM = Path.home() / "haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
RUNS = ("20261029-a7-508279eb", "20261029-a7-2aadfd99")


def generate():
    rom = ROM.read_bytes()
    if (
        hashlib.sha256(rom).hexdigest()
        != "aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54"
    ):
        raise ValueError("wrong ROM")
    reports = []
    paths = []
    names = [
        "src/devinit/Interpreter.cpp",
        "src/devinit/Interpreter.h",
        "src/devinit/BoundPost.cpp",
        "src/a7/NativePlatform.cpp",
        "src/a7/Owner.cpp",
        "tools/observer/supervise.py",
        "tools/a7/startup_audit.py",
    ]
    for name in RUNS:
        path = ROOT / "results" / name / "serial.log"
        raw = path.read_bytes()
        text = raw.decode()
        events = [
            (m[0], int(m[1], 16), int(m[2], 16))
            for m in re.findall(
                r"k40_a7: SCRIPT_(ACTIVE|SKIPPED) a=0x([0-9a-f]+) b=0x([0-9a-f]+)", text
            )
        ]
        paths.append(events)
        fixed = []
        conditions = []
        for i, (active, pc, op) in enumerate(events):
            wait = None
            if op == 0x69:
                wait = 20000
            if active == "ACTIVE" and op == 0x74:
                value = int.from_bytes(rom[pc + 1 : pc + 3], "little")
                wait = ((value + 900) // 1000) * 1000 if value >= 1000 else value
            if wait is not None:
                fixed.append(dict(pc=hex(pc), active=active, us=wait))
            if active == "ACTIVE" and op == 0x56:
                after = events[i + 1] if i + 1 < len(events) else None
                conditions.append(
                    dict(
                        pc=hex(pc),
                        condition=rom[pc + 1],
                        max_samples=min(rom[pc + 2] * 50, 100),
                        next_pc=hex(after[1]) if after else None,
                        next_active=after[0] if after else None,
                        adjacent=bool(after and after[1] == pc + 3),
                        actual_poll_count="UNKNOWN",
                    )
                )
        begin = raw.index(b"k40_a7: SCRIPT_")
        end = raw.index(b"k40_a7: POST_RESULT", begin)
        script_bytes = sum(
            len(line)
            for line in raw.splitlines(keepends=True)
            if b"k40_a7: SCRIPT_" in line
        )
        output_bytes = len(raw[begin:end])
        reports.append(
            dict(
                run=name,
                serial_sha256=hashlib.sha256(raw).hexdigest(),
                active=sum(e[0] == "ACTIVE" for e in events),
                skipped=sum(e[0] == "SKIPPED" for e in events),
                fixed_time_io_us=sum(w["us"] for w in fixed),
                fixed_waits=fixed,
                condition_time=conditions,
                script_serial_bytes=script_bytes,
                all_serial_bytes_during_post=output_bytes,
                physical_uart_8n1_scenarios_seconds={
                    str(rate): output_bytes * 10 / rate for rate in (19200, 115200)
                },
                uart_scenario_warning="Not a QEMU lower bound or a measured guest baud rate",
                conditional_wait_conservative_max_us=sum(
                    c["max_samples"] * 20000 for c in conditions
                ),
            )
        )
    prefix = 0
    for first, second in zip(*paths):
        if first != second:
            break
        prefix += 1
    return dict(
        scope="KNOWN saved traces and source arithmetic; runtime attribution UNKNOWN",
        rom_sha256=hashlib.sha256(rom).hexdigest(),
        common_prefix_entries=prefix,
        run6_is_exact_run5_prefix=prefix == len(paths[1]),
        runs=reports,
        source_sha256={
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in sorted(names)
        },
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
            raise ValueError("startup audit differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
