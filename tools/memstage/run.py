#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""One closed combined physical stage. Preparation does not authorize a launch."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.memstage import build, stage
from tools.memstage.exchange import exchange, save
from tools.memstage.monitor import Broker, drive
from tools.a7 import run as a7run
from tools.haiku import card_run, d0_run
from tools.haiku.vm_guard import guest_lock
from tools.observer.supervise import observed_child


def prerequisites(cardless=False):
    if os.geteuid() == 0:
        raise ValueError("root forbidden")
    suite = build.validate_public(require_rehearsal=not cardless)
    for tool in (
        "contract",
        "arena_report",
        "fault_report",
        "upload_report",
        "mmu_report",
        "pci",
        "host_check",
    ):
        subprocess.run(
            [sys.executable, str(ROOT / "tools/memstage" / (tool + ".py")), "--check"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
    d0_run.prerequisites()
    if not cardless:
        if os.environ.get("GPU_BDF", card_run.ALLOWED_BDF) != card_run.ALLOWED_BDF:
            raise ValueError("only development card 04:00.0")
        if (build.PACKAGE / "consumed.json").exists():
            raise ValueError("combined approval already consumed; preserve marker")
    return suite


def prepare(suite, cardless):
    stamp = datetime.now().strftime("%Y%m%d")
    ident = uuid.uuid4().hex[:8]
    evidence = (
        ROOT
        / "results"
        / (stamp + (("-batch1-rehearsal-" if cardless else "-batch1-a7-bar1-") if stage.NAME == "s1"
                    else ("-s2-rehearsal-" if cardless else "-s2-copy-")) + ident)
    )
    evidence.mkdir(mode=0o700, exist_ok=False)
    (evidence / "a7").mkdir(mode=0o700)
    folder = ROOT / "build/mem" / ident
    folder.mkdir(parents=True, mode=0o700, exist_ok=False)
    (folder / "a7").mkdir(mode=0o700)
    if max(len(os.fsencode(folder / name)) for name in ("monitor.sock", "qmp")) > 107:
        raise ValueError("monitor path too long")
    for destination, group in (
        (folder, suite["artifacts"]),
        (folder / "a7", suite["A7"]["artifacts"]),
    ):
        for role, info in group.items():
            shutil.copyfile(info["path"], destination / role)
            if build.sha(destination / role) != info["sha256"]:
                raise ValueError("staged artifact differs")
    shutil.copyfile(d0_run.BASE.parent / "vars.fd", folder / "vars.fd")
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
            str(d0_run.BASE.resolve()),
            str(folder / "overlay.qcow2"),
        ],
        check=True,
    )
    return folder, evidence


def arguments(folder, captures, suite, cardless):
    if not cardless:
        args = card_run.qemu_args(d0_run.BASE, folder, captures, card_run.ALLOWED_BDF)
        args[0] = suite["qemu"]["path"]
        args[args.index("-name") + 1] = "k40-batch1-a7-bar1"
    else:
        firmware = (
            Path(os.environ.get("HAIKU_OVMF_DIR", "/usr/share/OVMF"))
            / "OVMF_CODE_4M.fd"
        )
        args = [
            suite["qemu"]["path"],
            "-name",
            "k40-batch1-cardless",
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
            "if=pflash,format=raw,readonly=on,file=" + str(firmware),
            "-drive",
            "if=pflash,format=raw,file=" + str(folder / "vars.fd"),
            "-drive",
            "file=" + str(folder / "overlay.qcow2") + ",format=qcow2,if=none,id=system",
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
            "file:" + str(captures / "serial.log"),
            "-monitor",
            "unix:" + str(folder / "monitor.sock") + ",server,nowait",
        ]
        if any("vfio" in value or "host=" in value for value in args):
            raise ValueError("cardless command contains host device")
    return args + ["-qmp", "unix:" + str(folder / "qmp") + ",server,nowait"]


