#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Exercise B5 refusal, evidence, and watchdog behavior without a GPU or VM.

Reads launcher modules and synthetic PCI/probe fixtures in temporary folders.
Starts only local HTTP servers and short-lived sleep processes. Writes no results.
"""

import hashlib
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/haiku"))
import card_run
import probe_stage
import vm_guard


class CardRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.tmp = Path(self.temporary.name)
        self.sysfs = self.tmp / "sys"
        self.dev = self.tmp / "dev"
        self.device = self.sysfs / "bus/pci/devices" / card_run.ALLOWED_BDF
        self.device.mkdir(parents=True)
        driver = self.sysfs / "bus/pci/drivers/vfio-pci"
        driver.mkdir(parents=True)
        (self.device / "driver").symlink_to(driver)
        self.group = self.sysfs / "kernel/iommu_groups/23"
        (self.group / "devices").mkdir(parents=True)
        (self.group / "devices" / card_run.ALLOWED_BDF).symlink_to(self.device)
        (self.device / "iommu_group").symlink_to(self.group)
        (self.dev / "vfio").mkdir(parents=True)
        (self.dev / "vfio/23").touch()

    def preflight(self, bdf=card_run.ALLOWED_BDF):
        return card_run.preflight(bdf, self.sysfs, self.dev)

    def test_exact_device(self):
        self.assertEqual(self.preflight()["members"], [card_run.ALLOWED_BDF])
        for bdf in ("0000:03:00.0", "0000:82:00.0", "04:00.0", ""):
            with self.subTest(bdf=bdf), self.assertRaises(ValueError):
                self.preflight(bdf)

    def test_binding_and_isolation(self):
        (self.device / "driver").unlink()
        with self.assertRaises(ValueError):
            self.preflight()
        other = self.sysfs / "bus/pci/drivers/nvidia"
        other.mkdir()
        (self.device / "driver").symlink_to(other)
        with self.assertRaises(ValueError):
            self.preflight()
        (self.device / "driver").unlink()
        (self.device / "driver").symlink_to(other.with_name("vfio-pci"))
        (self.group / "devices/0000:04:00.1").touch()
        with self.assertRaises(ValueError):
            self.preflight()

    def test_vfio_access(self):
        with patch.object(card_run.os, "access", return_value=False):
            with self.assertRaises(ValueError):
                self.preflight()
        (self.dev / "vfio/23").unlink()
        with self.assertRaises(ValueError):
            self.preflight()

    def test_stage_tampering(self):
        driver = self.tmp / "probe"
        driver.write_bytes(b"\x7fELF" + probe_stage.STAGE.encode())
        kernel = self.tmp / "kernel"
        kernel.write_bytes(b"test-kernel")
        for name in probe_stage.SOURCES:
            p = self.tmp / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("source fixture\n")
        sidecar = driver.with_name(driver.name + ".stage.json")
        sidecar.write_text(probe_stage.stage_text(driver, self.tmp, kernel))
        self.assertEqual(probe_stage.validate(driver, self.tmp, kernel)["stage"], probe_stage.STAGE)
        old = driver.read_bytes()
        driver.write_bytes(old + b"tampered")
        with self.assertRaises(ValueError):
            probe_stage.validate(driver, self.tmp, kernel)
        driver.write_bytes(old)
        (self.tmp / probe_stage.SOURCES[0]).write_text("changed\n")
        with self.assertRaises(ValueError):
            probe_stage.validate(driver, self.tmp, kernel)
        driver.write_bytes(b"\x7fELFcardless")
        with self.assertRaises(ValueError):
            probe_stage.manifest(driver, self.tmp, kernel)

    def serial(self):
        return ("K40-B5-BEGIN\n"
                "k40_stage: B5_IDENTITY_READ_ONLY\n"
                "k40_os: PCI command 0x0002\n"
                "k40_os: GPU identity 0x0f1240a1; no bring-up or DMA\n"
                "k40_os: PASS B5 identity reads only\nK40-B5-END\n")

    def test_complete_evidence_only(self):
        serial = self.serial()
        self.assertTrue(card_run.verdict(serial, b"0\n"))
        # Haiku devfs can reload a driver whose published device list is empty.
        repeated = serial.replace("K40-B5-END", serial.split("K40-B5-BEGIN\n")[1])
        self.assertTrue(card_run.verdict(repeated, b"0\n"))
        self.assertFalse(card_run.verdict(serial, None))
        self.assertFalse(card_run.verdict(serial.replace("K40-B5-END", ""), b"0"))
        for bad in (
            serial.replace("0x0f1240a1", "0xffffffff"),
            serial.replace("PCI command 0x0002", "PCI command 0x0000"),
            serial.replace("B5_IDENTITY_READ_ONLY", "CARDLESS"),
            serial.replace("k40_os: PASS B5 identity reads only", "k40_os: PASS native OS mechanics only"),
            serial + "PANIC: test\n", serial + "k40_os: FAIL status -1\n",
            serial + "k40_os: cleanup failed\n",
        ):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                card_run.verdict(bad, b"0")
        with self.assertRaises(RuntimeError):
            card_run.verdict(serial, b"1")

    def test_closed_qemu_options(self):
        args = card_run.qemu_args(self.tmp / "base", self.tmp, self.tmp, card_run.ALLOWED_BDF)
        host_devices = [arg for arg in args if "host=" in arg]
        self.assertEqual(host_devices, ["vfio-pci,host=0000:04:00.0"])
        self.assertIn("overlay.qcow2", " ".join(args))
        self.assertNotIn(str(self.tmp / "base"), " ".join(args))
        with self.assertRaises(ValueError):
            card_run.qemu_args(self.tmp, self.tmp, self.tmp, "0000:03:00.0")

    def test_timeout_bounds_before_launch(self):
        with patch.object(card_run.subprocess, "Popen") as launch:
            for seconds in (0, 29, 601):
                with self.assertRaises(ValueError):
                    card_run.run(self.tmp, self.tmp, self.tmp, seconds)
            launch.assert_not_called()

    def test_single_guest_lock_and_inventory(self):
        with patch.object(vm_guard, "refuse_running_guest"):
            with vm_guard.guest_lock(self.tmp):
                with self.assertRaises(ValueError):
                    with vm_guard.guest_lock(self.tmp):
                        self.fail("second lock acquired")
        proc = self.tmp / "proc/123"
        proc.mkdir(parents=True)
        (proc / "comm").write_text("qemu-system-x86\n")
        with self.assertRaises(ValueError):
            vm_guard.refuse_running_guest(proc.parent)

    def test_independent_deadline(self):
        proc = subprocess.Popen(["sleep", "30"])
        try:
            with vm_guard.deadline(proc, 0.1, self.tmp / "deadline"):
                proc.wait(timeout=5)
            self.assertLess(proc.returncode, 0)
            self.assertEqual((self.tmp / "deadline").read_text(), "deadline expired\n")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.wait()

    def test_watchdog_survives_launcher_death(self):
        code = (
            "import os,subprocess,sys;from pathlib import Path;"
            "sys.path.insert(0,sys.argv[1]);from vm_guard import deadline;"
            "p=subprocess.Popen(['sleep','30']);"
            "d=deadline(p,20,Path(sys.argv[2]));d.__enter__();"
            "print(p.pid,flush=True);os._exit(0)"
        )
        parent = subprocess.Popen([sys.executable, "-c", code, str(ROOT / "tools/haiku"),
                                   str(self.tmp / "parent-death")], stdout=subprocess.PIPE)
        pid = int(parent.stdout.readline())
        fd = os.pidfd_open(pid)
        try:
            parent.wait(timeout=5)
            self.assertTrue(select.select([fd], [], [], 5)[0])
            self.assertEqual((self.tmp / "parent-death").read_text(), "launcher exited\n")
        finally:
            os.close(fd)
            parent.stdout.close()

    def test_exchange_kernel_and_write_once(self):
        folder = self.tmp / "run"
        evidence = self.tmp / "evidence"
        folder.mkdir()
        evidence.mkdir()
        (folder / "probe").write_bytes(b"driver")
        kernel = b"expected kernel"
        with card_run.exchange(folder, evidence, hashlib.sha256(kernel).hexdigest()) as port:
            def put(name, data):
                request = urllib.request.Request(f"http://127.0.0.1:{port}/{name}",
                                                 method="PUT", data=data)
                try:
                    with urllib.request.urlopen(request, timeout=3) as reply:
                        return reply.status
                except urllib.error.HTTPError as error:
                    return error.code
            self.assertEqual(put("kernel_x86_64", b"wrong kernel"), 409)
            self.assertFalse((evidence / "kernel_x86_64").exists())
            self.assertEqual(put("kernel_x86_64", kernel), 201)
            self.assertEqual((evidence / "kernel.sha256").read_text().strip(),
                             hashlib.sha256(kernel).hexdigest())
            self.assertEqual(put("job.exit", b"0"), 201)
            self.assertEqual(put("job.exit", b"1"), 409)
            self.assertEqual(put("../outside", b"bad"), 413)
            self.assertEqual(put("job.exit", b"a" * 33), 413)


if __name__ == "__main__":
    unittest.main()
