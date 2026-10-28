#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Execute actual A7 shell helpers against inert host fixtures, never a guest."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.a7 import guest_job


class InstallationTests(unittest.TestCase):
    def test_checked_rename_and_failures(self):
        import hashlib

        payload = b"complete binary"
        digest = hashlib.sha256(payload).hexdigest()
        for failure in (
            None,
            "download",
            "size",
            "hash",
            "chmod",
            "rename",
            "copy",
            "existing",
        ):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                target = root / "live"
                if failure == "existing":
                    target.write_bytes(b"preserve")
                script = (
                    'set -eu\nhost=http://inert\ncurl() { printf "complete binary" > "$3"; '
                    + ("return 1;" if failure == "download" else "")
                    + " }\n"
                )
                if failure == "chmod":
                    script += "chmod() { return 1; }\n"
                if failure == "rename":
                    script += "mv() { return 1; }\n"
                if failure == "copy":
                    script += 'mv() { cp "$1" "$2"; rm "$1"; }\n'
                script += guest_job.INSTALL
                script += f'\ninstall_artifact identity "{target}" {1 if failure == "size" else len(payload)} {"0"*64 if failure == "hash" else digest}\n'
                result = subprocess.run(
                    ["sh", "-c", script], capture_output=True, text=True
                )
                self.assertEqual(result.returncode == 0, failure is None, result.stderr)
                if failure is None:
                    self.assertEqual(target.read_bytes(), payload)
                    self.assertTrue(target.stat().st_mode & 0o111)
                    self.assertIn("inode-before=", result.stdout)
                elif failure == "existing":
                    self.assertEqual(target.read_bytes(), b"preserve")
                elif failure != "copy":
                    self.assertFalse(target.exists())

    def test_publication_wait_is_bounded_and_does_not_open(self):
        for present in (False, True):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as d:
                calls = Path(d) / "calls"
                device = "/dev/null" if present else str(Path(d) / "absent")
                # Only the fixture substitutes the path. The shipped job is fixed.
                wait = guest_job.WAIT.replace("/dev/misc/k40_a7_stage", device)
                env = dict(os.environ, calls=str(calls))
                script = (
                    """set -eu
ls() { echo scan >> "$calls"; }
sleep() { echo delay >> "$calls"; }
"""
                    + wait
                    + "\nwait_a7_node\n"
                )
                result = subprocess.run(
                    ["sh", "-c", script], env=env, capture_output=True, text=True
                )
                events = calls.read_text().splitlines()
                self.assertEqual(events.count("scan"), 1 if present else 30)
                self.assertEqual(events.count("delay"), 0 if present else 30)
                self.assertEqual(result.returncode, 0 if present else 1)
                self.assertIn(
                    (
                        "A7-DEVICE-PUBLISHED"
                        if present
                        else "A7-DEVICE-PUBLICATION-TIMEOUT"
                    ),
                    result.stdout + result.stderr,
                )

    def test_rehearsal_requires_specific_refusal_and_matching_binding(self):
        from tools.a7 import rehearse
        import copy

        artifacts = {
            role: dict(bytes=1, sha256="a" * 64)
            for role in ("identity", "owner", "client")
        }
        suite = dict(guest_artifacts=artifacts, kernel_sha256="b" * 64)
        original = rehearse.binding(suite)
        for role in artifacts:
            altered = copy.deepcopy(suite)
            altered["guest_artifacts"][role]["sha256"] = "c" * 64
            self.assertNotEqual(original, rehearse.binding(altered))
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            output = "".join(
                f"A7-INSTALL {role} size=1 sha256={'a'*64} inode-before=7 inode-after=7\n"
                for role in artifacts
            )
            output += "A7-DEVICE-PUBLISHED\nA7-OPEN-DEVICE\n"
            (folder / "job-output.txt").write_text(output)
            (folder / "job.exit").write_text("1\n")
            (folder / "kernel.sha256").write_text("b" * 64 + "\n")
            good = "k40_a7: REFUSED no matching PCI card before reservation\nk40_a7: FAIL client prepare\n"
            (folder / "serial.log").write_text(good)
            rehearse.capture_verdict(folder, suite)
            for bad in ("", "k40_a7: FAIL client prepare\n", good + "k40_a7: PREPARED"):
                (folder / "serial.log").write_text(bad)
                with self.assertRaises(ValueError):
                    rehearse.capture_verdict(folder, suite)

    def test_job_syntax_and_one_open_after_wait(self):
        script = guest_job.job(
            12345,
            {
                role: dict(bytes=1, sha256="0" * 64)
                for role in ("identity", "owner", "client")
            },
        )
        subprocess.run(["sh", "-n"], input=script, text=True, check=True)
        self.assertEqual(script.count("exec 3<>/dev/misc/k40_a7_stage"), 1)
        self.assertLess(script.index("\nwait_a7_node\n"), script.index("exec 3<>"))
        self.assertLess(
            script.index("echo K40-B5-BEGIN"), script.index("install_artifact identity")
        )
        self.assertIn("base=/boot/system/non-packaged/add-ons/kernel", script)
        self.assertNotIn("stage=", script)
        self.assertNotIn("ln ", guest_job.INSTALL)
        self.assertNotIn("cp ", guest_job.INSTALL)
        self.assertIn('test "$before" = "$after"', guest_job.INSTALL)
        self.assertLess(
            script.index("install_artifact owner"),
            script.index("install_artifact client"),
        )


if __name__ == "__main__":
    unittest.main()
