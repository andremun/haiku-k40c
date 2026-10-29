#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Record selected primary sources and enforce the run7 A7 source freeze.

Generation fetches fixed Haiku sources outside reference/ and writes contract
records. --check does not fetch, write, launch a guest or access hardware.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/S1MEMCONTRACT"
CACHE = ROOT / "build/memstage/sources"
REV = "49a0af9585d80e42240af63ab66e31e9873f59b8"
HAIKU = ("src/system/kernel/vm/vm.cpp", "src/system/kernel/arch/x86/arch_vm.cpp")
NOUVEAU = (
    "nvkm/engine/device/base.c",
    "nvkm/core/memory.c",
    "nvkm/subdev/instmem/base.c",
    "nvkm/subdev/instmem/nv50.c",
    "nvkm/subdev/fb/base.c",
    "nvkm/subdev/fb/gf100.c",
    "nvkm/subdev/fb/gk110.c",
    "nvkm/subdev/fb/ram.c",
    "nvkm/subdev/fb/ramgf100.c",
    "nvkm/subdev/bar/gf100.c",
    "nvkm/subdev/bar/g84.c",
    "nvkm/subdev/mmu/vmmgk104.c",
    "nvkm/subdev/mmu/vmmgf100.c",
    "nvkm/subdev/mmu/gk104.c",
    "nvkm/engine/fifo/gf100.c",
    "nvkm/engine/fifo/gk104.c",
    "nvkm/subdev/privring/gk104.c",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def frozen():
    old = json.loads((ROOT / "results/20261029-a7-069cb71b/launch.json").read_text())[
        "suite"
    ]["source_sha256"]
    prefixes = (
        "src/a7/",
        "src/devinit/",
        "src/memory/ArmedReference.",
        "src/runtime/PreStart.",
        "src/runtime/Bootstrap.",
        "src/os/HaikuBackend.",
        "src/os/HaikuMemory.",
    )
    extras = {
        "tools/haiku/selftest/a7_client.cpp",
        "tools/a7/guest_job.py",
        "tools/a7/open_session.c",
    }
    chosen = {
        name: digest
        for name, digest in sorted(old.items())
        if name.startswith(prefixes) or name in extras
    }
    if not chosen or any(sha(ROOT / name) != digest for name, digest in chosen.items()):
        raise ValueError("A7 run7 source changed: separate review required")
    return dict(
        scope="run7 A7 source bytes; new package key/nonce/config differ by design",
        origin="results/20261029-a7-069cb71b/launch.json",
        source_sha256=chosen,
    )


def sources():
    values = {
        "reference/nouveau/"
        + name: dict(
            sha256=sha(ROOT / "reference/nouveau" / name), kind="KNOWN/SOURCE_ONLY"
        )
        for name in sorted(NOUVEAU)
    }
    for name in HAIKU:
        path = CACHE / "haiku" / name
        values["build/memstage/sources/haiku/" + name] = dict(
            sha256=sha(path),
            url=f"https://raw.githubusercontent.com/haiku/haiku/{REV}/{name}",
            kind="KNOWN/SOURCE_ONLY; full running-kernel source identity unestablished",
        )
    vm = (CACHE / "haiku" / HAIKU[0]).read_text()
    if (
        "memoryType = B_UNCACHED_MEMORY" not in vm
        or "weak ? &memoryType : NULL" not in vm
    ):
        raise ValueError("unexpected Haiku memory-type implementation")
    return dict(
        haiku_revision=REV,
        sources=values,
        profile="explicit strong UC request; mapping error stops; effective host-RAM DMA coherency unclaimed",
        selection=dict(
            bar="BAR1",
            context_source="nvkm/subdev/bar/gf100.c:52-58",
            vmm="gk104",
            bar2=False,
            separate_d1_gate=False,
            flush_readback="observation only; Q11 open",
        ),
        code_source_sha256=sha(Path(__file__)),
        contract_sha256=sha(ROOT / "docs/S1-MEMORY-CONTRACT.md"),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        for name in HAIKU:
            path = CACHE / "haiku" / name
            if not path.exists():
                data = urllib.request.urlopen(
                    f"https://raw.githubusercontent.com/haiku/haiku/{REV}/{name}",
                    timeout=30,
                ).read(2 * 1024 * 1024 + 1)
                if len(data) > 2 * 1024 * 1024:
                    raise ValueError("source too large")
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as out:
                    out.write(data)
    records = {"a7-freeze.json": dump(frozen()), "sources.json": dump(sources())}
    for name, text in sorted(records.items()):
        path = WORK / name
        if args.check:
            if path.read_text() != text:
                raise ValueError("contract record differs: " + name)
        else:
            WORK.mkdir(parents=True, exist_ok=True)
            path.write_text(text)


if __name__ == "__main__":
    main()