def run():
    suite = prerequisites()
    host = card_run.preflight(card_run.ALLOWED_BDF)
    with guest_lock(d0_run.BASE.parent), a7run.StrictLog() as kernel:
        folder, captures = prepare(suite, False)
        args = arguments(folder, captures, suite, False)
        save(captures / "kernel-before.log", kernel.before)
        start = time.monotonic()
        status = "failed"
        error = ""
        broker = None
        try:
            with a7run.exchange(folder / "a7", captures / "a7", suite["A7"]) as (
                a7port,
                a7ready,
            ), exchange(folder, captures, suite, a7port) as (port, ready), (
                captures / "qemu.log"
            ).open(
                "xb"
            ) as log:
                save(captures / "job.sh", (folder / "job.sh").read_bytes())
                save(captures / "a7/job.sh", (folder / "a7/job.sh").read_bytes())
                save(
                    captures / "launch.json",
                    build.dump(
                        dict(
                            stage=build.STAGE,
                            args=args,
                            suite=suite,
                            host=host,
                            port=port,
                            a7_port=a7port,
                            host_pci_command_before=a7run.command_register(),
                            timeout_seconds=600,
                            kernel_stream=kernel.metadata(),
                            source_commit=subprocess.check_output(
                                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                            ).strip(),
                        )
                    ),
                )
                if (
                    prerequisites() != suite
                    or card_run.preflight(card_run.ALLOWED_BDF) != host
                ):
                    raise ValueError("launch inputs changed")
                # Verify both role-fixed keys before consuming the one approval.
                from tools.memstage.sign import load

                load("A7", suite)
                load("memory", suite)
                kernel.poll()
                kernel.open_start_window()
                save(
                    build.PACKAGE / "consumed.json",
                    build.dump(
                        dict(
                            stage=build.STAGE,
                            package_sha256=build.sha(build.PUBLIC),
                            evidence=str(captures),
                        )
                    ),
                )
                with observed_child(
                    suite["observer"]["path"],
                    args,
                    captures / "trace.log",
                    log,
                    600,
                    captures / "watchdog.txt",
                    ["/dev/vfio/vfio", host["vfio"]],
                ) as child:
                    save(
                        captures / "processes.json",
                        build.dump(
                            dict(
                                qemu_pid=child.process.pid,
                                tracer_pid=child.tracer,
                                kernel_reader_pid=kernel.pid,
                            )
                        ),
                    )
                    broker = Broker(
                        folder,
                        captures,
                        captures / "a7",
                        suite,
                        ready,
                        False,
                        child,
                        host,
                        kernel,
                    )
                    drive(
                        broker,
                        a7ready,
                        folder / "monitor.sock",
                        port,
                        captures / "serial.log",
                        child.check,
                    )
                d0_run.finish_trace(
                    captures / "trace.log", broker.stream, broker.old, broker.pending
                )
                command = a7run.stopped_command()
                save(
                    captures / "teardown.json",
                    build.dump(
                        dict(
                            host_pci_command_after=command,
                            bus_master_enable=False,
                            claim="owned QEMU/tracer exited; read-only host command bit 2 clear; no manual reset",
                        )
                    ),
                )
                save(captures / "kernel-after.log", kernel.poll())
                status = "pass"
        except BaseException as exc:
            error = str(exc)
            raise
        finally:
            if not (captures / "teardown.json").exists():
                try:
                    save(
                        captures / "teardown.json",
                        build.dump(
                            dict(
                                host_pci_command_after=a7run.stopped_command(),
                                bus_master_enable=False,
                            )
                        ),
                    )
                except (OSError, RuntimeError) as exc:
                    save(captures / "teardown-unconfirmed.txt", str(exc) + "\n")
            if not (captures / "kernel-after.log").exists():
                try:
                    save(captures / "kernel-after.log", kernel.capture())
                except (OSError, RuntimeError):
                    save(captures / "kernel-after-unavailable.txt", "capture failed\n")
            if (captures / "serial.log").exists():
                save(captures / "a7/serial.log", (captures / "serial.log").read_bytes())
            save(
                captures / "result.json",
                build.dump(
                    dict(
                        status=status,
                        error=error,
                        stage=build.STAGE,
                        elapsed_seconds=round(time.monotonic() - start, 2),
                        S1_complete=status == "pass",  # evidence.memory_final S1 predicate (part of S2 too).
                        S2_complete=status == "pass" and stage.CURRENT["copy"],  # evidence.memory_final S2 predicate.
                        DMA_payload_visibility=False,
                        Q7="open",
                        Q11="open; A7 G1 observation only",
                        allowed_kernel_lines=getattr(kernel, "allowed", []),
                        kernel_scope="R5 selected classes; not a clean full kernel log",
                        verification="HARDWARE_VERIFIED under Haiku for this finite card/context only if status=pass",
                    )
                ),
            )
            save(
                captures / "README.md",
                f"# {stage.CURRENT['title']}\n\nStatus: {status}. {error}\n\n"
                f"Command: `K40_MEM_STAGE={stage.NAME} python3 tools/memstage/run.py --run-approved-batch1-once`.\n"
                f"Package SHA-256: `{build.sha(build.PUBLIC)}`. See launch.json for commands,\n"
                "hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7\n"
                "phase, memory-attestation.json and memory-observations.json for the BAR1 phase.\n"
                "Raw serial, R5 before/after, trace and teardown are retained.\n\n"
                "A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.\n"
                f"A pass is {stage.CURRENT['scope']}.\n"
                "It is not host payload visibility or Q11 closure.\n"
                "Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.\n",
            )
            print(captures, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--host-check", action="store_true")
    group.add_argument(
        "--run-approved-batch1-once",
        action="store_true",
        help="requires Claude acceptance and explicit user yes for this exact package",
    )
    args = parser.parse_args()
    if args.run_approved_batch1_once:
        run()
    elif args.check:
        prerequisites()
        print("Combined package checks pass; no guest started.")
    else:
        prerequisites()
        card_run.preflight(card_run.ALLOWED_BDF)
        with a7run.StrictLog() as kernel:
            kernel.poll()
        print(
            "Combined host checks pass; no guest started; no approval supplied by checks."
        )


if __name__ == "__main__":
    main()
