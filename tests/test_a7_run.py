#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic A7 launcher fixtures. Never starts a guest or reads a private key."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.a7 import run
from test_observer_binding import LINES

ROOT = Path(__file__).resolve().parents[1]
TOPO = ROOT / "results/20261027-d0-topology-fixture"
SERIAL = """K40-B5-BEGIN
k40_stage: B5_IDENTITY_READ_ONLY
k40_os: PCI command 0x0007
k40_os: GPU identity 0x0f1240a1; no bring-up or DMA
k40_os: PASS B5 identity reads only
K40-B5-END
k40_stage: A7_ARM_ONLY_POST_WRITE
k40_a7: PREPARED a=0x7 b=0x100000
"""
FINAL = (
    "".join(
        f"k40_a7: {name} a=0x{a:x} b=0x{b:x}\n"
        for name, a, b in (
            ("PCI_COMMAND", 7, 0),
            ("IDENTITY", 0xF1240A1, 0),
            ("ARM_BEFORE", 0x100000, 0x1000),
            ("POST_RESULT", 0, 0),
            ("ARM_READBACK", 0xDEADBEEF, 0),
            ("ARM_AFTER", 0x100000, 0x1000),
            ("TIMER", 1, 2),
            ("VRAM_BYTES", 11520 * 1024**2, 0),
            ("SCRATCH_PASS", 0x40000, 4096),
            ("PASS ARM_ONLY_POST", 11520 * 1024**2, 2),
            ("RETAINED", 7, 2),
        )
    )
    + "K40-A7-END\n"
)
REQUEST = (
    b"K40A7REQ\x01"
    + bytes(7)
    + bytes([0x51]) * 32
    + (7).to_bytes(8, "little")
    + (0x100000).to_bytes(8, "little")
    + (4096).to_bytes(8, "little")
    + bytes(40)
    + bytes([0x61]) * 16
)
SUITE = {
    "package_nonce_hex": (bytes([0x51]) * 32).hex(),
    "artifacts": {"qemu": {"path": "/usr/bin/qemu-system-x86_64"}},
    "physical_vram_bytes": 11520 * 1024**2,
}


