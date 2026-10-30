#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Repeat the existing combined cardless job with a separate evidence summary.

--run starts one guarded cardless guest. --check reads evidence only. The original
launcher, installer, binaries, summary, package and consumed marker stay unchanged.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.memstage import build, rehearse

WORK = ROOT / "work/S1CARDLESSRECHECK"
OUTPUT = WORK / "rehearsal.json"
PRESERVED = WORK / "preserved.json"
INPUTS = (
    "work/S1MEMPACKAGE/package.json",
    "work/S1MEMPACKAGE/rehearsal.json",
    "build/memstage/package/consumed.json",
    "work/S1BATCH2PLAN/review-inputs.json",
)


def hashes():
    """Hash the existing records that this rerun must preserve."""
    return {name: build.sha(ROOT / name) for name in sorted(INPUTS)}


def check():
    """Validate the new capture and compare the preserved input hashes."""
    if json.loads(PRESERVED.read_text()) != hashes():
        raise ValueError("prior records changed during the cardless recheck")
    rehearse.OUTPUT = OUTPUT
    record = rehearse.validate(build.validate_public(require_rehearsal=False))
    result = json.loads((ROOT / record["folder"] / "result.json").read_text())
    if result["status"] != "PASS_CARDLESS_NO_CARD" or any(
        result[name]
        for name in (
            "host_device_assigned",
            "keys_read",
            "grants_issued",
            "hardware_evidence",
            "S1_complete",
        )
    ):
        raise ValueError("cardless evidence scope mismatch")
    print(record["folder"])
    print("PASS: existing A7/memory install, no-card refusal and reload only.")


def main():
    """Start one requested rehearsal, or verify its saved evidence without writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.run:
        # An existing receipt prevents an accidental second attempt after a stop.
        with PRESERVED.open("x") as target:
            target.write(build.dump(hashes()))
        rehearse.OUTPUT = OUTPUT
        rehearse.run()
    check()


if __name__ == "__main__":
    main()
