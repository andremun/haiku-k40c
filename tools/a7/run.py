#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Closed, single-use A7 write stage. Run ONLY after a reviewed per-run yes.

Default/--check checks the package only; --host-check also requires live R5.
No extra QEMU arguments, keys, firmware, devices or bytecode are accepted.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.a7 import build
from tools.a7.guest_job import job
import card_run
from tools.haiku import d0_run
from tools.haiku.d0_kernel_log import KernelLog, FILTER_PATTERN
from tools.haiku.d0_monitor import snapshot
from tools.haiku.d0_topology import parse as parse_topology
from tools.haiku.vm_guard import guest_lock
from tools.observer.task_stream import TaskStream
from tools.observer.supervise import observed_child
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

save = d0_run.save
save_json = d0_run.save_json
STAGE = "A7_ARM_ONLY_POST_WRITE"
SELECTED = re.compile(FILTER_PATTERN, re.I)
COMMAND = Path("/sys/bus/pci/devices") / card_run.ALLOWED_BDF / "config"


class StrictLog(KernelLog):
    def poll(self):
        previous = self.last
        data = super().poll()
        if any(
            SELECTED.search(line)
            for line in data[len(previous) :].decode(errors="replace").splitlines()
        ):
            raise RuntimeError("new R5 selected-class line; stop without retry")
        return data


def command_register(path=COMMAND):
    # PCI.h:240,686: command offset 4; bit 2 is PCI bus master enable.
    with path.open("rb", buffering=0) as source:
        source.seek(4)
        data = source.read(2)
    if len(data) != 2:
        raise RuntimeError("host PCI command unreadable")
    return int.from_bytes(data, "little")


def stopped_command():
    end = time.monotonic() + 2
    while True:
        value = command_register()
        if not value & 4:
            return value
        if time.monotonic() >= end:
            raise RuntimeError(
                "PCI bus mastering remains enabled after owned guest exit; STOP"
            )
        time.sleep(0.05)


@contextmanager
def exchange(folder, evidence, suite):
    lock = threading.Lock()
    ready = threading.Event()
    downloads = {
        name: folder / name
        for name in ("identity", "owner", "client", "helper", "job.sh")
    }
    limits = {
        "environment.txt": 65536,
        "kernel_x86_64": 64 * 1024 * 1024,
        "request.bin": 128,
        "job.exit": 16,
        "job-output.txt": 65536,
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/grant.bin":
                path = evidence / "grant.bin" if ready.is_set() else None
            else:
                path = downloads.get(self.path[1:])
            if path is None:
                self.send_error(404)
                return
            data = path.read_bytes()
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
            if name not in limits or not 0 < size <= limits[name]:
                self.send_error(413)
                return
            if name == "request.bin" and size != 128:
                self.send_error(400)
                return
            self.connection.settimeout(20)
            data = self.rfile.read(size)
            if len(data) != size:
                self.send_error(400)
                return
            if name == "kernel_x86_64":
                if hashlib.sha256(data).hexdigest() != suite["kernel_sha256"]:
                    self.send_error(409)
                    return
                name = "kernel.sha256"
                data = (suite["kernel_sha256"] + "\n").encode()
            with lock:
                path = evidence / name
                if path.exists():
                    code = 201 if path.read_bytes() == data else 409
                else:
                    save(path, data)
                    code = 201
            self.send_response(code)
            self.end_headers()

        def log_message(self, fmt, *args):
            with lock, (evidence / "http.log").open("a") as out:
                out.write(fmt % args + "\n")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    save(folder / "job.sh", job(server.server_address[1], suite["guest_artifacts"]))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], ready
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request_fields(request, suite, serial):
    if len(request) != 128 or request[:16] != b"K40A7REQ\x01" + bytes(7):
        raise RuntimeError("A7 request framing")
    if (
        request[16:48].hex() != suite["package_nonce_hex"]
        or any(request[72:112])
        or not any(request[112:128])
    ):
        raise RuntimeError("A7 request identity/reserved fields")
    token, gpa, size = (
        int.from_bytes(request[start : start + 8], "little") for start in (48, 56, 64)
    )
    if not token or not gpa or gpa % 4096 or size != 4096 or gpa + size > 2**32:
        raise RuntimeError("A7 request extent")
    matches = re.findall(
        r"^k40_a7: PREPARED a=0x([0-9a-f]+) b=0x([0-9a-f]+)\r?$", serial, re.M
    )
    if len(matches) != 1 or tuple(int(x, 16) for x in matches[0]) != (token, gpa):
        raise RuntimeError("A7 owner/request mismatch")
    return token, gpa, size


