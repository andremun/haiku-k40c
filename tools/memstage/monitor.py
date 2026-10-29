# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Fixed ordered broker. Cardless mode has no signing path or VFIO observer."""
import hashlib
import json
from pathlib import Path
import re
import time

from tools.a7 import run as a7run
from tools.memstage import build, evidence, pci
from tools.haiku import card_run, d0_monitor, d0_topology
from tools.observer.task_stream import TaskStream
from tools.memstage.exchange import save


def exit_status(path):
    if not path.exists():
        return None
    data = path.read_bytes()
    if not data.endswith(b"\n"):
        return None
    if not re.fullmatch(rb"[0-9]{1,3}\n", data):
        raise ValueError("malformed job exit")
    return int(data.strip())


class Broker:
    def __init__(
        self,
        folder,
        captures,
        a7captures,
        suite,
        ready,
        cardless,
        child=None,
        host=None,
        kernel=None,
    ):
        self.folder = folder
        self.captures = captures
        self.a7captures = a7captures
        self.suite = suite
        self.ready = ready
        self.cardless = cardless
        self.child = child
        self.host = host
        self.kernel = kernel
        self.old = b""
        self.pending = b""
        self.witness = None
        self.g0 = False
        self.armed = False
        self.a7done = False
        self.memoryGranted = False
        self.memoryDone = False
        self.stream = None
        if not cardless:
            if child is None or host is None or kernel is None:
                raise ValueError("physical supervision missing")

            def proof(value):
                with (captures / "task-proofs.jsonl").open("a") as out:
                    out.write(json.dumps(value, sort_keys=True) + "\n")

            self.stream = TaskStream(
                folder.name,
                child.process.pid,
                int(host["group"]),
                target=str(Path(suite["qemu"]["path"]).resolve()),
                sink=proof,
            )

    def drain(self):
        if self.cardless:
            return
        current = self.child.trace.read_bytes() if self.child.trace.exists() else b""
        if len(current) > 16 * 1024 * 1024 or not current.startswith(self.old):
            raise ValueError("observer history changed/oversized")
        self.pending += current[len(self.old) :]
        self.old = current
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            if not self.stream.feed((line + b"\n").decode("ascii")):
                raise ValueError("batch observer: " + str(self.stream.error))
        if self.witness is not None and not self.stream.current(self.witness):
            raise ValueError("fresh A7 armed extent invalidated")

    def live(self):
        if self.cardless:
            return
        self.child.check()
        self.kernel.poll()
        self.drain()

    def release(self, role, raw, digest, target, ready):
        if self.cardless:
            raise ValueError("cardless signing forbidden")
        from tools.memstage.sign import grant

        self.live()
        if self.pending:
            raise ValueError("partial observer record before grant")
        data = grant(role, raw, digest, self.suite)
        self.live()
        if self.pending:
            raise ValueError("partial observer record before serving grant")
        save(target, data)
        ready.set()

    def arm(self, serial):
        path = self.a7captures / "request.bin"
        if (
            self.armed
            or not path.exists()
            or path.stat().st_size != 128
            or self.pending
        ):
            return
        kernel = self.a7captures / "kernel.sha256"
        if not kernel.exists() or kernel.stat().st_size != 65:
            return
        if kernel.read_text().strip() != self.suite["kernel_sha256"]:
            raise ValueError("guest kernel handshake differs")
        a7run.serial_valid(serial)
        raw = path.read_bytes()
        token, gpa, size = a7run.request_fields(raw, self.suite["A7"], serial)
        topology = d0_monitor.snapshot(self.folder / "qmp")
        realized = d0_topology.parse(**topology, physical=True)
        if not realized.contains(gpa, size):
            raise ValueError("arm extent is not realized guest RAM")
        self.drain()
        if self.pending:
            return
        witness = self.stream.coverage(gpa=gpa, iova=gpa, size=size)
        if witness is None:
            raise ValueError("same-run arm mapping coverage missing")
        self.witness = witness
        for name, data in topology.items():
            save(self.a7captures / (name + ".txt"), data)
        cutoff = dict(
            token=token,
            gpa=gpa,
            iova=gpa,
            bytes=size,
            trace_prefix_bytes=len(self.old),
            trace_prefix_sha256=hashlib.sha256(self.old).hexdigest(),
            container=witness.mapping.identity.container,
            generation=witness.mapping.identity.generation,
            cutoff=witness.mapping.cutoff,
            group=witness.group,
            device_fd=witness.device_fd,
            mapped_segments=[vars(region) for region in witness.mapping.regions],
            claim="same-run structural coverage; IOVA=GPA INFERRED; no payload/visibility claim",
        )
        encoded = build.dump(cutoff)
        save(self.a7captures / "cutoff.json", encoded)
        self.release(
            "A7",
            raw,
            hashlib.sha256(encoded.encode()).digest(),
            self.a7captures / "grant.bin",
            self.a7ready,
        )
        self.armed = True

    def memory_grant(self, serial):
        if self.memoryGranted or not self.ready["request.bin"].is_set():
            return
        if not self.a7done or not self.armed or self.witness is None:
            raise ValueError("memory request before A7 attestation")
        raw = (self.captures / "request.bin").read_bytes()
        rawpci = pci.snapshot(self.folder / "qmp")
        resources = pci.resources(rawpci)
        fields = evidence.request_fields(raw, self.suite, serial, resources)
        self.live()
        if self.pending:
            return
        proof = dict(
            stage=build.STAGE,
            plan_sha256=self.suite["plan_sha256"],
            memory_request_sha256=hashlib.sha256(raw).hexdigest(),
            a7_request_sha256=build.sha(self.a7captures / "request.bin"),
            a7_grant_sha256=build.sha(self.a7captures / "grant.bin"),
            cutoff_sha256=build.sha(self.a7captures / "cutoff.json"),
            a7_serial_prefix_sha256=self.a7_serial,
            pci=resources,
            pci_raw_sha256=hashlib.sha256(build.dump(rawpci).encode()).hexdigest(),
            trace_prefix_bytes=len(self.old),
            trace_prefix_sha256=hashlib.sha256(self.old).hexdigest(),
            mapping_generation=self.witness.mapping.identity.generation,
            kernel_sha256=self.suite["kernel_sha256"],
            kernel_selected_sha256=hashlib.sha256(self.kernel.poll()).hexdigest(),
            native=fields,
        )
        save(self.captures / "pci-before.json", build.dump(rawpci))
        save(self.captures / "memory-attestation.json", build.dump(proof))
        self.release(
            "memory",
            raw,
            hashlib.sha256(build.dump(proof).encode()).digest(),
            self.captures / "grant.bin",
            self.ready["grant.bin"],
        )
        self.memoryGranted = True

    def step(self, serial, a7ready):
        self.a7ready = a7ready
        self.live()
        for root in (self.captures, self.a7captures):
            for name in ("http.log", "serial.log", "qemu.log", "job-output.txt"):
                path = root / name
                if path.exists() and path.stat().st_size > 16 * 1024 * 1024:
                    raise ValueError("batch log bound")
        if re.search(r"^\s*(?:PANIC:|KERNEL PANIC\b)", serial, re.I | re.M):
            raise ValueError("guest panic; stop without retry")
        if not self.cardless:
            card_run.verdict(serial, None)
            if re.search(r"^k40_(?:a7|mem): FAIL\b", serial, re.M):
                raise ValueError("native phase failure; stop without retry")
        elif any(
            (root / name).exists()
            for root in (self.captures, self.a7captures)
            for name in ("request.bin", "grant.bin")
        ):
            raise ValueError("cardless request/grant forbidden")
        if self.ready["preflight-install.txt"].is_set():
            if evidence.preflight(self.captures, serial, self.cardless):
                evidence.installed(
                    (self.captures / "preflight-install.txt").read_text(),
                    self.suite["guest_artifacts"],
                    ("preflight", "preflight_helper"),
                )
                if not self.g0:
                    self.g0 = True
                    self.ready["advance-a7"].set()
        if self.g0 and not self.cardless:
            self.arm(serial)
        child_exit = exit_status(self.a7captures / "job.exit")
        if (
            self.g0
            and not self.a7done
            and child_exit is not None
            and self.ready["child-result.txt"].is_set()
        ):
            if exit_status(self.captures / "child-result.txt") != child_exit:
                raise ValueError("outer/A7 child exit mismatch")
            if self.cardless:
                complete = evidence.a7_nocard(self.a7captures, serial, self.suite["A7"])
            else:
                if child_exit != 0:
                    raise ValueError("A7 child job failed; stop without retry")
                if not self.armed:
                    raise ValueError("A7 child ended without same-run grant")
                a7run.serial_valid(
                    serial,
                    True,
                    (self.a7captures / "request.bin").read_bytes(),
                    self.suite["A7"],
                )
                complete = True
            if complete:
                self.a7done = True
                self.a7_serial = hashlib.sha256(serial.encode()).hexdigest()
                save(self.captures / "a7-serial-prefix.txt", serial)
                self.ready["advance-memory"].set()
        if self.ready["memory-install.txt"].is_set():
            if not self.a7done:
                raise ValueError("memory install before A7 gate")
            evidence.installed(
                (self.captures / "memory-install.txt").read_text(),
                self.suite["guest_artifacts"],
                tuple(self.suite["guest_artifacts"]),
            )
            if not self.cardless:
                self.memory_grant(serial)
        if self.ready["memory-exit.txt"].is_set() and not self.memoryDone:
            if self.cardless:
                complete = evidence.memory_nocard(self.captures, serial)
            else:
                if exit_status(self.captures / "memory-exit.txt") != 0:
                    raise ValueError("memory stream failed; stop without retry")
                if not self.memoryGranted:
                    raise ValueError("memory ended without grant")
                result = evidence.memory_final(
                    serial, self.suite, (self.captures / "request.bin").read_bytes()
                )
                after = pci.snapshot(self.folder / "qmp")
                if (
                    pci.resources(after)
                    != json.loads(
                        (self.captures / "memory-attestation.json").read_text()
                    )["pci"]
                ):
                    raise ValueError("BAR resources changed after memory phase")
                save(self.captures / "pci-after.json", build.dump(after))
                save(self.captures / "memory-observations.json", build.dump(result))
                complete = True
            if complete:
                self.memoryDone = True
                self.ready["finish-ok"].set()
        if self.ready["job.exit"].is_set():
            if exit_status(self.captures / "job.exit") != 0:
                raise ValueError("combined guest job failed")
            if not self.memoryDone:
                raise ValueError("combined job ended before memory gate")
            return True
        return False


def drive(broker, a7ready, monitor, port, serial_path, alive):
    start = time.monotonic()
    launch_at = None
    terminal_at = None
    launched = False
    while time.monotonic() - start < 570:
        alive()
        serial = serial_path.read_text(errors="replace") if serial_path.exists() else ""
        if not broker.cardless:
            broker.live()
            if serial:
                broker.kernel.close_start_window()
        if broker.step(serial, a7ready):
            return
        now = time.monotonic()
        if launch_at is None and (
            "first login script" in serial
            or 'Volume::InitialVerify(): volume at "/boot/home/config" is consistent'
            in serial
        ):
            launch_at = now + 12
        if launch_at is not None and terminal_at is None and now >= launch_at:
            card_run.hmp(monitor, "cmd", "sendkey alt-meta_l-t")
            terminal_at = now + 8
        if terminal_at is not None and not launched and now >= terminal_at:
            card_run.hmp(
                monitor,
                "type",
                f"curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/batch-job.sh; sh /tmp/batch-job.sh",
            )
            launched = True
        time.sleep(0.25)
    raise ValueError("combined guest deadline; stop without retry")
