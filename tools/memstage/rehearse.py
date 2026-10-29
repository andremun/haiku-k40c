#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Run/check the exact combined installer cardlessly. No key read, signing or VFIO."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.memstage import build, evidence, pci
from tools.memstage.guest_job import job
from tools.memstage.exchange import exchange, save
from tools.memstage.monitor import Broker, drive
from tools.memstage.run import prerequisites, prepare, arguments
from tools.a7 import run as a7run
from tools.a7.guest_job import job as a7_job
from tools.haiku import card_run, d0_run
from tools.haiku.vm_guard import guest_lock, deadline

OUTPUT = ROOT / "work/S1MEMPACKAGE/rehearsal.json"
RELOAD = "echo K40-BATCH-RELOAD-BEGIN > /dev/dprintf; touch /boot/system/non-packaged/add-ons/kernel/drivers/bin/k40_identity_probe /boot/system/non-packaged/add-ons/kernel/drivers/bin/k40_a7_stage /boot/system/non-packaged/add-ons/kernel/drivers/bin/k40_mem_stage; for pass in 1 2 3 4; do ls /dev/misc >/dev/null; sleep 1; done; echo K40-BATCH-RELOAD-END > /dev/dprintf"


def binding(suite):
    return dict(
        package_sha256=build.sha(build.PUBLIC),
        plan_sha256=suite["plan_sha256"],
        job_sha256=suite["job_sha256"],
        A7_job_sha256=suite["plan"]["A7_job_sha256"],
        guest_artifacts=suite["guest_artifacts"],
        A7_artifacts=suite["A7"]["guest_artifacts"],
        kernel_sha256=suite["kernel_sha256"],
    )


def load_counts(serial):
    return dict(
        preflight=serial.count("k40_mem_preflight: LOAD"),
        memory_client=serial.count("k40_mem_stage: BATCH1_MEMORY"),
        memory_owner=serial.count("k40_mem: OWNER_LOAD"),
        A7_client=serial.count("k40_stage: A7_ARM_ONLY_POST_WRITE"),
        A7_owner=serial.count("k40_a7: OWNER_LOAD"),
        identity=serial.count("k40_stage: B5_IDENTITY_READ_ONLY"),
    )


def verdict(folder, suite):
    serial = (folder / "serial.log").read_text(errors="replace")
    a7folder = folder / "a7"
    if (
        not evidence.preflight(folder, serial, True)
        or not evidence.a7_nocard(a7folder, serial, suite["A7"])
        or not evidence.memory_nocard(folder, serial)
    ):
        raise ValueError("incomplete no-card phase evidence")
    output = (folder / "job-output.txt").read_text()
    evidence.installed(
        output, suite["guest_artifacts"], tuple(suite["guest_artifacts"])
    )
    if (
        "BATCH-JOB-END" not in output
        or (folder / "job.exit").read_text().strip() != "0"
    ):
        raise ValueError("combined installer did not finish")
    if not all(
        marker in output
        for marker in ("MEM-NODE k40_mem_preflight", "MEM-NODE k40_mem_stage")
    ):
        raise ValueError("expected character nodes not observed")
    allowed = {
        "k40_identity_probe",
        "k40_a7_stage",
        "k40_mem_preflight",
        "k40_mem_stage",
    }
    discovered = re.findall(r'driver "([^"\n]+)" (?:added|removed)', serial)
    relevant = [name for name in discovered if "k40" in name or ".partial" in name]
    if not relevant or set(relevant) - allowed or not allowed.issubset(set(relevant)):
        raise ValueError("driver discovery from wrong/missing final name")
    paths = re.findall(r"(?:loaded driver|reload driver) [^\r\n]*", serial)
    if any("partial" in line or "staging" in line for line in paths):
        raise ValueError("driver loaded from staging/partial path")
    counts = load_counts(serial)
    if (
        counts["memory_owner"] != 1
        or counts["A7_owner"] != 1
        or counts["memory_client"] < 2
        or counts["A7_client"] < 2
        or counts["identity"] < 2
    ):
        raise ValueError("resident owner reconstructed or reload not exercised")
    observations = re.findall(
        r"^k40_mem: CLIENT_LOAD n=(\d+) state=(\d+)\r?$", serial, re.M
    )
    if len(observations) != counts["memory_client"] or any(
        int(n) != i + 1 for i, (n, state) in enumerate(observations)
    ):
        raise ValueError("memory client load counter differs")
    if observations[0][1] != "0" or not any(
        state == "4" for n, state in observations[1:]
    ):
        raise ValueError("memory Failed latch not retained through reload")
    if (
        serial.count("k40_mem: PREPARE_CALL n=1") != 1
        or serial.count("k40_a7: PREPARE_CALL a=0x1 b=0x0") != 1
    ):
        raise ValueError("driver prepared again on reload")
    if "K40-BATCH-RELOAD-END" not in serial:
        raise ValueError("reload sequence incomplete")
    return counts


