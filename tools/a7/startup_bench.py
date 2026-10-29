#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Measure host observer cost using inert regular files, never QEMU or a card.

Generation runs three bounded samples per scenario. --check reconstructs the
report from saved samples and source hashes, without rerunning measurements.
This is a mechanism test, not a guest timing calibration or hardware result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.a7 import startup_audit

FOLDER = ROOT / "work/S1A7STARTUP/host-bench"
OUTPUT = ROOT / "work/S1A7STARTUP/host-bench.json"
PROBE = ROOT / "build/tests/a7_startup_bench"
OBSERVER = ROOT / "build/observer/strace-source/src/strace"


def render():
    saved = json.loads((FOLDER / "cases.json").read_text())
    results = []
    for scenario in saved["scenarios"]:
        times = []
        for name in scenario["samples"]:
            fields = (FOLDER / (name + ".out")).read_text().split()
            if len(fields) != 3:
                raise ValueError("bad benchmark sample")
            times.append(float(fields[0]))
        results.append(
            dict(
                name=scenario["name"],
                median_seconds=statistics.median(times),
                seconds=times,
            )
        )
    names = (
        "tools/a7/startup_bench.py",
        "tests/a7_startup_bench.c",
        "tools/observer/supervise.py",
    )
    return (
        json.dumps(
            dict(
                scope="HOST inert syscall/regular-file mechanism measurement; NOT guest attribution",
                parameters=saved,
                results=results,
                source_sha256={
                    n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
                    for n in sorted(names)
                },
                observer_sha256=hashlib.sha256(OBSERVER.read_bytes()).hexdigest(),
                probe_sha256=hashlib.sha256(PROBE.read_bytes()).hexdigest(),
                sample_sha256={
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(FOLDER.glob("*.out"))
                },
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
    if args.check:
        if OUTPUT.read_text() != render():
            raise ValueError("benchmark record differs")
        return
    FOLDER.mkdir(exist_ok=False)
    subprocess.run(
        [
            "cc",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "tests/a7_startup_bench.c",
            "-o",
            str(PROBE),
        ],
        cwd=ROOT,
        check=True,
    )
    total = startup_audit.generate()["runs"][1]["all_serial_bytes_during_post"]
    scenarios = []
    for traced, chunk, extra in (
        (False, 1, 0),
        (True, 1, 0),
        (False, 4096, 0),
        (True, 4096, 0),
        (False, 1, 2),
        (True, 1, 2),
    ):
        name = f"traced-{int(traced)}-chunk-{chunk}-extra-{extra}"
        samples = []
        for repeat in range(3):
            sample = name + "-" + str(repeat)
            samples.append(sample)
            target = FOLDER / (sample + ".data")
            command = [str(PROBE), str(target), str(total), str(chunk), str(extra)]
            if traced:
                command = [
                    str(OBSERVER),
                    "-f",
                    "-qq",
                    "-y",
                    "-X",
                    "raw",
                    "-e",
                    "trace=openat,ioctl,close,dup,dup2,dup3,fcntl,execve,execveat,unshare,close_range",
                    "-e",
                    "signal=none",
                    "-P",
                    str(FOLDER / "unmatched-filter"),
                    "-o",
                    str(FOLDER / (sample + ".trace")),
                    "--",
                    *command,
                ]
            with (FOLDER / (sample + ".out")).open("xb") as out, (
                FOLDER / (sample + ".err")
            ).open("xb") as err:
                subprocess.run(command, stdout=out, stderr=err, check=True, timeout=30)
            target.unlink()
        scenarios.append(
            dict(
                name=name,
                traced=traced,
                chunk=chunk,
                extra_inert_syscalls_per_write=extra,
                samples=samples,
            )
        )
    (FOLDER / "cases.json").write_text(
        json.dumps(
            dict(
                bytes=total,
                repeats=3,
                observer_filter_matches_supervise=True,
                daemonize_flag_omitted=True,
                scenarios=scenarios,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    OUTPUT.write_text(render())


if __name__ == "__main__":
    main()
