#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Pin the read-only external verification-only dependency. No key or VM access.

Reads a clean exact checkout. Generates a deterministic source/notice record.
--check compares exact text without writing. No network or reference changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path("/tmp/k40-a7-ed25519")
COMMIT = "b1f19fab4aebe607805620d25a5e42566ce46a0e"
OUTPUT = ROOT / "work/S1A7NATIVE/crypto-sources.json"
SOURCES = ("fe.c", "ge.c", "sc.c", "sha512.c", "verify.c")


def validate():
    if (
        subprocess.check_output(
            ["git", "-C", str(CACHE), "rev-parse", "HEAD"], text=True
        ).strip()
        != COMMIT
    ):
        raise ValueError("wrong crypto source revision")
    if subprocess.check_output(
        ["git", "-C", str(CACHE), "status", "--porcelain"], text=True
    ):
        raise ValueError("crypto checkout must be clean")
    names = ["license.txt", *("src/" + name for name in SOURCES)]
    names += ["src/" + p.name for p in sorted((CACHE / "src").glob("*.h"))]
    return dict(
        origin="https://github.com/orlp/ed25519",
        commit=COMMIT,
        license="zlib; original source/notice retained in external cache",
        compiled_sources=list(SOURCES),
        sha256={
            name: hashlib.sha256((CACHE / name).read_bytes()).hexdigest()
            for name in sorted(names)
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = json.dumps(validate(), indent=2, sort_keys=True) + "\n"
    if args.check:
        return 0 if OUTPUT.is_file() and OUTPUT.read_text() == expected else 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
