#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Export libroot from a disposable cardless guest for a native helper link.

The existing cardless runner fixes QEMU options and transfer destinations.
Its kernel_x86_64 upload slot carries libroot bytes in this export-only job.
--check reads saved bytes/metadata only. No card, key or module is supplied.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/haiku"))
sys.path.insert(0, str(ROOT))
from tools.haiku import cardless_run
from tools.a7 import build

OUTPUT = ROOT / "work/S1A7REHEARSAL2/runtime.json"
LIBRARY = Path.home() / "haiku-cross/lib/libroot.so"


def export_job(port, driver, owner):
    """Use only fixed existing upload slots, with no driver installation."""
    return "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            f"host=http://10.0.2.2:{port}",
            'curl -fsS -T /boot/system/lib/libroot.so "$host/kernel_x86_64"',
            "sha256sum /boot/system/kernel_x86_64 > /tmp/kernel-hash",
            'curl -fsS -T /tmp/kernel-hash "$host/environment.txt"',
            "echo 0 > /tmp/export.exit",
            'curl -fsS -T /tmp/export.exit "$host/job.exit"',
            "",
        ]
    )


def render(folder):
    return build.dump(
        dict(
            scope="CARDLESS_LIBROOT_EXPORT_ONLY",
            folder=str(folder.relative_to(ROOT)),
            library_sha256=build.sha(LIBRARY),
            kernel_sha256=(folder / "environment.txt").read_text().split()[0],
            capture_sha256={
                name: build.sha(folder / name)
                for name in (
                    "kernel_x86_64",
                    "environment.txt",
                    "job.sh",
                    "launch.json",
                    "serial.log",
                    "result.json",
                )
            },
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        folder = ROOT / json.loads(OUTPUT.read_text())["folder"]
        if OUTPUT.read_text() != render(folder):
            raise ValueError("runtime export differs")
    else:
        # Change only the cardless job renderer during this synchronous call.
        # The runner's fixed QEMU command, lock and overlay behaviour stay intact.
        with patch.object(cardless_run, "guest_commands", export_job):
            folder = cardless_run.run(cardless_run.DEFAULT_BASE, None, 600, 2, True)
        if (folder / "environment.txt").read_text().split()[0] != build.sha(
            LIBRARY.with_name("kernel_x86_64")
        ):
            raise ValueError("export guest kernel differs")
        raw = (folder / "kernel_x86_64").read_bytes()
        if raw[:6] != b"\x7fELF\x02\x01":
            raise ValueError("not a native ELF runtime")
        shutil.copyfile(folder / "kernel_x86_64", LIBRARY)
        OUTPUT.write_text(render(folder))


if __name__ == "__main__":
    main()
