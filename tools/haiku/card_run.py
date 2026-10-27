#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Run the authorized B5 identity probe in a bounded Haiku VFIO guest.

Reads the staged driver, persistent VM disk, and read-only host PCI inventory.
Writes a disposable overlay under build/ and incremental evidence in results/.
Requires user VFIO/KVM access and ADR 005. No host binding or BAR operations.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time

import probe_stage
from vm_guard import deadline, guest_lock

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = Path(os.environ.get(
    "HAIKU_PERSISTENT_VM_DIR", Path.home() / "haiku-vm"
)).expanduser() / "system.qcow2"
# ADR 005 restricts the host device. This is an authorization boundary,
# not a configurable device-selection default.
ALLOWED_BDF = "0000:04:00.0"
STAGE = probe_stage.STAGE
HMP = Path(__file__).with_name("qemu_hmp.py")


def preflight(bdf, sysfs=Path("/sys"), dev=Path("/dev")):
    """Read host binding and isolation. Never change a device's state."""
    if bdf != ALLOWED_BDF:
        raise ValueError("ADR 005 permits only " + ALLOWED_BDF)
    device = sysfs / "bus/pci/devices" / bdf
    if not (device / "driver").is_symlink():
        raise ValueError("driver binding absent")
    driver = (device / "driver").resolve(strict=True)
    if driver.name != "vfio-pci":
        raise ValueError("development card is not bound to vfio-pci")
    group = (device / "iommu_group").resolve(strict=True)
    if not group.name.isdecimal():
        raise ValueError("invalid IOMMU group")
    members = sorted(p.name for p in (group / "devices").iterdir())
    if members != [bdf]:
        raise ValueError("IOMMU group is not exclusive to the development card")
    vfio = dev / "vfio" / group.name
    if not vfio.exists() or not os.access(vfio, os.R_OK | os.W_OK):
        raise ValueError("VFIO group is not readable and writable by this user")
    return {"bdf": bdf, "driver": driver.name, "group": group.name,
            "members": members, "vfio": str(vfio)}


def verdict(serial, job_exit):
    """Validate the complete B5 evidence, not just a shell's exit status."""
    if re.search(r"^\s*(?:PANIC:|KERNEL PANIC\b)", serial, re.I | re.M):
        raise RuntimeError("guest panic; stop without retry")
    if "k40_os: FAIL" in serial or "cleanup failed" in serial:
        raise RuntimeError("identity probe failed; see serial log")
    if "K40-B5-END" not in serial or job_exit is None:
        return False
    if job_exit.strip() != b"0":
        raise RuntimeError("guest job failed")
    begin = serial.rfind("K40-B5-BEGIN")
    end = serial.rfind("K40-B5-END")
    section = serial[begin:end] if begin >= 0 else ""
    required = (
        "k40_stage: " + STAGE,
        "k40_os: GPU identity 0x0f1240a1; no bring-up or DMA",
        "k40_os: PASS B5 identity reads only",
    )
    if not all(marker in section for marker in required):
        raise RuntimeError("job ended without complete B5 identity evidence")
    commands = re.findall(r"k40_os: PCI command 0x([0-9a-fA-F]{4})", section)
    if not commands or any(not int(command, 16) & 2 for command in commands):
        raise RuntimeError("PCI memory decode evidence missing or off")
    return True


def qemu_args(base, folder, evidence, bdf):
    """Return the closed B5 QEMU configuration. No extra options are accepted."""
    if bdf != ALLOWED_BDF:
        raise ValueError("unauthorized host device")
    firmware = Path(os.environ.get("HAIKU_OVMF_DIR", "/usr/share/OVMF"))
    return [
        "qemu-system-x86_64", "-name", "k40-b5-identity", "-machine", "q35",
        "-accel", "kvm", "-cpu", "host", "-smp", "2", "-m", "4096",
        "-drive", "if=pflash,format=raw,readonly=on,file=" + str(firmware / "OVMF_CODE_4M.fd"),
        "-drive", "if=pflash,format=raw,file=" + str(folder / "vars.fd"),
        "-drive", "file=" + str(folder / "overlay.qcow2") + ",format=qcow2,if=none,id=system",
        "-device", "ide-hd,drive=system,bus=ide.0,bootindex=1",
        "-device", "qemu-xhci", "-device", "usb-tablet", "-vga", "std",
        "-device", "vfio-pci,host=" + bdf,
        "-netdev", "user,id=n0", "-device", "e1000,netdev=n0", "-display", "none",
        "-serial", "file:" + str(evidence / "serial.log"),
        "-monitor", "unix:" + str(folder / "monitor.sock") + ",server,nowait",
    ]


