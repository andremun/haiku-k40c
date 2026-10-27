#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Re-pin the shared Haiku tools in the authorized application repository.

Reads committed owner files and the existing application tool metadata.
Writes only reference/HAIKU-TOOLS.json, or compares exact text with --check.
Requires a committed tool revision. Does not commit or push either repository.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ADDITIONS = ("tools/haiku/card_run.py", "tools/haiku/probe_stage.py",
             "tools/haiku/vm_guard.py", "tools/haiku/build_backend.sh",
             "tools/haiku/selftest/memory.cpp", "tools/haiku/selftest/owner.cpp")


def generate(target, commit):
    """Keep prior pin fields and update sorted file hashes from Git blobs."""
    pin = json.loads(target.read_text())
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", commit + "^{commit}"], text=True
    ).strip()
    names = sorted(set(pin["files"]) | set(ADDITIONS))
    hashes = {}
    for name in names:
        content = subprocess.check_output(["git", "-C", str(ROOT), "show", revision + ":" + name])
        if (ROOT / name).read_bytes() != content:
            raise ValueError("tool has uncommitted changes: " + name)
        hashes[name] = hashlib.sha256(content).hexdigest()
    pin.update(commit=revision, branch="main", files=hashes)
    return json.dumps(pin, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path,
                        default=ROOT.parent / "haiku-k40c-llm/reference/HAIKU-TOOLS.json")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = generate(args.target, args.commit)
    if args.check:
        if args.target.read_text() != text:
            raise SystemExit("shared tool pin differs")
    else:
        args.target.write_text(text)


if __name__ == "__main__":
    main()