def sign(request, digest, suite):
    public, _ = build.key_inputs()
    if public.hex() != suite["public_key_hex"]:
        raise RuntimeError("signing key differs")
    key = serialization.load_pem_private_key(
        (build.PACKAGE / "host-key.pem").read_bytes(), password=None
    )
    if not isinstance(key, Ed25519PrivateKey):
        raise RuntimeError("signing key type")
    message = bytearray(request)
    message[:8] = b"K40A7ARM"
    message[72:80] = request[56:64]
    message[80:112] = digest
    return bytes(message) + key.sign(bytes(message))


def serial_valid(serial, final=False, request=None, suite=None):
    card_run.verdict(serial, b"0")
    if re.search(r"^k40_a7: FAIL\b", serial, re.M):
        raise RuntimeError("native A7 failure; stop without retry")
    tags = {
        line.partition("k40_stage: ")[2].strip()
        for line in serial.splitlines()
        if "k40_stage: " in line
    }
    if tags - {"B5_IDENTITY_READ_ONLY", STAGE}:
        raise RuntimeError("unexpected stage role")
    if not final:
        return
    markers = (
        "IDENTITY",
        "PCI_COMMAND",
        "ARM_BEFORE",
        "POST_RESULT",
        "ARM_READBACK",
        "ARM_AFTER",
        "TIMER",
        "VRAM_BYTES",
        "SCRATCH_PASS",
        "PASS ARM_ONLY_POST",
        "RETAINED",
    )
    positions = []
    values = {}
    for marker in markers:
        matches = list(
            re.finditer(
                r"^k40_a7: "
                + re.escape(marker)
                + r" a=0x([0-9a-f]+) b=0x([0-9a-f]+)\r?$",
                serial,
                re.M,
            )
        )
        if len(matches) != 1:
            raise RuntimeError("missing/repeated A7 evidence: " + marker)
        positions.append(matches[0].start())
        values[marker] = tuple(int(x, 16) for x in matches[0].groups())
    # PCI command is logged immediately before native identity.
    order = [positions[1], positions[0], *positions[2:]]
    if order != sorted(order) or "K40-A7-END" not in serial:
        raise RuntimeError("A7 evidence order")
    post = re.search(r"^k40_a7: POST_RESULT a=0x([0-9a-f]+)", serial, re.M)
    if int(post[1], 16):
        raise RuntimeError("POST failed")
    if values["IDENTITY"] != (0xF1240A1, 0) or not values["PCI_COMMAND"][0] & 2:
        raise RuntimeError("native identity/PCI memory decode")
    if values["TIMER"][1] <= values["TIMER"][0] or values["SCRATCH_PASS"] != (
        0x40000,
        4096,
    ):
        raise RuntimeError("readiness evidence differs")
    if (
        values["ARM_BEFORE"] != values["ARM_AFTER"]
        or values["ARM_BEFORE"][1] != values["ARM_BEFORE"][0] >> 8
    ):
        raise RuntimeError("armed addresses differ")
    if request is not None:
        token, gpa, _ = request_fields(request, suite, serial)
        if values["ARM_BEFORE"] != (gpa, gpa >> 8) or values["RETAINED"] != (token, 2):
            raise RuntimeError("wrong reference or retention")
        total = suite["physical_vram_bytes"]
        if values["VRAM_BYTES"] != (total, 0) or values["PASS ARM_ONLY_POST"] != (
            total,
            2,
        ):
            raise RuntimeError("wrong memory size/arming count")


