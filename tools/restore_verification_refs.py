#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Restore exact public source pins at the existing reference symlink targets.

The links in reference/ point into .refs/, an ignored link to the source cache.
The cache folder is $K40_REFS (default ~/llm-server/agent-refs). This tool
creates the .refs link when it is absent, then fetches each missing source at
its pinned commit (reference/MANIFEST.md).

--check verifies without writing or using the network. Existing repositories
must be clean and at the correct revision; they are never reset or overwritten.
This does not install system packages or access hardware.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "nouveau": ("https://github.com/torvalds/linux.git", ["drivers/gpu/drm/nouveau", "drivers/hwmon"]),
    "envytools": ("https://github.com/envytools/envytools.git", []),
    "haiku": ("https://github.com/haiku/haiku.git", ["headers/os", "headers/private/kernel", "headers/private/drivers", "headers/private/graphics", "src/add-ons/kernel/drivers/graphics/nvidia", "docs/develop"]),
    "open-gpu-doc": ("https://github.com/NVIDIA/open-gpu-doc.git", []),
    "mesa": ("https://gitlab.freedesktop.org/mesa/mesa.git", ["src/gallium/drivers/nouveau", "docs", "include/drm-uapi"]),
}


def git(path, *args, capture=False):
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          text=True, capture_output=capture)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pins = dict(re.findall(r"\| `([\w-]+)/` \|[^\n]*?\| ([0-9a-f]{40}) \|",
                           (ROOT / "reference/MANIFEST.md").read_text()))
    if set(pins) != set(SOURCES):
        raise ValueError("source manifest does not contain exactly the expected five pins")
    refs = ROOT / ".refs"
    if not refs.exists():
        if args.check:
            raise ValueError("missing .refs link; run without --check to create it")
        cache = Path(os.environ.get("K40_REFS", Path.home() / "llm-server/agent-refs"))
        cache.mkdir(parents=True, exist_ok=True)
        refs.symlink_to(cache.resolve(), target_is_directory=True)
    cache = refs.resolve()
    for name, (url, sparse) in SOURCES.items():
        link = ROOT / "reference" / name
        if not link.is_symlink():
            raise ValueError(f"refuse to alter non-symlink {link}")
        path = link.resolve()
        if name == "nouveau":
            if path.parts[-4:] != ("drivers", "gpu", "drm", "nouveau"):
                raise ValueError("unexpected Nouveau target layout")
            path = path.parents[3]
        if cache not in path.parents:
            raise ValueError(f"unexpected source-cache target: {path}")
        if not path.exists():
            if args.check:
                raise ValueError(f"missing source cache: {path}")
            path.mkdir(parents=True)
            git(path, "init")
            git(path, "remote", "add", "origin", url)
            if sparse:
                git(path, "sparse-checkout", "set", *sparse)
            git(path, "fetch", "--depth=1", "--filter=blob:none", "origin", pins[name])
            git(path, "checkout", "--detach", "FETCH_HEAD")
        actual = git(path, "rev-parse", "HEAD", capture=True).stdout.strip()
        dirty = git(path, "status", "--porcelain", capture=True).stdout
        if actual != pins[name] or dirty or not link.is_dir():
            raise ValueError(f"{name}: missing, changed or incorrect revision; not overwritten")
        print(f"{name}: clean {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
