#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Preserve the single approved 2026-10-28 A7 attempt. No device or VM access.

Read immutable launcher evidence and the original package manifest. Copy raw
files once into the requested result folder and generate an exact summary.
--check compares raw bytes and generated text without writing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/20261028-a7-fad36717"
OUTPUT = ROOT / "results/20261028-a7-post"
ARCHIVE = ROOT / "build/a7/approved-8974695"
ROLES = ("owner", "client", "identity", "observer")
RAW = tuple(sorted(path.name for path in SOURCE.iterdir() if path.is_file()))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render():
    launch = json.loads((SOURCE / "launch.json").read_text())
    result = json.loads((SOURCE / "result.json").read_text())
    teardown = json.loads((SOURCE / "teardown.json").read_text())
    serial = (SOURCE / "serial.log").read_text(errors="replace")
    before = (SOURCE / "kernel-before.log").read_bytes()
    after = (SOURCE / "kernel-after.log").read_bytes()
    if not after.startswith(before):
        raise ValueError("kernel log is not an append-only baseline")
    if not launch["source_commit"].startswith("8974695"):
        raise ValueError("not the approved source commit")
    if result["status"] != "failed" or (SOURCE / "grant.bin").exists():
        raise ValueError("this recorder describes only the captured pre-grant stop")
    events = re.findall(r"^k40_a7: ([^\r\n]+)", serial, re.M)
    report = dict(
        stage="A7_ARM_ONLY_POST_WRITE",
        source_commit=launch["source_commit"],
        command="python3 tools/a7/run.py --run-approved-A7-once",
        preflight_commands=[
            "python3 tools/a7/build.py --check",
            "python3 tools/a7/run.py --host-check",
        ],
        authorization="User approved exactly one unchanged package run; consumed, no retry authorized",
        source_evidence=str(SOURCE.relative_to(ROOT)),
        package_sha256=sha(
            (json.dumps(launch["suite"], indent=2, sort_keys=True) + "\n").encode()
        ),
        artifact_archive={
            role: str((ARCHIVE / role).relative_to(ROOT)) for role in ROLES
        },
        artifacts=launch["suite"]["artifacts"],
        kernel_sha256=launch["suite"]["kernel_sha256"],
        rom_sha256=launch["suite"]["rom_sha256"],
        launcher_result=result,
        native_events=events,
        b5=dict(
            status="KNOWN / HARDWARE_VERIFIED under Haiku",
            identity="0x0f1240a1",
            pci_command="0x0007",
        ),
        post=dict(
            status="NOT_REACHED",
            verification="UNKNOWN; no POST result",
            arm_request_received=(SOURCE / "request.bin").exists(),
            grant_issued=False,
            register_100c10_before=None,
            register_100c10_after=None,
            readiness="NOT_REACHED",
            write_claim="INFERRED no A7 writes: no host grant; approved source gates all writes on a valid grant",
        ),
        kernel_log=dict(
            before_sha256=sha(before),
            after_sha256=sha(after),
            delta_bytes=len(after) - len(before),
            scope="KNOWN R5 selected classes only, not a complete kernel log",
        ),
        teardown=teardown,
        failure_location="INFERRED device discovery/open before the request upload; exact guest stderr unavailable",
        consumed_marker="build/a7/package/consumed.json retained; no second launch",
        S1_complete=False,
        raw_sha256={name: sha((SOURCE / name).read_bytes()) for name in RAW},
    )
    return json.dumps(report, indent=2, sort_keys=True) + "\n", after[len(before) :]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    summary, delta = render()
    launch = json.loads((SOURCE / "launch.json").read_text())
    approved = json.dumps(launch["suite"], indent=2, sort_keys=True) + "\n"
    if args.check:
        return (
            0
            if (
                all(
                    (OUTPUT / name).read_bytes() == (SOURCE / name).read_bytes()
                    for name in RAW
                )
                and (OUTPUT / "approved-package.json").read_text() == approved
                and all(
                    sha((ARCHIVE / role).read_bytes())
                    == launch["suite"]["artifacts"][role]["sha256"]
                    for role in ROLES
                )
                and (OUTPUT / "summary.json").read_text() == summary
                and (OUTPUT / "kernel-delta.log").read_bytes() == delta
            )
            else 1
        )
    OUTPUT.mkdir(mode=0o700, parents=True, exist_ok=False)
    ARCHIVE.mkdir(mode=0o700, parents=True, exist_ok=False)
    for role in ROLES:
        shutil.copyfile(launch["suite"]["artifacts"][role]["path"], ARCHIVE / role)
    (OUTPUT / "approved-package.json").write_text(approved)
    for name in RAW:
        shutil.copyfile(SOURCE / name, OUTPUT / name)
    (OUTPUT / "summary.json").write_text(summary)
    (OUTPUT / "kernel-delta.log").write_bytes(delta)
    print("A7 stopped before grant; raw evidence preserved; no retry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
