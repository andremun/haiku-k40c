#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Build only the pinned offline nvbios decoder, without installing packages.

Extract bison/flex/m4 packages into build/decoder-tools/root first (see
work/V2/RESULT.md). Generated sources, binary and metadata stay under build/.
No upstream source files are modified; no firmware/device is opened here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "reference/envytools"
BUILD = ROOT / "build/nvbios"
TOOLS = ROOT / "build/decoder-tools/root/usr"
PIN = "f102b82381f3f11cee113d16374c87091db039d9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(SOURCE), "status", "--porcelain"], text=True)
    if revision != PIN or dirty:
        raise ValueError("requires unchanged envytools at the exact recorded pin")
    metadata = BUILD / "build.json"
    if args.check:
        record = json.loads(metadata.read_text())
        if record["source_revision"] != PIN or record["binary_sha256"] != sha(BUILD / "nvbios"):
            raise ValueError("decoder binary/metadata mismatch")
        for path, digest in record["tool_sha256"].items():
            if sha(Path(path)) != digest:
                raise ValueError(f"changed build tool: {path}")
        print("Pinned decoder binary and recorded build tools match")
        return 0
    generated = BUILD / "gen"
    generated.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, BISON_PKGDATADIR=str(TOOLS / "share/bison"), M4=str(TOOLS / "bin/m4"))
    commands = [
        [str(TOOLS / "bin/bison"), "-d", "-o", str(generated / "easm_parse.c"), str(SOURCE / "easm/easm_parse.y")],
        [str(TOOLS / "bin/flex"), "--header-file=" + str(generated / "easm_lex.h"), "-o", str(generated / "easm_lex.c"), str(SOURCE / "easm/easm_lex.l")],
    ]
    files = []
    for directory, library in (("util", "envyutil"), ("easm", "easm"), ("envydis", "envy"), ("nvbios", "envybios")):
        text = (SOURCE / directory / "CMakeLists.txt").read_text()
        names = re.search(r"add_library\(" + library + r"\s+(.*?)\)", text, re.S).group(1).split()
        files.extend(str(SOURCE / directory / name) for name in names if name.endswith(".c"))
    files.extend([str(SOURCE / "nvbios/nvbios.c"), str(generated / "easm_parse.c"), str(generated / "easm_lex.c")])
    commands.append(["gcc", "-std=gnu11", "-O2", "-Wno-missing-braces", "-I" + str(SOURCE / "include"), "-I" + str(generated), *files, "-lm", "-o", str(BUILD / "nvbios")])
    with (BUILD / "build.log").open("w") as log:
        for cmd in commands:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    record = dict(source_revision=PIN, commands=commands,
                  compiler=subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0],
                  binary_sha256=sha(BUILD / "nvbios"),
                  tool_sha256={str(TOOLS / "bin" / tool): sha(TOOLS / "bin" / tool) for tool in ("bison", "flex", "m4")})
    metadata.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("Built pinned offline decoder:", BUILD / "nvbios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
