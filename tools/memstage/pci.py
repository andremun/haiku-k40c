# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Fixed read-only QMP PCI resource witness. No arbitrary monitor commands."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "build/memstage/sources/qemu/pci.json"
URL = "https://raw.githubusercontent.com/qemu/qemu/v6.2.0/qapi/pci.json"
DIGEST = "20d52b33b118f0c7104ad0fcffc07019effda84314c8922b941920ac1b957dca"
OUTPUT = ROOT / "work/S1MEMPACKAGE/qmp-pci-source.json"


def source_record():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("PCI schema pin differs")
    return dict(
        url=URL,
        sha256=DIGEST,
        scope="QEMU 6.2 upstream QAPI schema baseline, not exact Ubuntu source identity",
        fields="qapi/pci.json:26-48,77-88,124-170; fixed query-pci; PCI bridge devices recursion",
    )


def snapshot(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(3)
        connection.connect(str(path))
        buffer = b""
        total = 0
        deadline = time.monotonic() + 10

        def receive(expected=None):
            nonlocal buffer, total
            for _ in range(100):
                while b"\n" not in buffer:
                    if time.monotonic() > deadline:
                        raise RuntimeError("PCI monitor deadline")
                    data = connection.recv(65536)
                    if not data:
                        raise RuntimeError("PCI monitor EOF")
                    buffer += data
                    total += len(data)
                    if total > 4 * 1024 * 1024:
                        raise RuntimeError("PCI monitor output bound")
                line, buffer = buffer.split(b"\n", 1)
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RuntimeError("PCI monitor packet")
                if expected is None:
                    if "QMP" not in value:
                        raise RuntimeError("PCI monitor greeting")
                    return
                if "event" in value:
                    continue
                if (
                    value.get("id") != expected
                    or "error" in value
                    or "return" not in value
                ):
                    raise RuntimeError("PCI monitor reply")
                return value["return"]
            raise RuntimeError("PCI monitor event bound")

        def send(command, ident):
            connection.sendall(
                (json.dumps(dict(execute=command, id=ident)) + "\r\n").encode()
            )
            return receive(ident)

        receive()
        send("qmp_capabilities", 1)
        status = send("query-status", 2)
        if (
            not isinstance(status, dict)
            or status.get("running") is not True
            or status.get("status") != "running"
        ):
            raise RuntimeError("PCI witness guest not running")
        return send("query-pci", 3)


def resources(value):
    matches = []
    seen = set()
    count = 0

    def devices(items, depth):
        nonlocal count
        if depth > 8 or not isinstance(items, list):
            raise ValueError("PCI topology bounds/type")
        for device in items:
            count += 1
            if count > 256 or not isinstance(device, dict):
                raise ValueError("PCI device bound/type")
            ident = tuple(device.get(name) for name in ("bus", "slot", "function"))
            if (
                any(type(x) is not int for x in ident)
                or not (
                    0 <= ident[0] < 256 and 0 <= ident[1] < 32 and 0 <= ident[2] < 8
                )
                or ident in seen
            ):
                raise ValueError("PCI device identity")
            seen.add(ident)
            ids = device.get("id")
            if not isinstance(ids, dict):
                raise ValueError("PCI vendor/device missing")
            if ids.get("vendor") == 0x10DE and ids.get("device") == 0x1024:
                matches.append(device)
            if "pci_bridge" in device:
                bridge = device["pci_bridge"]
                if not isinstance(bridge, dict):
                    raise ValueError("PCI bridge type")
                devices(bridge.get("devices", []), depth + 1)

    if not isinstance(value, list) or not value or len(value) > 256:
        raise ValueError("PCI bus list missing/bound")
    for bus in value:
        if not isinstance(bus, dict):
            raise ValueError("PCI bus type")
        devices(bus.get("devices"), 0)
    if len(matches) != 1:
        raise ValueError("PCI target missing/ambiguous")
    target = matches[0]
    regions = target.get("regions")
    if not isinstance(regions, list) or len(regions) > 7:
        raise ValueError("PCI regions missing/bound")
    selected = {}
    for number in (0, 1):
        items = [
            r
            for r in regions
            if isinstance(r, dict)
            and type(r.get("bar")) is int
            and r.get("bar") == number
        ]
        if len(items) != 1:
            raise ValueError("PCI BAR missing/ambiguous")
        item = items[0]
        address = item.get("address")
        size = item.get("size")
        if (
            item.get("type") != "memory"
            or type(address) is not int
            or type(size) is not int
            or address <= 0
            or size <= 0
            or address % 4096
            or size % 4096
            or size & (size - 1)
            or address + size > 2**64
        ):
            raise ValueError("PCI memory BAR profile")
        selected[str(number)] = dict(
            address=address, bytes=size, mem_type_64=item.get("mem_type_64")
        )
    a, b = selected["0"], selected["1"]
    if (
        not 8388608 <= a["bytes"] <= 16777216
        or not 8192 <= b["bytes"] <= 2**40
        or a["mem_type_64"] is not False
        or type(b["mem_type_64"]) is not bool
    ):
        raise ValueError("PCI BAR0/BAR1 finite profile")
    if (
        a["address"] < b["address"] + b["bytes"]
        and b["address"] < a["address"] + a["bytes"]
    ):
        raise ValueError("PCI BAR overlap")
    return dict(
        bus=target["bus"],
        slot=target["slot"],
        function=target["function"],
        bars=selected,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check and not SOURCE.exists():
        data = urllib.request.urlopen(URL, timeout=30).read(200000)
        if hashlib.sha256(data).hexdigest() != DIGEST:
            raise ValueError("downloaded schema differs")
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE.write_bytes(data)
    text = json.dumps(source_record(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("PCI source record differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
