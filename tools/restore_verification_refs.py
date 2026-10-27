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
It also compares the sparse list of each cache with SOURCES and checks that
every path a tool reads (REQUIRED) exists. The envytools decoder source comes
from a full envytools checkout (envytools_full()), never from the sparse cache.
This does not install system packages or access hardware.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
# Sparse lists of the caches on the T7610 (git sparse-checkout list, no-cone mode,
# without the leading and trailing "/"). An empty list means not sparse.
SOURCES = {
    "nouveau": ("https://github.com/torvalds/linux.git", ["drivers/gpu/drm/nouveau"]),
    "envytools": ("https://github.com/envytools/envytools.git", ["docs", "rnndb"]),
    "haiku": ("https://github.com/haiku/haiku.git", ["docs/develop", "headers/os", "headers/private/drivers", "headers/private/graphics", "headers/private/kernel", "src/add-ons/kernel/drivers/graphics/nvidia"]),
    "open-gpu-doc": ("https://github.com/NVIDIA/open-gpu-doc.git", []),
    "mesa": ("https://gitlab.freedesktop.org/mesa/mesa.git", ["docs/features.txt", "docs/license.rst", "include/drm-uapi/nouveau_drm.h", "src/gallium/drivers/nouveau"]),
}
# Paths that the tools read, relative to the link target reference/<name>/.
REQUIRED = {
    "nouveau": ["nouveau_dma.c", "nouveau_dma.h", "nvkm/engine/device/base.c", "nvkm/engine/fifo/gf100.c",
                "nvkm/engine/fifo/gk104.c", "nvkm/subdev/bar/g84.c", "nvkm/subdev/bios/init.c",
                "nvkm/subdev/fb/gf100.c", "nvkm/subdev/instmem/nv50.c", "nvkm/subdev/mmu"],
    "envytools": ["nvbios/nvbios.c", "rnndb"],
    "haiku": [],
    "open-gpu-doc": ["Devinit/devinit.xml"],
    "mesa": ["src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h", "src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h"],
}
# Required paths that the full decoder checkout supplies instead of the cache.
DECODER = {("envytools", "nvbios/nvbios.c")}
ENVYTOOLS_DEFAULT = Path.home() / "haiku-cross/src/envytools"


def git(path, *args, capture=False):
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          text=True, capture_output=capture)


def manifest_pins():
    """Return the pinned commit of each source from reference/MANIFEST.md."""
    pins = dict(re.findall(r"\| `([\w-]+)/` \|[^\n]*?\| ([0-9a-f]{40}) \|",
                           (ROOT / "reference/MANIFEST.md").read_text()))
    if set(pins) != set(SOURCES):
        raise ValueError("source manifest does not contain exactly the expected five pins")
    return pins


def sparse_list(path):
    """Return the sorted sparse entries of a checkout without "/" at both ends; [] if not sparse."""
    result = subprocess.run(["git", "-C", str(path), "sparse-checkout", "list"],
                            text=True, capture_output=True)
    if result.returncode != 0:
        return []
    # git 2.34 does not know "set --no-cone" and stores "--no-cone" as a pattern
    # line. Such a line is not a path of these caches: skip option text.
    return sorted(line.strip().strip("/") for line in result.stdout.splitlines()
                  if line.strip() and not line.strip().startswith("--"))


def envytools_full():
    """Return the path of a clean, full envytools checkout at the pin. Reads only.

    Path: $K40_ENVYTOOLS_FULL, default ~/haiku-cross/src/envytools. Raises ValueError
    when the path is absent, at another commit, changed, sparse or without nvbios.c.
    """
    path = Path(os.environ.get("K40_ENVYTOOLS_FULL", ENVYTOOLS_DEFAULT)).expanduser()
    pin = manifest_pins()["envytools"]
    hint = "set K40_ENVYTOOLS_FULL or run tools/restore_verification_refs.py without --check for the commands"
    if not path.is_dir():
        raise ValueError(f"envytools (full, decoder): {path} does not exist; {hint}")
    head = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, capture_output=True)
    if head.returncode != 0 or head.stdout.strip() != pin:
        raise ValueError(f"envytools (full, decoder): {path} is not at the pin {pin}")
    changed = git(path, "status", "--porcelain", "--untracked-files=no", capture=True).stdout
    if changed:
        raise ValueError(f"envytools (full, decoder): {path} has changed tracked files")
    if sparse_list(path):
        raise ValueError(f"envytools (full, decoder): {path} is a sparse checkout")
    if not (path / "nvbios/nvbios.c").is_file():
        raise ValueError(f"envytools (full, decoder): {path}/nvbios/nvbios.c is missing")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pins = manifest_pins()
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
                # "init --no-cone", then "set": also correct on git 2.34 (see sparse_list).
                git(path, "sparse-checkout", "init", "--no-cone")
                git(path, "sparse-checkout", "set", *("/" + entry for entry in sparse))
            git(path, "fetch", "--depth=1", "--filter=blob:none", "origin", pins[name])
            git(path, "checkout", "--detach", "FETCH_HEAD")
        actual = git(path, "rev-parse", "HEAD", capture=True).stdout.strip()
        dirty = git(path, "status", "--porcelain", capture=True).stdout
        if actual != pins[name] or dirty or not link.is_dir():
            raise ValueError(f"{name}: missing, changed or incorrect revision; not overwritten")
        if args.check:
            found = sparse_list(path)
            if found != sorted(sparse):
                missing = sorted(set(sparse) - set(found))
                extra = sorted(set(found) - set(sparse))
                raise ValueError(f"{name}: sparse list differs from SOURCES; missing {missing}, extra {extra}")
            for rel in REQUIRED[name]:
                if (name, rel) not in DECODER and not (link / rel).exists():
                    raise ValueError(f"{name}: required path {rel} is missing (sparse list: {found or 'not sparse'})")
        print(f"{name}: clean {actual}")
    if args.check:
        print(f"envytools (full, decoder): clean {pins['envytools']} {envytools_full()}")
    else:
        try:
            envytools_full()
        except ValueError as error:
            target = os.environ.get("K40_ENVYTOOLS_FULL", ENVYTOOLS_DEFAULT)
            print(f"{error}\nMake the full decoder checkout with:\n"
                  f"  git clone {SOURCES['envytools'][0]} {target}\n"
                  f"  git -C {target} checkout --detach {pins['envytools']}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
