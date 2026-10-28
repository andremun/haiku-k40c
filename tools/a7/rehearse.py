#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Rehearse the exact A7 job cardless. Never read a grant key or sign a grant.

Run against the candidate public manifest. --check verifies immutable passing
capture hashes and its binding to the current job, binaries and guest kernel.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.a7 import build
from tools.a7.guest_job import job
from tools.a7.run import exchange
from tools.haiku import card_run, cardless_run
from tools.haiku.vm_guard import guest_lock, deadline

BINDING = ROOT / "work/S1A7REHEARSAL/rehearsal.json"


def binding(suite):
    """Bind exact canonical job bytes, artifacts and kernel without secret inputs."""
    return dict(
        job_sha256=hashlib.sha256(
            job(0, suite["guest_artifacts"]).encode()
        ).hexdigest(),
        guest_artifacts=suite["guest_artifacts"],
        kernel_sha256=suite["kernel_sha256"],
    )


def capture_verdict(folder, suite):
    """Require complete checked installations and the specific native no-card refusal."""
    output = (folder / "job-output.txt").read_text()
    serial = (folder / "serial.log").read_text(errors="replace")
    import re

    for role, info in suite["guest_artifacts"].items():
        matches = re.findall(
            r"A7-INSTALL "
            + role
            + r" size=(\d+) sha256=([0-9a-f]{64}) inode-before=(\d+) inode-after=(\d+)",
            output,
        )
        if len(matches) != 1:
            raise ValueError("missing/duplicate install evidence: " + role)
        size, digest, before, after = matches[0]
        if int(size) != info["bytes"] or digest != info["sha256"] or before != after:
            raise ValueError("install evidence differs: " + role)
    if not all(
        marker in output for marker in ("A7-DEVICE-PUBLISHED", "A7-OPEN-DEVICE")
    ):
        raise ValueError("device node/open callback not reached")
    if (
        "k40_a7: REFUSED no matching PCI card before reservation" not in serial
        or "k40_a7: FAIL client prepare" not in serial
    ):
        raise ValueError("missing expected native no-card refusal")
    if (folder / "job.exit").read_text().strip() == "0":
        raise ValueError("unexpected successful device preparation without card")
    if (folder / "kernel.sha256").read_text().strip() != suite["kernel_sha256"]:
        raise ValueError("guest kernel mismatch")
    if any((folder / name).exists() for name in ("request.bin", "grant.bin")) or any(
        x in serial
        for x in ("k40_a7: PREPARED", "k40_a7: ARM_BEFORE", "k40_a7: POST_RESULT")
    ):
        raise ValueError("unexpected request/grant or physical execution")


def validate_evidence(suite):
    """Verify saved raw captures, verdict and exact current job/artifact binding."""
    record = json.loads(BINDING.read_text())
    if BINDING.read_text() != build.dump(record):
        raise ValueError("rehearsal record is not canonical generated text")
    if (
        record["binding"] != binding(suite)
        or record["status"] != "PASS_CARDLESS_NO_CARD"
    ):
        raise ValueError("A7 rehearsal does not match job/binaries/kernel")
    folder = ROOT / record["folder"]
    for name, digest in record["capture_sha256"].items():
        if build.sha(folder / name) != digest:
            raise ValueError("rehearsal capture changed: " + name)
    launch = json.loads((folder / "launch.json").read_text())
    if launch["scope"] != "CARDLESS_KVM" or any(
        "vfio" in arg or "host=" in arg for arg in launch["args"]
    ):
        raise ValueError("rehearsal not cardless")
    if (folder / "job.sh").read_text() != job(launch["port"], suite["guest_artifacts"]):
        raise ValueError("saved guest job differs")
    capture_verdict(folder, suite)
    return record