def validate(suite):
    record = json.loads(OUTPUT.read_text())
    if (
        OUTPUT.read_text() != build.dump(record)
        or record["binding"] != binding(suite)
        or record["status"] != "PASS_CARDLESS_NO_CARD"
    ):
        raise ValueError("rehearsal does not match current package")
    folder = ROOT / record["folder"]
    for name, digest in record["capture_sha256"].items():
        if build.sha(folder / name) != digest:
            raise ValueError("rehearsal capture changed: " + name)
    launch = json.loads((folder / "launch.json").read_text())
    if launch["scope"] != "CARDLESS_KVM" or any(
        "vfio" in value or "host=" in value for value in launch["args"]
    ):
        raise ValueError("rehearsal not cardless")
    if (folder / "job.sh").read_text() != job(
        launch["port"], launch["a7_port"], suite
    ) or (folder / "a7/job.sh").read_text() != a7_job(
        launch["a7_port"], suite["A7"]["guest_artifacts"]
    ):
        raise ValueError("rehearsed job bytes differ")
    if verdict(folder, suite) != record["load_counts"]:
        raise ValueError("rehearsal driver load count differs")
    return record


def stop_owned(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def forbid_private_keys(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(os.fspath(args[0])))
        if path.name in ("host-key.pem", "nonce.bin"):
            raise RuntimeError("cardless audit forbids private signing inputs")


def run():
    sys.addaudithook(forbid_private_keys)
    suite = prerequisites(cardless=True)
    with guest_lock(d0_run.BASE.parent):
        folder, captures = prepare(suite, True)
        args = arguments(folder, captures, suite, True)
        process = None
        status = "FAILED_CARDLESS"
        error = ""
        start = time.monotonic()
        try:
            with a7run.exchange(folder / "a7", captures / "a7", suite["A7"]) as (
                a7port,
                a7ready,
            ), exchange(folder, captures, suite, a7port) as (port, ready):
                save(captures / "job.sh", (folder / "job.sh").read_bytes())
                save(captures / "a7/job.sh", (folder / "a7/job.sh").read_bytes())
                save(
                    captures / "launch.json",
                    build.dump(
                        dict(
                            scope="CARDLESS_KVM",
                            suite=suite,
                            args=args,
                            port=port,
                            a7_port=a7port,
                            binding=binding(suite),
                            timeout_seconds=600,
                            source_commit=subprocess.check_output(
                                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                            ).strip(),
                        )
                    ),
                )
                if prerequisites(cardless=True) != suite:
                    raise ValueError("rehearsal inputs changed")
                with (captures / "qemu.log").open("xb") as log:
                    process = subprocess.Popen(args, stdout=log, stderr=log)
                with ExitStack() as lifetime:
                    lifetime.enter_context(
                        deadline(process, 600, captures / "watchdog.txt")
                    )
                    lifetime.callback(stop_owned, process)

                    def alive():
                        if process.poll() is not None:
                            raise ValueError("cardless guest exited before evidence")

                    broker = Broker(
                        folder, captures, captures / "a7", suite, ready, True
                    )
                    drive(
                        broker,
                        a7ready,
                        folder / "monitor.sock",
                        port,
                        captures / "serial.log",
                        alive,
                    )
                    raw = pci.snapshot(folder / "qmp")
                    save(captures / "pci-cardless.json", build.dump(raw))
                    card_run.hmp(folder / "monitor.sock", "type", RELOAD)
                    end = time.monotonic() + 45
                    while time.monotonic() < end:
                        alive()
                        serial = (captures / "serial.log").read_text(errors="replace")
                        if re.search(
                            r"^\s*(?:PANIC:|KERNEL PANIC\b)", serial, re.I | re.M
                        ):
                            raise ValueError("guest panic during reload")
                        if "K40-BATCH-RELOAD-END" in serial:
                            break
                        time.sleep(0.25)
                    else:
                        raise ValueError("cardless reload deadline")
                if (captures / "watchdog.txt").exists():
                    raise ValueError("cardless watchdog stop; no retry")
                save(captures / "a7/serial.log", (captures / "serial.log").read_bytes())
                counts = verdict(captures, suite)
                status = "PASS_CARDLESS_NO_CARD"
        except BaseException as exc:
            error = str(exc)
            raise
        finally:
            stop_owned(process)
            save(
                captures / "result.json",
                build.dump(
                    dict(
                        status=status,
                        error=error,
                        elapsed_seconds=round(time.monotonic() - start, 2),
                        scope="CARDLESS_KVM",
                        host_device_assigned=False,
                        keys_read=False,
                        grants_issued=False,
                        hardware_evidence=False,
                        S1_complete=False,
                    )
                ),
            )
            save(
                captures / "README.md",
                f"# Combined cardless rehearsal\n\n{status}. {error}\n\nThe exact combined installer and binaries run without VFIO, grant keys or\ngrants. Expected outcomes: G0 and memory open return B_ENTRY_NOT_FOUND\n(0x80006003); original A7 open returns its unchanged B_ERROR (0xffffffff).\nAll artifacts require size/SHA-256 and same-inode moves from unwatched staging.\nFinal-name-only driver loads and resident Failed state through reload are checked.\nThis is Haiku installation/lifetime evidence only, not K40c/UC/VRAM/MMU evidence.\n",
            )
            print(captures, flush=True)
        files = sorted(
            p.relative_to(captures).as_posix()
            for p in captures.rglob("*")
            if p.is_file()
        )
        record = dict(
            status=status,
            folder=captures.relative_to(ROOT).as_posix(),
            binding=binding(suite),
            load_counts=counts,
            capture_sha256={name: build.sha(captures / name) for name in files},
            reload_command=RELOAD,
            scope="CARDLESS_ONLY install/open/no-card/reload; no physical mapping, DMA or BAR1 proof",
        )
        OUTPUT.write_text(build.dump(record))
        validate(suite)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.run:
        run()
    else:
        validate(build.validate_public(require_rehearsal=False))
        print("Exact combined rehearsal binding passes; no guest started.")


if __name__ == "__main__":
    main()
