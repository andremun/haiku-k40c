# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Host parser/phase/transport failures; no guest, VFIO device or package key."""
import copy
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unittest.mock import patch
import urllib.error
import urllib.request

from tools.memstage import evidence, pci, build
from tools.memstage.monitor import Broker, exit_status
from tools.memstage.exchange import exchange
from tools.memstage.guest_job import job
from tools.memstage.sign import grant

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    target = dict(
        bus=0,
        slot=4,
        function=0,
        id=dict(vendor=0x10DE, device=0x1024),
        regions=[
            dict(
                bar=0,
                type="memory",
                address=268435456,
                size=16777216,
                mem_type_64=False,
            ),
            dict(
                bar=1,
                type="memory",
                address=536870912,
                size=268435456,
                mem_type_64=True,
            ),
        ],
    )
    return [dict(bus=0, devices=[target])]


def frame():
    raw = bytearray(256)
    raw[:16] = b"K40MEMREQ\x01" + bytes(6)
    raw[16:48] = bytes([1]) * 32
    raw[48:80] = bytes([2]) * 32
    raw[80:96] = bytes([3]) * 16
    raw[96:176] = struct.pack(
        "<10Q",
        2,
        2,
        268435456,
        16777216,
        536870912,
        268435456,
        11520 * 1048576,
        256 * 1024 + 4096,
        11519 * 1048576,
        8192,
    )
    suite = dict(
        package_nonce_hex=(bytes([1]) * 32).hex(),
        plan_sha256=(bytes([2]) * 32).hex(),
        plan=dict(vram_bytes=11520 * 1048576),
    )
    serial = "k40_mem: MAP bar=0 base=10000000 resource=16777216 mapped=8388608 flags=explicit-UC status=3\n"
    serial += "k40_mem: MAP bar=1 base=20000000 resource=268435456 mapped=8192 flags=explicit-UC read-only status=4\n"
    serial += "k40_mem: PREPARED owner=2 epoch=2 bar0=10000000 bar1=20000000\n"
    return bytes(raw), suite, serial