def run():
    """Start only one fixed cardless KVM guest, preserve logs, and stop our guest."""
    if os.geteuid() == 0:
        raise ValueError("root forbidden")
    suite = json.loads(build.PUBLIC.read_text())
    for name, digest in suite["source_sha256"].items():
        if build.sha(ROOT / name) != digest:
            raise ValueError("candidate source changed: " + name)
    for role in ("identity", "owner", "client"):
        if build.sha(build.ARTIFACTS[role]) != suite["guest_artifacts"][role]["sha256"]:
            raise ValueError("candidate binary changed: " + role)
    base = cardless_run.DEFAULT_BASE
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        raise ValueError("KVM unavailable")
    with guest_lock(base.parent):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder = ROOT / ("results/" + stamp + "-a7-rehearsal")
        folder.mkdir(parents=True, exist_ok=False)
        work = ROOT / ("build/a7/rehearsal-" + stamp)
        work.mkdir(parents=True, exist_ok=False)
        for role in ("identity", "owner", "client"):
            shutil.copyfile(build.ARTIFACTS[role], work / role)
        shutil.copyfile(base.parent / "vars.fd", work / "vars.fd")
        subprocess.run(
            [
                "qemu-img",
                "create",
                "-q",
                "-f",
                "qcow2",
                "-F",
                "qcow2",
                "-b",
                str(base.resolve()),
                str(work / "overlay.qcow2"),
            ],
            check=True,
        )
        monitor = work / "monitor.sock"
        args = [
            "/usr/bin/qemu-system-x86_64",
            "-name",
            "k40-a7-cardless-rehearsal",
            "-machine",
            "q35",
            "-accel",
            "kvm",
            "-cpu",
            "host",
            "-smp",
            "2",
            "-m",
            "4096",
            "-drive",
            "if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd",
            "-drive",
            "if=pflash,format=raw,file=" + str(work / "vars.fd"),
            "-drive",
            "file=" + str(work / "overlay.qcow2") + ",format=qcow2,if=none,id=system",
            "-device",
            "ide-hd,drive=system,bus=ide.0,bootindex=1",
            "-device",
            "qemu-xhci",
            "-device",
            "usb-tablet",
            "-vga",
            "std",
            "-netdev",
            "user,id=n0",
            "-device",
            "e1000,netdev=n0",
            "-display",
            "none",
            "-serial",
            "file:" + str(folder / "serial.log"),
            "-monitor",
            "unix:" + str(monitor) + ",server,nowait",
        ]
        process = None
        status = "FAILED_CARDLESS"
        start = time.monotonic()
        try:
            with exchange(work, folder, suite) as (port, unused_ready):
                (folder / "job.sh").write_bytes((work / "job.sh").read_bytes())
                (folder / "launch.json").write_text(
                    build.dump(
                        dict(
                            args=args,
                            port=port,
                            scope="CARDLESS_KVM",
                            binding=binding(suite),
                            timeout_seconds=600,
                            source_commit=subprocess.check_output(
                                ["git", "rev-parse", "HEAD"], text=True
                            ).strip(),
                        )
                    )
                )
                with (folder / "qemu.log").open("wb") as log:
                    process = subprocess.Popen(args, stdout=log, stderr=log)
                with deadline(process, 600, folder / "watchdog.txt"):
                    launched = False
                    while time.monotonic() - start < 570 and process.poll() is None:
                        serial = (
                            (folder / "serial.log").read_text(errors="replace")
                            if (folder / "serial.log").exists()
                            else ""
                        )
                        if re.search(
                            r"^\s*(?:PANIC:|KERNEL PANIC\b)", serial, re.I | re.M
                        ):
                            raise ValueError("guest panic")
                        if not launched and (
                            "first login script" in serial
                            or 'Volume::InitialVerify(): volume at "/boot/home/config" is consistent'
                            in serial
                        ):
                            time.sleep(12)
                            card_run.hmp(monitor, "cmd", "sendkey alt-meta_l-t")
                            time.sleep(8)
                            card_run.hmp(
                                monitor,
                                "type",
                                f"curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/a7-job.sh; sh /tmp/a7-job.sh",
                            )
                            launched = True
                        if (folder / "job.exit").exists():
                            capture_verdict(folder, suite)
                            status = "PASS_CARDLESS_NO_CARD"
                            break
                        time.sleep(1)
                    if status != "PASS_CARDLESS_NO_CARD":
                        raise ValueError("guest exit or rehearsal deadline")
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            monitor.unlink(missing_ok=True)
            (folder / "result.json").write_text(
                build.dump(
                    dict(
                        status=status,
                        elapsed_seconds=round(time.monotonic() - start, 2),
                        scope="CARDLESS_ONLY",
                    )
                )
            )
            print(folder, flush=True)
        names = (
            "job.sh",
            "launch.json",
            "job-output.txt",
            "job.exit",
            "serial.log",
            "kernel.sha256",
            "http.log",
            "result.json",
            "environment.txt",
            "qemu.log",
        )
        record = dict(
            status=status,
            folder=str(folder.relative_to(ROOT)),
            binding=binding(suite),
            capture_sha256={name: build.sha(folder / name) for name in names},
        )
        BINDING.write_text(build.dump(record))
        validate_evidence(suite)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    if options.check:
        validate_evidence(json.loads(build.PUBLIC.read_text()))
    else:
        run()