def monitor(child, folder, evidence, port, ready, host, kernel, suite):
    def proof_record(value):
        with (evidence / "task-proofs.jsonl").open("a") as out:
            out.write(json.dumps(value, sort_keys=True) + "\n")

    stream = TaskStream(
        folder.name,
        child.process.pid,
        int(host["group"]),
        target=str(Path(suite["artifacts"]["qemu"]["path"]).resolve()),
        sink=proof_record,
    )
    old = b""
    pending = b""
    granted = False
    witness = None
    launched = False
    launch_at = None
    terminal_at = None

    def drain():
        nonlocal old, pending
        current = child.trace.read_bytes() if child.trace.exists() else b""
        if len(current) > 16 * 1024 * 1024 or not current.startswith(old):
            raise RuntimeError("observer log changed/oversized")
        pending += current[len(old) :]
        old = current
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            if not stream.feed((line + b"\n").decode("ascii")):
                raise RuntimeError("A7 observer: " + str(stream.error))
        if witness is not None and not stream.current(witness):
            raise RuntimeError("armed map witness invalidated; stop")

    start = time.monotonic()
    while time.monotonic() - start < 570:
        child.check()
        kernel.poll()
        drain()
        for name in ("serial.log", "qemu.log"):
            path = evidence / name
            if path.exists() and path.stat().st_size > 16 * 1024 * 1024:
                raise RuntimeError("guest log limit")
        serial = (
            (evidence / "serial.log").read_text(errors="replace")
            if (evidence / "serial.log").exists()
            else ""
        )
        # Panic and B5 failure are checked before the handshake is complete too.
        card_run.verdict(serial, None)
        if re.search(r"^k40_a7: FAIL\b", serial, re.M):
            raise RuntimeError("native A7 failure")
        exited = evidence / "job.exit"
        if exited.exists() and exited.read_bytes().strip() != b"0":
            raise RuntimeError("A7 guest job failed")
        request = evidence / "request.bin"
        if not granted and request.exists() and not pending:
            serial_valid(serial)
            if not (evidence / "kernel.sha256").exists():
                raise RuntimeError("guest kernel handshake missing")
            raw = request.read_bytes()
            token, gpa, size = request_fields(raw, suite, serial)
            topology = snapshot(folder / "qmp")
            realized = parse_topology(**topology, physical=True)
            if not realized.contains(gpa, size):
                raise RuntimeError("armed page not in realized system RAM")
            drain()
            if pending:
                raise RuntimeError("partial observer record at grant cutoff")
            witness = stream.coverage(gpa=gpa, iova=gpa, size=size)
            if witness is None:
                raise RuntimeError("fresh armed extent map coverage missing")
            for name, data in topology.items():
                save(evidence / (name + ".txt"), data)
            cutoff = dict(
                token=token,
                gpa=gpa,
                iova=gpa,
                bytes=size,
                trace_prefix_bytes=len(old),
                trace_prefix_sha256=hashlib.sha256(old).hexdigest(),
                container=witness.mapping.identity.container,
                generation=witness.mapping.identity.generation,
                cutoff=witness.mapping.cutoff,
                group=witness.group,
                device_fd=witness.device_fd,
                mapped_segments=[vars(region) for region in witness.mapping.regions],
                claim="same-run structural API coverage; IOVA=GPA INFERRED; no payload visibility or coherency claim",
            )
            encoded = build.dump(cutoff)
            save(evidence / "cutoff.json", encoded)
            grant = sign(raw, hashlib.sha256(encoded.encode()).digest(), suite)
            # Signer never exports the secret. Re-check live inputs before serving.
            child.check()
            kernel.poll()
            drain()
            if pending:
                raise RuntimeError("partial observer record before grant release")
            save(evidence / "grant.bin", grant)
            granted = True
            ready.set()
        if granted and exited.exists():
            serial_valid(
                (evidence / "serial.log").read_text(errors="replace"),
                True,
                (evidence / "request.bin").read_bytes(),
                suite,
            )
            return stream, old, pending
        now = time.monotonic()
        if launch_at is None and (
            "first login script" in serial
            or 'Volume::InitialVerify(): volume at "/boot/home/config" is consistent'
            in serial
        ):
            launch_at = now + 12
        if launch_at is not None and terminal_at is None and now >= launch_at:
            card_run.hmp(folder / "monitor.sock", "cmd", "sendkey alt-meta_l-t")
            terminal_at = now + 8
        if terminal_at is not None and not launched and now >= terminal_at:
            card_run.hmp(
                folder / "monitor.sock",
                "type",
                f"curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/a7-job.sh; sh /tmp/a7-job.sh",
            )
            launched = True
        time.sleep(0.25)
    raise RuntimeError("A7 guest deadline; stop without retry")


def prerequisites():
    if os.geteuid() == 0:
        raise ValueError("root execution forbidden")
    if os.environ.get("GPU_BDF", card_run.ALLOWED_BDF) != card_run.ALLOWED_BDF:
        raise ValueError("only 04:00.0 authorized")
    suite = build.validate()
    if (build.PACKAGE / "consumed.json").exists():
        raise ValueError("single-use A7 package already consumed")
    return suite


