#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Inventory offline S1 verification inputs. No device or VM access.

--check compares the generated report without writing it. --require-ready
also exits 2 if the external source/ROM/toolchain inputs are incomplete.
Neither a matching file nor a successful inventory proves device readiness.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "analysis/s1-verification-inputs.json"
ROM_SHA256 = "aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54"
ROM_SIZE = 181760


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def inventory(rom=None):
    sources = []
    manifest = (ROOT / "reference/MANIFEST.md").read_text()
    for name, pin in re.findall(r"\| `([\w-]+)/` \|[^\n]*?\| ([0-9a-f]{40}) \|", manifest):
        path = ROOT / "reference" / name
        actual = None
        if path.is_dir():
            proc = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                                  text=True, capture_output=True, check=False)
            if proc.returncode == 0:
                actual = proc.stdout.strip()
        sources.append(dict(name=name, expected_revision=pin, exists=path.is_dir(),
                            actual_revision=actual, revision_matches=actual == pin))
    captures = []
    for rel in ("reference/linux-run/mmiotrace.txt.xz",
                "reference/linux-run-debug/mmiotrace.txt.xz",
                "reference/linux-run-debug/dmesg.txt.xz"):
        path = ROOT / rel
        captures.append(dict(path=rel, exists=path.is_file(),
                             sha256=digest(path) if path.is_file() else None))
    firmware = dict(supplied=rom is not None, expected_size=ROM_SIZE,
                    expected_sha256=ROM_SHA256, matches=False)
    if rom is not None:
        path = Path(rom)
        firmware.update(path=str(path), exists=path.is_file())
        if path.is_file():
            firmware.update(size=path.stat().st_size, sha256=digest(path))
            firmware["matches"] = firmware["size"] == ROM_SIZE and firmware["sha256"] == ROM_SHA256
    local_cross = ROOT / "build/haiku-cross"
    default_cross = local_cross if local_cross.is_dir() else Path.home() / "haiku-cross"
    cross = Path(os.environ.get("HAIKU_CROSS", str(default_cross)))
    toolchain = dict(root=str(cross), compiler=(cross / "generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc").is_file(),
                     headers=(cross / "haiku/headers/os/drivers/PCI.h").is_file(),
                     kernel=(cross / "lib/kernel.so").is_file())
    ready = (len(sources) == 5 and all(s["revision_matches"] for s in sources)
             and all(c["exists"] for c in captures) and firmware["matches"]
             and all(toolchain[k] for k in ("compiler", "headers", "kernel")))
    return dict(scope="OFFLINE_INPUT_INVENTORY_ONLY", sources=sources,
                captures=captures, rom=firmware, toolchain=toolchain,
                external_inputs_complete=ready, hardware_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", help="explicit offline image path; never probed from hardware")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    report = inventory(args.rom)
    content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != content:
            print("S1 input report differs; regenerate it for this checkout")
            return 1
    else:
        OUTPUT.write_text(content)
    print("S1 external inputs: " + ("complete" if report["external_inputs_complete"] else "incomplete"))
    return 2 if args.require_ready and not report["external_inputs_complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
