#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Measure the native logging path in two fixed cardless guests, never a card.

--check verifies saved input, probe, source and guest evidence without a launch.
Generation refuses an existing result binding. Stops are never retried here.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.haiku import cardless_run

OUTPUT = ROOT / "work/S1A7BUFFER/native-logging.json"
PROBE = ROOT / "build/haiku/k40_a7_logging"
INPUT = ROOT / "build/a7/logging-input/a7_logging_input.h"
SERIAL = ROOT / "results/20261029-a7-2aadfd99/serial.log"
OBSERVER = ROOT / "build/observer/strace-source/src/strace"
SOURCES = (
    "src/a7/PostDiagnostics.h",
    "tools/haiku/selftest/a7_logging.cpp",
    "tools/haiku/cardless_run.py",
    "tools/observer/supervise.py",
    "tools/a7/logging_bench.py",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def input_text():
    rows = re.findall(
        r"k40_a7: SCRIPT_(ACTIVE|SKIPPED) a=0x([0-9a-f]+) b=0x([0-9a-f]+)",
        SERIAL.read_text(),
    )
    if len(rows) != 528:
        raise ValueError("unexpected saved trace size")
    return (
        "struct LoggingEntry {bool active;unsigned pc,op;};\n"
        "static constexpr LoggingEntry loggingEntries[]={\n"
        + "".join(
            "{%s,0x%s,0x%s},\n" % ("true" if active == "ACTIVE" else "false", pc, op)
            for active, pc, op in rows
        )
        + "};\n"
    )


def evidence(folder):
    launch = json.loads((folder / "launch.json").read_text())
    result = json.loads((folder / "result.json").read_text())
    if result["status"] != "pass" or launch["scope"] != "CARDLESS_KVM":
        raise ValueError("native logging guest failed")
    if any("vfio-pci" in arg or "host=" in arg for arg in launch["args"]):
        raise ValueError("guest is not cardless")
    kernel = sha(Path.home() / "haiku-cross/lib/kernel_x86_64")
    if sha(folder / "kernel_x86_64") != kernel or launch["artifacts_sha256"][
        "probe"
    ] != sha(PROBE):
        raise ValueError("native logging probe/kernel changed")
    serial = (folder / "serial.log").read_text()
    blocks = re.findall(
        r"logging_probe: BEGIN CARDLESS_A7_LOGGING_ONLY(.*?)logging_probe: END",
        serial,
        re.S,
    )
    if not blocks or "k40_os: FAIL" in serial or "PANIC:" in serial:
        raise ValueError("native logging results missing or failed")
    samples = []
    for block in blocks:
        rows = re.findall(
            r"logging_probe: SAMPLE index=(\d+) live_us=(\d+) buffered_us=(\d+) drain_us=(\d+) entries=(\d+)",
            block,
        )
        if (
            len(rows) != 3
            or [int(r[0]) for r in rows] != [0, 1, 2]
            or any(int(r[4]) != 528 for r in rows)
        ):
            raise ValueError("native logging samples incomplete")
        if block.count("k40_a7: TRACE_END a=0x0 b=0x0") != 3:
            raise ValueError("native logging trace unhealthy")
        samples.extend(
            dict(index=int(i), live_us=int(l), buffered_us=int(b), drain_us=int(d))
            for i, l, b, d, _ in rows
        )
    files = [
        "launch.json",
        "result.json",
        "serial.log",
        "job.exit",
        "environment.txt",
        "kernel_x86_64",
        "probe",
    ]
    if launch["logging_observer"]:
        files += ["observer.trace"]
        if (folder / "observer-watchdog.json").exists():
            raise ValueError("observer watchdog fired")
    return dict(
        folder=str(folder.relative_to(ROOT)),
        logging_observer=launch["logging_observer"],
        samples=samples,
        medians_us={
            name: statistics.median(s[name] for s in samples)
            for name in ("live_us", "buffered_us", "drain_us")
        },
        files_sha256={n: sha(folder / n) for n in sorted(files)},
    )


def render(folders):
    return dump(
        dict(
            scope="CARDLESS native logging mechanics only; not GPU POST timing",
            kernel_sha256=sha(Path.home() / "haiku-cross/lib/kernel_x86_64"),
            observer_sha256=sha(OBSERVER),
            probe_sha256=sha(PROBE),
            input_sha256=hashlib.sha256(input_text().encode()).hexdigest(),
            capture_sha256=sha(SERIAL),
            source_sha256={n: sha(ROOT / n) for n in sorted(SOURCES)},
            runs=[evidence(folder) for folder in folders],
        )
    )


def validate():
    raw = OUTPUT.read_text()
    data = json.loads(raw)
    folders = [ROOT / run["folder"] for run in data["runs"]]
    if [run["logging_observer"] for run in data["runs"]] != [
        False,
        True,
    ] or raw != render(folders):
        raise ValueError("native logging evidence differs")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate()
        return
    if OUTPUT.exists():
        raise ValueError("preserve existing benchmark binding")
    INPUT.parent.mkdir(parents=True, exist_ok=True)
    INPUT.write_text(input_text())
    subprocess.run(
        [
            "bash",
            "tools/haiku/build-driver.sh",
            "k40_a7_logging",
            "tools/haiku/selftest/a7_logging.cpp",
        ],
        cwd=ROOT,
        env=dict(
            __import__("os").environ,
            KCFLAGS="-Werror -Wframe-larger-than=4096 -Isrc -I" + str(INPUT.parent),
        ),
        check=True,
    )
    frozen = {name: sha(ROOT / name) for name in SOURCES}
    frozen_probe = sha(PROBE)
    folders = []
    for observed in (False, True):
        folder = cardless_run.run(
            cardless_run.DEFAULT_BASE, PROBE, 600, 2, True, logging_observer=observed
        )
        saved = ROOT / (
            "results/"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ("-a7-logging-observed" if observed else "-a7-logging-plain")
        )
        saved.mkdir(exist_ok=False)
        # Save bounded evidence, not the disposable disk or firmware.
        for name in (
            "launch.json",
            "result.json",
            "serial.log",
            "job.exit",
            "environment.txt",
            "kernel_x86_64",
            "probe",
            "qemu.log",
            "http.log",
            "observer.trace",
            "observer-watchdog.json",
        ):
            if (folder / name).is_file():
                shutil.copyfile(folder / name, saved / name)
        folders.append(saved)
        evidence(saved)
    if frozen != {name: sha(ROOT / name) for name in SOURCES} or frozen_probe != sha(
        PROBE
    ):
        raise ValueError("native logging inputs changed during measurement")
    OUTPUT.write_text(render(folders))
    validate()
    print("Native logging benchmark passed; cardless only")


if __name__ == "__main__":
    main()