def run():
    suite = prerequisites()
    d0_run.prerequisites()
    host = card_run.preflight(card_run.ALLOWED_BDF)
    with guest_lock(d0_run.BASE.parent), StrictLog() as kernel:
        evidence = (
            ROOT
            / "results"
            / (datetime.now().strftime("%Y%m%d") + "-a7-" + uuid.uuid4().hex[:8])
        )
        evidence.mkdir(mode=0o700, exist_ok=False)
        folder = ROOT / "build/a7" / uuid.uuid4().hex[:8]
        folder.mkdir(mode=0o700, parents=True, exist_ok=False)
        if (
            max(len(os.fsencode(folder / name)) for name in ("qmp", "monitor.sock"))
            > 107
        ):
            raise ValueError("monitor path too long")
        for role in ("identity", "owner", "client", "helper"):
            shutil.copyfile(suite["artifacts"][role]["path"], folder / role)
            if build.sha(folder / role) != suite["artifacts"][role]["sha256"]:
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
        args = card_run.qemu_args(d0_run.BASE, folder, evidence, card_run.ALLOWED_BDF)
        args[0] = suite["artifacts"]["qemu"]["path"]
        args[args.index("-name") + 1] = "k40-a7-arm-only-post"
        args += ["-qmp", "unix:" + str(folder / "qmp") + ",server,nowait"]
        save(evidence / "kernel-before.log", kernel.before)
        save_json(
            evidence / "launch.json",
            dict(
                stage=STAGE,
                args=args,
                suite=suite,
                host=host,
                host_pci_command_before=command_register(),
                timeout_seconds=600,
                kernel_stream=kernel.metadata(),
                source_commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
            ),
        )
        status = "failed"
        error = ""
        start = time.monotonic()
        try:
            with exchange(folder, evidence, suite) as (port, ready), (
                evidence / "qemu.log"
            ).open("xb") as log:
                if (
                    card_run.preflight(card_run.ALLOWED_BDF) != host
                    or prerequisites() != suite
                ):
                    raise ValueError("launch inputs changed")
                kernel.poll()
                save_json(
                    build.PACKAGE / "consumed.json",
                    dict(
                        evidence=str(evidence), package_sha256=build.sha(build.PUBLIC)
                    ),
                )
                with observed_child(
                    suite["artifacts"]["observer"]["path"],
                    args,
                    evidence / "trace.log",
                    log,
                    600,
                    evidence / "watchdog.txt",
                    ["/dev/vfio/vfio", host["vfio"]],
                ) as child:
                    save_json(
                        evidence / "processes.json",
                        dict(
                            qemu_pid=child.process.pid,
                            tracer_pid=child.tracer,
                            kernel_reader_pid=kernel.pid,
                        ),
                    )
                    stream, prefix, pending = monitor(
                        child, folder, evidence, port, ready, host, kernel, suite
                    )
                d0_run.finish_trace(evidence / "trace.log", stream, prefix, pending)
                save_json(
                    evidence / "teardown.json",
                    dict(
                        host_pci_command_after=stopped_command(),
                        bus_master_enable=False,
                        claim="owned QEMU/tracer exited; read-only host PCI command bit 2 clear; no manual reset",
                    ),
                )
                save(evidence / "kernel-after.log", kernel.poll())
                status = "pass"
        except BaseException as exc:
            error = str(exc)
            raise
        finally:
            if not (evidence / "teardown.json").exists():
                try:
                    save_json(
                        evidence / "teardown.json",
                        dict(
                            host_pci_command_after=stopped_command(),
                            bus_master_enable=False,
                        ),
                    )
                except (OSError, RuntimeError) as exc:
                    save(evidence / "teardown-unconfirmed.txt", str(exc) + "\n")
            if not (evidence / "kernel-after.log").exists():
                try:
                    save(evidence / "kernel-after.log", kernel.capture())
                except (OSError, RuntimeError):
                    save(evidence / "kernel-after-unavailable.txt", "capture failed\n")
            save_json(
                evidence / "result.json",
                dict(
                    status=status,
                    error=error,
                    stage=STAGE,
                    elapsed_seconds=round(time.monotonic() - start, 2),
                    dma_publication=False,
                    payload_visibility=False,
                    S1_complete=False,
                    kernel_scope="R5 selected classes only; any new selected-class line stops stage",
                ),
            )
            print(evidence, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--host-check", action="store_true")
    group.add_argument(
        "--run-approved-A7-once",
        action="store_true",
        help="requires prior explicit yes for this exact reviewed package",
    )
    args = parser.parse_args()
    if args.run_approved_A7_once:
        run()
    else:
        prerequisites()
        if args.host_check:
            d0_run.prerequisites()
            card_run.preflight(card_run.ALLOWED_BDF)
            with StrictLog() as kernel:
                kernel.poll()
        print(
            "A7 checks pass; no guest started; no run approval supplied by this check"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