def guest_job(port):
    """Load only the staged identity driver and report shell completion."""
    return "\n".join([
        "#!/bin/sh", "set -eu", f"host=http://10.0.2.2:{port}",
        "uname -a > /tmp/k40-environment.txt",
        'curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"',
        'curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"',
        "base=/boot/system/non-packaged/add-ons/kernel/drivers",
        'mkdir -p "$base/bin" "$base/dev/misc"',
        'curl -fsS -o "$base/bin/k40_identity_probe" "$host/probe"',
        'chmod +x "$base/bin/k40_identity_probe"',
        'ln -sf ../../bin/k40_identity_probe "$base/dev/misc/k40_identity_probe"',
        "echo K40-B5-BEGIN > /dev/dprintf", "ls /dev/misc >/dev/null", "sleep 3",
        "echo K40-B5-END > /dev/dprintf", "echo 0 > /tmp/k40-job.exit",
        'curl -fsS -T /tmp/k40-job.exit "$host/job.exit"', "",
    ])


@contextmanager
def exchange(folder, evidence, kernel_sha256):
    """Serve immutable probe bytes and accept bounded, write-once evidence."""
    lock = threading.RLock()
    limits = {"environment.txt": 4096, "kernel_x86_64": 64 * 1024 * 1024,
              "job.exit": 32}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/job.sh", "/probe"):
                self.send_error(404)
                return
            data = (folder / self.path[1:]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path[1:]
            try:
                size = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                self.send_error(400)
                return
            if name not in limits or not 0 <= size <= limits[name]:
                self.send_error(413)
                return
            self.connection.settimeout(20)
            data = self.rfile.read(size)
            if len(data) != size:
                self.send_error(400)
                return
            if name == "kernel_x86_64" and hashlib.sha256(data).hexdigest() != kernel_sha256:
                (evidence / "kernel-mismatch.txt").write_text(hashlib.sha256(data).hexdigest() + "\n")
                self.send_error(409, "guest kernel differs from link kernel")
                return
            if name == "kernel_x86_64":
                # Preserve the verified hash, not another copy of the guest kernel.
                name = "kernel.sha256"
                data = (kernel_sha256 + "\n").encode("ascii")
            with lock:
                target = evidence / name
                if target.exists():
                    self.send_response(201 if target.read_bytes() == data else 409)
                else:
                    temporary = evidence / (name + ".partial")
                    temporary.write_bytes(data)
                    temporary.replace(target)
                    self.send_response(201)
            self.end_headers()

        def log_message(self, fmt, *args):
            with lock, (evidence / "http.log").open("a") as log:
                log.write(fmt % args + "\n")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    (folder / "job.sh").write_text(guest_job(server.server_address[1]))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def hmp(monitor, mode, text):
    """Send a bounded monitor request to this guest only."""
    subprocess.run([sys.executable, str(HMP), str(monitor), mode, text],
                   check=True, timeout=30, stdout=subprocess.DEVNULL)


def monitor_guest(process, folder, evidence, port, seconds):
    """Wait for boot and load once. Never retry a hung or panicked guest."""
    start = time.monotonic()
    launch_at = None
    terminal_at = None
    launched = False
    while process.poll() is None and time.monotonic() - start < seconds:
        serial_path = evidence / "serial.log"
        serial = serial_path.read_text(errors="replace") if serial_path.exists() else ""
        exit_path = evidence / "job.exit"
        job_exit = exit_path.read_bytes() if exit_path.exists() else None
        if verdict(serial, job_exit):
            return
        now = time.monotonic()
        if launch_at is None and (
            "first login script" in serial or
            'Volume::InitialVerify(): volume at "/boot/home/config" is consistent' in serial
        ):
            launch_at = now + 12
        if launch_at is not None and terminal_at is None and now >= launch_at:
            hmp(folder / "monitor.sock", "cmd", "sendkey alt-meta_l-t")
            terminal_at = now + 8
        if terminal_at is not None and not launched and now >= terminal_at:
            command = (f"curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/k40-job.sh; "
                       "sh /tmp/k40-job.sh")
            hmp(folder / "monitor.sock", "type", command)
            launched = True
        time.sleep(0.5)
    raise RuntimeError("guest exited or deadline expired; stop without retry")


def run(base, driver, evidence, seconds=600, bdf=ALLOWED_BDF):
    """Validate the stage and host, then run exactly one identity experiment."""
    if not 30 <= seconds <= 600:
        raise ValueError("timeout must be 30..600 seconds")
    if os.geteuid() == 0:
        raise ValueError("never run the card launcher as root")
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        raise ValueError("KVM unavailable to this user")
    base = base.resolve(strict=True)
    driver = driver.resolve(strict=True)
    stage = probe_stage.validate(driver)
    host = preflight(bdf)
    with guest_lock(base.parent):
        evidence = evidence.resolve()
        evidence.mkdir(parents=True, exist_ok=False)
        folder = ROOT / "build/b5" / evidence.name
        folder.mkdir(parents=True, exist_ok=False)
        if len(os.fsencode(folder / "monitor.sock")) > 107:
            raise ValueError("monitor socket path exceeds 107 bytes")
        # Copy verified bytes before launch. Validate the copy against its stage record.
        shutil.copyfile(driver, folder / "probe")
        (folder / "probe.stage.json").write_text(json.dumps(stage, indent=2, sort_keys=True) + "\n")
        probe_stage.validate(folder / "probe")
        firmware = Path(os.environ.get("HAIKU_OVMF_DIR", "/usr/share/OVMF"))
        peer_vars = base.parent / "vars.fd"
        shutil.copyfile(peer_vars if peer_vars.is_file() else firmware / "OVMF_VARS_4M.fd",
                        folder / "vars.fd")
        subprocess.run(["qemu-img", "create", "-q", "-f", "qcow2", "-F", "qcow2",
                        "-b", str(base), str(folder / "overlay.qcow2")], check=True)
        args = qemu_args(base, folder, evidence, bdf)
        record = {"args": args, "base": str(base), "timeout_seconds": seconds,
                  "stage": stage, "host": host, "scope": STAGE,
                  "source_commit": subprocess.check_output(
                      ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()}
        (evidence / "launch.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        (evidence / "command.txt").write_text(shlex.join([sys.executable, *sys.argv]) + "\n")
        status, error = "failed", ""
        process = None
        start = time.monotonic()
        try:
            with exchange(folder, evidence, stage["kernel_sha256"]) as port, (evidence / "qemu.log").open("wb") as log:
                # Recheck binding/isolation at the last boundary before QEMU.
                if preflight(bdf) != host:
                    raise ValueError("host state changed before launch")
                process = subprocess.Popen(args, stdout=log, stderr=log)
                with deadline(process, seconds, evidence / "watchdog.txt"):
                    monitor_guest(process, folder, evidence, port, seconds)
                status = "pass"
        except BaseException as exc:
            error = str(exc)
            raise
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            result = {"status": status, "error": error, "stage": STAGE,
                      "elapsed_seconds": round(time.monotonic() - start, 2),
                      "driver_sha256": stage["driver_sha256"],
                      "claim": "PMC_BOOT_0 only under Haiku" if status == "pass" else "none",
                      "verification": "HARDWARE_VERIFIED" if status == "pass" else "UNKNOWN"}
            (evidence / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            (folder / "monitor.sock").unlink(missing_ok=True)
            print(evidence, flush=True)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--driver", type=Path, default=ROOT / "build/haiku/k40_identity_probe")
    parser.add_argument("--results", type=Path,
                        default=ROOT / "results" / (datetime.now().strftime("%Y%m%d") + "-b5-identity"))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--check", action="store_true", help="check host and stage without starting a VM")
    args = parser.parse_args()
    bdf = os.environ.get("GPU_BDF", ALLOWED_BDF)
    if args.check:
        print(json.dumps({"host": preflight(bdf), "stage": probe_stage.validate(args.driver)},
                         indent=2, sort_keys=True))
    else:
        run(args.base, args.driver, args.results, args.timeout, bdf)


if __name__ == "__main__":
    main()
