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
    serial = "k40_mem: MAP bar=0 base=10000000 resource=16777216 mapped=16777216 flags=explicit-UC status=3\n"
    serial += "k40_mem: MAP bar=1 base=20000000 resource=268435456 mapped=8192 flags=explicit-UC read-write status=4\n"
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
                raw, suite, serial.replace("read-write", "writeable"), resources
            )

    def test_production_trace_and_mutations(self):
        raw, suite, unused = frame()
        suite["plan"]["A7_guest_artifacts"] = {}
        serial = subprocess.check_output(
            [str(ROOT / "build/tests/test_mem_channel"), "--dump"], text=True, timeout=30
        )
        result = evidence.memory_final(serial, suite, raw)
        self.assertEqual(result["bar_flush_count"], 17)
        mutations = [
            serial.replace("closure=2", "closure=1"),
            serial.replace("retained=1", "retained=0", 1),
            serial.replace("generation=6", "generation=5"),
            serial.replace("generation=15", "generation=14"),
            serial.replace("after=1/1", "after=0/1"),
            serial.replace("mmu=0", "mmu=1"),
            serial.replace("runlist=1/4", "runlist=1/3"),
            serial.replace("value=3000000100000000", "value=3000000f00000000"),
            serial.replace("value=80000001", "value=80000003"),
            serial.replace("value=20010002", "value=20010003"),
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

    def test_copy_trace_and_mutations(self):
        raw, suite, unused = frame()
        suite["plan"]["A7_guest_artifacts"] = {}
        serial = subprocess.check_output(
            [str(ROOT / "build/tests/test_mem_copy"), "--dump"], text=True, timeout=30
        )
        # An S2 report is refused as S1, and the S1 report as S2.
        with self.assertRaises(ValueError):
            evidence.memory_final(serial, suite, raw)
        s1 = subprocess.check_output(
            [str(ROOT / "build/tests/test_mem_channel"), "--dump"], text=True, timeout=30
        )
        suite["stage"] = evidence.COPY_STAGE
        with self.assertRaises(ValueError):
            evidence.memory_final(s1, suite, raw)
        result = evidence.memory_final(serial, suite, raw)
        self.assertTrue(result["S2_complete"])
        self.assertEqual(result["channel"]["copy"]["engine"], 4)
        self.assertEqual(len(result["allocations"]), 16)
        mutations = [
            serial.replace("copied=1", "copied=0"),
            serial.replace("get=2/2", "get=1/2"),
            serial.replace("launcherr=0", "launcherr=2"),
            serial.replace("ce_intr=0", "ce_intr=4"),
            serial.replace("COPY_STATUS engine=0", "COPY_STATUS engine=80000000"),
            serial.replace("engine=1/4", "engine=1/5"),
            serial.replace("offset=28c value=2", "offset=28c value=3"),
            serial.replace("operation=4 role=16 detail=1", "operation=4 role=16 detail=0"),
            serial.replace("operation=3 role=15 detail=1", "operation=3 role=15 detail=2"),
            serial.replace("value=a0b520018000", "value=a0b520018001"),  # object bind header.
            serial.replace("value=838680c000000001", "value=838280c000000001"),  # launch without FLUSH.
            serial.replace("value=100000001000", "value=100000000ffc"),  # pitch or line length.
            serial.replace("generation=8", "generation=7"),
            serial.replace("allocations=16", "allocations=14"),
        ]
        for index, changed in enumerate(mutations):
            with self.subTest(index=index):
                self.assertNotEqual(changed, serial)
                with self.assertRaises(ValueError):
                    evidence.memory_final(changed, suite, raw)

    def test_gr_trace_and_mutations(self):
        raw, suite, unused = frame()
        suite["plan"]["A7_guest_artifacts"] = {}
        binary, fixture = str(ROOT / "build/tests/test_gr_compute"), str(ROOT / "build/tests/gr/gr_trace.txt")
        compute = subprocess.check_output([binary, fixture, "--report"], text=True, timeout=300)
        golden = subprocess.check_output([binary, fixture, "--report", "nolaunch"], text=True, timeout=300)
        with self.assertRaises(ValueError):  # an S3 report is not an S1 report
            evidence.memory_final(compute, suite, raw)
        suite["stage"] = "S3B_A7_BAR1_GR_COMPUTE"
        result = evidence.memory_final(compute, suite, raw)
        self.assertTrue(result["S3_complete"])
        self.assertEqual(len(result["allocations"]), 26)
        with self.assertRaises(ValueError):  # a golden-only report is not a compute report
            evidence.memory_final(golden, suite, raw)
        mutations = [
            compute.replace("computed=1", "computed=0"),
            compute.replace("wrong=0", "wrong=1"),
            compute.replace("after=1/1", "after=0/1"),
            compute.replace("trap=0", "trap=1"),
            compute.replace("fecs=0", "fecs=4"),
            compute.replace("gr=0", "gr=100000"),
            compute.replace("guard=6/", "guard=5/"),
            compute.replace("golden=1", "golden=0"),
            compute.replace("closing=0", "closing=1"),
            compute.replace("offset=28c value=1", "offset=28c value=2"),
            compute.replace("operation=8 role=0 detail=1", "operation=8 role=0 detail=0", 1),
            compute.replace("role=23 physical", "role=22 physical"),
            compute.replace("allocations=26", "allocations=14"),
            compute.replace("PASS S3_COMPUTE", "PASS S3_GOLDEN"),
        ]
        for index, changed in enumerate(mutations):
            with self.subTest(index=index):
                self.assertNotEqual(changed, compute)
                with self.assertRaises(ValueError):
                    evidence.memory_final(changed, suite, raw)
        suite["stage"] = "S3A_A7_BAR1_GR_GOLDEN"
        result = evidence.memory_final(golden, suite, raw)
        self.assertTrue(result["S3_golden_complete"])
        self.assertFalse(result["S3_complete"])
        with self.assertRaises(ValueError):
            evidence.memory_final(compute, suite, raw)

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
