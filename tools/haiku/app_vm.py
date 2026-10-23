#!/usr/bin/env python3
"""Persistent cardless Haiku application VM: start, inspect, type, click and stop.

Inputs: the VM folder ($HAIKU_PERSISTENT_VM_DIR, default ~/haiku-vm) with
system.qcow2 and vars.fd, and the pinned hrev60207 anyboot ISO for a first
install ($HAIKU_VM_ISO, default <VM folder>/haiku-master-hrev60207-x86_64-anyboot.iso).
Outputs: QEMU log, PID, launch record, serial log and screenshots in the VM folder.
Prerequisites: qemu-system-x86_64, qemu-img, OVMF 4M firmware. KVM only with --kvm.
The VM never receives a host device, and the tool accepts no extra QEMU arguments.

Merged on 2026-10-23 from the copies in haiku-k40c-llm and opencode-haiku
(alignment plan decision D4). Behavior equals the opencode-haiku copy.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

VM = Path(os.environ.get("HAIKU_PERSISTENT_VM_DIR", Path.home() / "haiku-vm")).expanduser()
ISO = Path(
    os.environ.get("HAIKU_VM_ISO", VM / "haiku-master-hrev60207-x86_64-anyboot.iso")
).expanduser()
SOCKET = Path(
    "/tmp/haiku-app-" + hashlib.sha256(str(VM.resolve()).encode()).hexdigest()[:12] + ".sock"
)
EXPECTED = "4cd0765e078414681cd64b1063f5d6c0d19dc6daa51c142c544cc4d614260e35"
PLAIN = {
    " ": "spc", "-": "minus", "=": "equal", ".": "dot", ",": "comma", "/": "slash",
    ";": "semicolon", "'": "apostrophe", "[": "bracket_left", "]": "bracket_right",
    "\\": "backslash", "`": "grave_accent",
}  # fmt: skip
SHIFT = {
    "_": "minus", "+": "equal", ">": "dot", "<": "comma", "?": "slash", ":": "semicolon",
    '"': "apostrophe", "{": "bracket_left", "}": "bracket_right", "|": "backslash",
    "~": "grave_accent", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6",
    "&": "7", "*": "8", "(": "9", ")": "0",
}  # fmt: skip
READ_ONLY_COMMANDS = {
    "info status", "info mice", "info pci", "info qtree", "info version", "info block",
    "info name", "info cpus",
}  # fmt: skip


def monitor(command):
    """Send one human monitor command and return the reply text."""
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5)
        s.connect(str(SOCKET))
        data = b""
        while b"(qemu)" not in data:
            chunk = s.recv(65536)
            if not chunk:
                raise RuntimeError("QEMU closed before monitor greeting")
            data += chunk
        s.sendall((command + "\n").encode())
        data = b""
        while b"(qemu)" not in data:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
        return data.decode(errors="replace")


def key(c):
    """Map one character to a QEMU sendkey name."""
    if c.isascii() and (c.islower() or c.isdigit()):
        return c
    if c.isascii() and c.isupper():
        return "shift-" + c.lower()
    if c in PLAIN:
        return PLAIN[c]
    if c in SHIFT:
        return "shift-" + SHIFT[c]
    raise ValueError("Unsupported keyboard character: " + repr(c))


def type_line(text, submit=True):
    for c in text:
        monitor("sendkey " + key(c) + " 20")
        time.sleep(0.045)
    if submit:
        monitor("sendkey ret")
        time.sleep(0.15)


def start(installed, memory_mib, kvm=False):
    VM.mkdir(parents=True, exist_ok=True)
    if SOCKET.exists():
        try:
            monitor("info status")
        except OSError:
            SOCKET.unlink()
        else:
            raise SystemExit("This application VM is already running")
    disk = VM / "system.qcow2"
    if not installed or not disk.exists():
        if hashlib.sha256(ISO.read_bytes()).hexdigest() != EXPECTED:
            raise SystemExit("ISO checksum mismatch")
    if not disk.exists():
        subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "32G"], check=True)
    if not (VM / "vars.fd").exists():
        shutil.copyfile("/usr/share/OVMF/OVMF_VARS_4M.fd", VM / "vars.fd")
    accel = ["-accel", "kvm", "-cpu", "host"] if kvm else ["-accel", "tcg,thread=multi", "-cpu", "qemu64"]
    args = [
        "qemu-system-x86_64", "-name", "haiku-app", "-machine", "q35", *accel,
        "-smp", "2", "-m", str(memory_mib),
        "-drive", "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
        "-drive", "if=pflash,format=raw,file=" + str(VM / "vars.fd"),
        "-drive", "file=" + str(disk) + ",format=qcow2,if=none,id=system",
        "-device", "ide-hd,drive=system,bus=ide.0" + (",bootindex=1" if installed else ""),
        "-device", "qemu-xhci", "-device", "usb-tablet",
        "-qmp", "unix:" + str(SOCKET) + ".qmp,server,nowait",
        "-vga", "std",
        "-netdev", "user,id=n0,hostfwd=tcp:127.0.0.1:2233-:22", "-device", "e1000,netdev=n0",
        "-display", "none", "-serial", "file:" + str(VM / "serial.log"),
        "-monitor", "unix:" + str(SOCKET) + ",server,nowait",
    ]  # fmt: skip
    if not installed:
        boot = VM / "boot.qcow2"
        if not boot.exists():
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", "-F", "raw", "-b", str(ISO), str(boot)],
                check=True,
            )
        args += [
            "-drive", "file=" + str(boot) + ",format=qcow2,if=none,id=install",
            "-device", "ide-hd,drive=install,bus=ide.1,bootindex=1",
        ]  # fmt: skip
    log = (VM / "qemu.out").open("wb")
    p = subprocess.Popen(args, stdout=log, stderr=log, start_new_session=True)
    time.sleep(1)
    if p.poll() is not None:
        raise SystemExit((VM / "qemu.out").read_text())
    (VM / "pid").write_text(str(p.pid))
    record = {"args": args, "pid": p.pid, "started": time.time()}
    (VM / "launch.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Started cardless application VM, PID", p.pid)


def screen():
    monitor("screendump " + str(VM / "screen.ppm"))
    from PIL import Image

    Image.open(VM / "screen.ppm").save(VM / "screen.png")
    print(VM / "screen.png")


def click(text, mode="click"):
    x, y = map(int, text.split(","))
    width, height = map(int, (VM / "screen.ppm").read_bytes().split(b"\n", 3)[1].split())
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError("Click outside screenshot")
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(5)
        sock.connect(str(SOCKET) + ".qmp")
        stream = sock.makefile("rwb")
        stream.readline()

        def request(execute, args=None):
            obj = {"execute": execute}
            if args is not None:
                obj["arguments"] = args
            stream.write(json.dumps(obj).encode() + b"\n")
            stream.flush()
            while True:
                out = json.loads(stream.readline())
                if "return" in out:
                    return out
                if "error" in out:
                    raise RuntimeError(out)

        request("qmp_capabilities")
        position = [
            {"type": "abs", "data": {"axis": "x", "value": x * 32767 // (width - 1)}},
            {"type": "abs", "data": {"axis": "y", "value": y * 32767 // (height - 1)}},
        ]
        request("input-send-event", {"events": position})
        time.sleep(0.3)
        if mode == "move":
            return
        double = mode == "doubleclick"
        for _ in range(2 if double else 1):
            down = [{"type": "btn", "data": {"button": "left", "down": True}}]
            up = [{"type": "btn", "data": {"button": "left", "down": False}}]
            request("input-send-event", {"events": down})
            time.sleep(0.05 if double else 0.2)
            request("input-send-event", {"events": up})
            time.sleep(0.1 if double else 0.8)


def main():
    actions = ["start", "status", "screen", "type", "key", "command", "stop", "click", "move",
               "doubleclick", "write"]  # fmt: skip
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=actions)
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--installed", action="store_true")
    ap.add_argument("--memory-mib", type=int, choices=[4096, 8192], default=None)
    ap.add_argument("--kvm", action="store_true", help="explicit KVM with -cpu host; fails if unavailable")
    a = ap.parse_args()
    if a.action == "start":
        start(a.installed, a.memory_mib or (8192 if a.kvm else 4096), a.kvm)
    elif a.action == "status":
        try:
            result = monitor("info status")
        except (FileNotFoundError, ConnectionRefusedError):
            print("VM status: stopped")
        else:
            for line in result.splitlines():
                if line.startswith("VM status:"):
                    print(line)
            print((VM / "qemu.out").read_text()[-2000:])
    elif a.action == "screen":
        screen()
    elif a.action == "type":
        type_line(a.text)
    elif a.action == "write":
        type_line(a.text, False)
    elif a.action == "key":
        monitor("sendkey " + a.text)
        time.sleep(0.15)
    elif a.action == "command":
        if a.text not in READ_ONLY_COMMANDS:
            raise SystemExit("Only read-only monitor inventory commands are allowed")
        print(monitor(a.text))
    elif a.action in ("click", "move", "doubleclick"):
        click(a.text, a.action)
    elif a.action == "stop":
        print(monitor("quit"))


if __name__ == "__main__":
    main()
