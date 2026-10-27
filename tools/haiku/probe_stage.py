#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind a linked B5 probe to its stage and source hashes.

Reads the probe and repository sources. Writes DRIVER.stage.json, or compares
its exact generated text with --check. Requires a linked Haiku ELF probe.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = "B5_IDENTITY_READ_ONLY"
SOURCES = (
    "src/os/HaikuBackend.c",
    "src/os/HaikuBackend.h",
    "src/os/HaikuProbe.c",
    "tools/haiku/build-driver.sh",
    "tools/haiku/build_backend.sh",
    "tools/haiku/kcc",
    "tools/haiku/probe_stage.py",
)


def digest(path):
    """Return a file's SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kernel_path():
    """Locate the raw guest kernel that matches the link kernel.so."""
    return Path(os.environ.get("HAIKU_CROSS", Path.home() / "haiku-cross")) / "lib/kernel_x86_64"


def manifest(driver, root=ROOT, kernel=None):
    """Describe a stage-tagged ELF and the sources used for its build."""
    data = driver.read_bytes()
    if data[:4] != b"\x7fELF" or STAGE.encode() not in data:
        raise ValueError("driver is not a stage-tagged B5 ELF")
    return {
        "stage": STAGE,
        "driver_sha256": hashlib.sha256(data).hexdigest(),
        "kernel_sha256": digest(kernel if kernel is not None else kernel_path()),
        "sources": {name: digest(root / name) for name in sorted(SOURCES)},
    }


def stage_text(driver, root=ROOT, kernel=None):
    """Return the deterministic manifest text."""
    return json.dumps(manifest(driver, root, kernel), indent=2, sort_keys=True) + "\n"


def validate(driver, root=ROOT, kernel=None):
    """Refuse a stale binary, stage record, or source set."""
    sidecar = driver.with_name(driver.name + ".stage.json")
    expected = stage_text(driver, root, kernel)
    if sidecar.read_text() != expected:
        raise ValueError("B5 stage record differs; rebuild the probe")
    return json.loads(expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate(args.driver)
    else:
        args.driver.with_name(args.driver.name + ".stage.json").write_text(
            stage_text(args.driver)
        )


if __name__ == "__main__":
    main()