class Tests(unittest.TestCase):
    def test_pci_unique_and_bridges(self):
        value = fixture()
        expected = pci.resources(value)
        bridge = dict(
            bus=0,
            slot=1,
            function=0,
            id=dict(vendor=1, device=1),
            regions=[],
            pci_bridge=dict(devices=value[0]["devices"]),
        )
        self.assertEqual(pci.resources([dict(bus=0, devices=[bridge])]), expected)
        for name in (
            "missing",
            "duplicate",
            "overlap",
            "io",
            "negative",
            "size",
            "width",
            "bar",
        ):
            changed = copy.deepcopy(value)
            target = changed[0]["devices"][0]
            if name == "missing":
                target["id"]["device"] = 0
            elif name == "duplicate":
                changed[0]["devices"].append(copy.deepcopy(target))
                changed[0]["devices"][1]["slot"] = 5
            elif name == "overlap":
                target["regions"][1]["address"] = 268435456
            elif name == "io":
                target["regions"][1]["type"] = "io"
            elif name == "negative":
                target["regions"][1]["address"] = -1
            elif name == "size":
                target["regions"][1]["size"] = 12288
            elif name == "width":
                del target["regions"][1]["mem_type_64"]
            else:
                target["regions"][1]["bar"] = True
            with self.subTest(name=name), self.assertRaises(ValueError):
                pci.resources(changed)

    def test_memory_request_binding(self):
        raw, suite, serial = frame()
        resources = pci.resources(fixture())
        self.assertEqual(
            evidence.request_fields(raw, suite, serial, resources)["begin"],
            int("41000", 16),
        )
        for offset in (
            0,
            16,
            48,
            80,
            96,
            104,
            112,
            120,
            128,
            136,
            144,
            152,
            160,
            168,
            176,
            192,
            224,
            255,
        ):
            changed = bytearray(raw)
            if offset == 80:
                changed[80:96] = bytes(16)
            else:
                changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                evidence.request_fields(bytes(changed), suite, serial, resources)
        with self.assertRaises(ValueError):
            evidence.request_fields(
                raw, suite, serial.replace("read-only", "writeable"), resources
            )

    def test_production_trace_and_mutations(self):
        raw, suite, unused = frame()
        suite["plan"]["A7_guest_artifacts"] = {}
        serial = subprocess.check_output(
            [str(ROOT / "build/tests/test_mem_policy"), "--dump"], text=True, timeout=30
        )
        result = evidence.memory_final(serial, suite, raw)
        self.assertEqual(result["bar_flush_count"], 17)
        mutations = [
            serial.replace("closure=2", "closure=1"),
            serial.replace("retained=1", "retained=0", 1),
            serial.replace("generation=5", "generation=4"),
            serial.replace("operation=7", "operation=0", 1),
            serial.replace("value=80000005", "value=80000007", 1),
            serial.replace("staged=1", "staged=0", 1),
            serial.replace(
                "k40_mem: RETAINED owner=2 state=3", "k40_mem: RETAINED owner=3 state=3"
            ),
        ]
        for changed in mutations:
            with self.assertRaises(ValueError):
                evidence.memory_final(changed, suite, raw)

    def test_cardless_cannot_sign(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            ready = {}
            broker = Broker(folder, folder, folder, {}, ready, True)
            with patch(
                "tools.memstage.sign.load", side_effect=AssertionError("key read")
            ):
                with self.assertRaises(ValueError):
                    broker.release(
                        "memory",
                        b"",
                        bytes([1]) * 32,
                        folder / "grant.bin",
                        threading.Event(),
                    )
                with self.assertRaises(ValueError):
                    grant("A7", bytes(256), bytes([1]) * 32, {})
                with self.assertRaises(ValueError):
                    grant("memory", bytes(128), bytes([1]) * 32, {})

    def test_exit_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exit"
            self.assertIsNone(exit_status(path))
            path.write_bytes(b"0")
            self.assertIsNone(exit_status(path))
            path.write_bytes(b"0\n")
            self.assertEqual(exit_status(path), 0)
            path.write_bytes(b"0\n1\n")
            with self.assertRaises(ValueError):
                exit_status(path)

    def test_transport_and_job(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            folder = base / "files"
            folder.mkdir()
            captures = base / "results"
            captures.mkdir()
            artifacts = {role: dict(bytes=3, sha256="a" * 64) for role in build.ROLES}
            suite = dict(guest_artifacts=artifacts)
            for role in artifacts:
                (folder / role).write_bytes(b"ELF")
            with exchange(folder, captures, suite, 9) as (port, ready):
                endpoint = f"http://127.0.0.1:{port}"
                self.assertEqual(
                    urllib.request.urlopen(endpoint + "/preflight", timeout=3).read(),
                    b"ELF",
                )
                for path in (
                    "/host-key.pem",
                    "/../host-key.pem",
                    "/advance-memory",
                    "/grant.bin",
                ):
                    with self.assertRaises(urllib.error.HTTPError):
                        urllib.request.urlopen(endpoint + path, timeout=3)
                request = urllib.request.Request(
                    endpoint + "/request.bin", data=bytes(256), method="PUT"
                )
                with urllib.request.urlopen(request, timeout=3) as response:
                    self.assertEqual(response.status, 201)
                self.assertTrue(ready["request.bin"].is_set())
                with self.assertRaises(urllib.error.HTTPError):
                    urllib.request.urlopen(
                        urllib.request.Request(
                            endpoint + "/request.bin", data=bytes(255), method="PUT"
                        ),
                        timeout=3,
                    )
                self.assertEqual((folder / "job.sh").read_text(), job(port, 9, suite))
                text = job(0, 0, suite)
                self.assertIn(".k40-memory-staging", text)
                self.assertNotIn("host-key", text)
                self.assertNotIn("vfio", text)
                self.assertIn("inode-before", text)
                self.assertIn("wait_gate advance-memory", text)


if __name__ == "__main__":
    unittest.main()