class A7Tests(unittest.TestCase):
    def test_extent_request_rejects_stale_and_partial(self):
        self.assertEqual(
            run.request_fields(REQUEST, SUITE, SERIAL), (7, 0x100000, 4096)
        )
        for start in (0, 8, 16, 48, 56, 64, 72, 80):
            raw = bytearray(REQUEST)
            raw[start] ^= 1
            with self.assertRaises(RuntimeError):
                run.request_fields(bytes(raw), SUITE, SERIAL)
        with self.assertRaises(RuntimeError):
            run.request_fields(REQUEST[:-1], SUITE, SERIAL)
        with self.assertRaises(RuntimeError):
            run.request_fields(REQUEST, SUITE, SERIAL + SERIAL)

    def test_final_evidence_order_failures_and_readback_difference(self):
        run.serial_valid(SERIAL + FINAL, True)
        for marker in (
            "ARM_AFTER",
            "ARM_READBACK",
            "POST_RESULT",
            "TIMER",
            "SCRATCH_PASS",
            "RETAINED",
        ):
            with self.assertRaises(RuntimeError):
                run.serial_valid((SERIAL + FINAL).replace(marker, "missing"), True)
        for extra in (
            "k40_a7: FAIL startup a=0x1 b=0x2\n",
            "k40_stage: UNREVIEWED_WRITE\n",
            "PANIC: stop\n",
        ):
            with self.assertRaises(RuntimeError):
                run.serial_valid(SERIAL + FINAL + extra, True)

    def test_strict_r5_stops_even_nonfault_vfio_lines(self):
        for line in (
            "vfio-pci 0000:04:00.0 enabling device",
            "DMAR: information",
            "AER: corrected",
            "IOMMU: mapping",
            "PCIe Bus Error",
        ):
            log = run.StrictLog.__new__(run.StrictLog)
            log.last = b"baseline\n"
            with patch.object(
                run.KernelLog,
                "poll",
                return_value=b"baseline\n" + line.encode() + b"\n",
            ):
                with self.assertRaises(RuntimeError):
                    log.poll()

    def test_exchange_no_secret_or_arbitrary_path_and_write_once(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "f"
            folder.mkdir()
            evidence = Path(d) / "e"
            evidence.mkdir()
            for name in ("identity", "owner", "client"):
                (folder / name).write_bytes(name.encode())
            kernel = b"synthetic kernel"
            suite = {"kernel_sha256": hashlib.sha256(kernel).hexdigest()}
            with run.exchange(folder, evidence, suite) as (port, ready):

                def request(name, data=None):
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/" + name,
                        data=data,
                        method="GET" if data is None else "PUT",
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=3) as response:
                            return response.status, response.read()
                    except urllib.error.HTTPError as exc:
                        with exc:
                            return exc.code, exc.read()

                self.assertEqual(request("client"), (200, b"client"))
                for name in (
                    "../host-key.pem",
                    "host-key.pem",
                    "a7_config.h",
                    "grant.bin",
                ):
                    self.assertEqual(request(name)[0], 404)
                self.assertEqual(request("request.bin", b"x" * 127)[0], 400)
                self.assertEqual(request("request.bin", REQUEST)[0], 201)
                self.assertEqual(request("request.bin", bytes(128))[0], 409)
                self.assertEqual(request("kernel_x86_64", b"wrong")[0], 409)
                self.assertEqual(request("kernel_x86_64", kernel)[0], 201)
                self.assertFalse((evidence / "kernel_x86_64").exists())
                run.save(evidence / "grant.bin", b"synthetic grant")
                ready.set()
                self.assertEqual(request("grant.bin"), (200, b"synthetic grant"))
                self.assertEqual(request("job.exit", b"x" * 17)[0], 413)
                self.assertEqual(
                    request("job-output.txt", b"A7-OPEN-DEVICE\nopen error\n")[0], 201
                )
                self.assertEqual(request("job-output.txt", b"replacement")[0], 409)
                self.assertEqual(request("job-output.txt", b"x" * 65537)[0], 413)

    def test_fresh_mapping_cutoff_and_no_grant_on_stop(self):
        for problem in (
            None,
            "binding",
            "identity",
            "role",
            "kernel",
            "guestfail",
            "lateclose",
            "partial",
            "stale-request",
            "new-r5",
        ):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as d:
                folder = Path(d) / "f"
                folder.mkdir()
                evidence = Path(d) / "e"
                evidence.mkdir()
                trace = Path(d) / "trace"
                records = [
                    line.replace("iova=0x1000", "iova=0x100000") for line in LINES
                ]
                if problem == "binding":
                    records[-1] = records[-1].replace("04:00.0", "03:00.0")
                trace.write_text(
                    '100 execve("/usr/bin/qemu-system-x86_64", [], 0) = 0\n'
                    + "".join("100 " + line + "\n" for line in records)
                )
                serial = (
                    SERIAL.replace("0x0f1240a1", "0xdeadbeef")
                    if problem == "identity"
                    else SERIAL
                )
                if problem == "role":
                    serial += "k40_stage: UNREVIEWED_WRITE\n"
                (evidence / "serial.log").write_text(serial)
                (evidence / "request.bin").write_bytes(
                    bytes(128) if problem == "stale-request" else REQUEST
                )
                if problem != "kernel":
                    (evidence / "kernel.sha256").write_text("synthetic hash\n")
                if problem == "guestfail":
                    (evidence / "job.exit").write_text("1\n")

                class Process:
                    pid = 100

                class Child:
                    process = Process()

                    def check(self):
                        pass

                child = Child()
                child.trace = trace

                class Kernel:
                    def poll(self):
                        if problem == "new-r5":
                            raise RuntimeError("new R5 selected-class line")

                class Ready:
                    called = False

                    def set(self):
                        self.called = True
                        with (evidence / "serial.log").open("a") as out:
                            out.write(FINAL)
                        (evidence / "job.exit").write_text("0\n")

                ready = Ready()
                topology = {
                    name: (TOPO / (name + ".txt")).read_text()
                    for name in ("qtree", "mtree", "ramblock")
                }
                topology[
                    "qtree"
                ] += '\n  dev: vfio-pci, id "test"\n    host = "0000:04:00.0"\n'

                def snapshot(_):
                    if problem == "lateclose":
                        with trace.open("a") as out:
                            out.write("100 close(9) = 0\n")
                    if problem == "partial":
                        with trace.open("a") as out:
                            out.write("100 ioctl(")
                    return topology

                with patch.object(run, "snapshot", side_effect=snapshot), patch.object(
                    run, "sign", return_value=b"synthetic signature"
                ) as signer:
                    if problem:
                        with self.assertRaises(RuntimeError):
                            run.monitor(
                                child,
                                folder,
                                evidence,
                                1,
                                ready,
                                {"group": "23"},
                                Kernel(),
                                SUITE,
                            )
                        self.assertFalse(ready.called)
                        signer.assert_not_called()
                    else:
                        run.monitor(
                            child,
                            folder,
                            evidence,
                            1,
                            ready,
                            {"group": "23"},
                            Kernel(),
                            SUITE,
                        )
                        self.assertTrue(ready.called)
                        signer.assert_called_once()
                        cutoff = json.loads((evidence / "cutoff.json").read_text())
                        self.assertIn("INFERRED", cutoff["claim"])

    def test_host_command_is_read_only_and_rejects_master_at_teardown(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "config"
            path.write_bytes(bytes(4) + b"\x07\x00")
            self.assertEqual(run.command_register(path), 7)
            self.assertEqual(path.read_bytes(), bytes(4) + b"\x07\x00")
        with patch.object(run, "command_register", return_value=2):
            self.assertEqual(run.stopped_command(), 2)
        with patch.object(run, "command_register", return_value=7), patch.object(
            run.time, "monotonic", side_effect=(0, 3)
        ):
            with self.assertRaises(RuntimeError):
                run.stopped_command()

    def test_teardown_check_compares_all_metadata_without_writes(self):
        from tools.a7 import teardown_sources as sources

        with tempfile.TemporaryDirectory() as d:
            cache = Path(d) / "cache"
            output = Path(d) / "record.json"
            for name in sources.FILES:
                path = cache / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic source")
            with patch.object(sources, "CACHE", cache), patch.object(
                sources, "OUTPUT", output
            ), patch.object(
                sys, "argv", ["teardown_sources.py", "--check"]
            ), patch.object(
                sources.urllib.request, "urlopen"
            ) as network:
                output.write_text(sources.render())
                self.assertEqual(sources.main(), 0)
                original = output.read_text().replace(
                    "SOURCE_ONLY", "UNSUPPORTED_CLAIM"
                )
                output.write_text(original)
                self.assertEqual(sources.main(), 1)
                self.assertEqual(output.read_text(), original)
                network.assert_not_called()

    def test_default_never_starts_guest(self):
        with patch.object(sys, "argv", ["run.py", "--check"]), patch.object(
            run, "prerequisites"
        ), patch.object(run, "run") as launch:
            self.assertEqual(run.main(), 0)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
