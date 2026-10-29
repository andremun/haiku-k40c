#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Capture fixed primary startup/debug sources outside read-only reference/.

--check compares saved source pins without network or file writes.
Haiku uses the project pin. QEMU is an explicitly labelled upstream baseline.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build/a7/startup-sources"
OUTPUT = ROOT / "work/S1A7STARTUP/source-pins.json"
REV = "49a0af9585d80e42240af63ab66e31e9873f59b8"
HAIKU = (
    "docs/user/drivers/KernelExport.dox",
    "headers/os/kernel/OS.h",
    "src/system/kernel/debug/debug.cpp",
    "src/system/kernel/arch/x86/arch_debug_console.cpp",
    "src/system/kernel/timer.cpp",
    "src/system/kernel/thread.cpp",
    "src/add-ons/kernel/bus_managers/pci/pci.cpp",
    "src/system/kernel/device_manager/legacy_drivers.cpp",
    "src/add-ons/kernel/drivers/graphics/nvidia/driver.c",
)
URLS = {
    "haiku/" + name: f"https://raw.githubusercontent.com/haiku/haiku/{REV}/{name}"
    for name in HAIKU
}
URLS["qemu/hw/char/serial.c"] = (
    "https://raw.githubusercontent.com/qemu/qemu/v6.2.0/hw/char/serial.c"
)

for name in ("chardev/char-fd.c", "io/channel-file.c", "accel/kvm/kvm-all.c"):
    URLS["qemu/" + name] = "https://raw.githubusercontent.com/qemu/qemu/v6.2.0/" + name


def render():
    kernel = Path.home() / "haiku-cross/lib/kernel_x86_64"
    disassembly = subprocess.check_output(
        ["objdump", "-d", "--disassemble=arch_debug_serial_puts", str(kernel)],
        text=True,
    )
    # Normalize the absolute filename while preserving the complete instruction text.
    disassembly = disassembly.replace(str(kernel), "kernel_x86_64")
    for instruction in ("cli", "in ", "out "):
        if instruction not in disassembly:
            raise ValueError("serial routine does not match the inspected mechanism")
    return (
        json.dumps(
            dict(
                haiku_revision=REV,
                kernel_sha256=hashlib.sha256(kernel.read_bytes()).hexdigest(),
                serial_disassembly_sha256=hashlib.sha256(
                    disassembly.encode()
                ).hexdigest(),
                scope="SOURCE_ONLY; exact running Haiku source identity unestablished. QEMU v6.2.0 upstream baseline, not Ubuntu patch proof.",
                sources={
                    name: dict(
                        url=url,
                        sha256=hashlib.sha256((CACHE / name).read_bytes()).hexdigest(),
                    )
                    for name, url in sorted(URLS.items())
                },
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        if OUTPUT.read_text() != render():
            raise ValueError("startup source record differs")
        return
    for name, url in sorted(URLS.items()):
        path = CACHE / name
        if not path.exists():
            data = urllib.request.urlopen(url, timeout=30).read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError("source too large")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as out:
                out.write(data)
    OUTPUT.write_text(render())


if __name__ == "__main__":
    main()
