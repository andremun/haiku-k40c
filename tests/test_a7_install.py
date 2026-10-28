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
    def test_complete_executable_published_once(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            stage = root / "private"
            stage.mkdir()
            target = root / "live"
            env = dict(
                os.environ, stage=str(stage), target=str(target), host="http://inert"
            )
            script = (
                """set -eu
curl() {
    printf partial > "$3"
    test ! -e "$target"
    printf complete >> "$3"
}
"""
                + guest_job.INSTALL
                + '\ninstall_artifact identity "$target"\n'
            )
            subprocess.run(["sh", "-c", script], env=env, check=True)
            self.assertEqual(target.read_bytes(), b"partialcomplete")
            self.assertEqual(
                target.stat().st_ino, (stage / "identity" / "addon").stat().st_ino
            )
            self.assertTrue(target.stat().st_mode & 0o111)

    def test_no_publication_on_download_chmod_or_link_failure(self):
        for failure in ("download", "chmod", "link", "existing"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                stage = root / "private"
                stage.mkdir()
                target = root / "live"
                if failure == "existing":
                    target.write_bytes(b"preserve me")
                env = dict(
                    os.environ,
                    stage=str(stage),
                    target=str(target),
                    host="http://inert",
                    failure=failure,
                )
                script = """set -eu
curl() { printf partial > "$3"; test "$failure" != download; }
"""
                if failure == "chmod":
                    script += "chmod() { return 1; }\n"
                if failure == "link":
                    script += "ln() { return 1; }\n"
                result = subprocess.run(
                    [
                        "sh",
                        "-c",
                        script
                        + guest_job.INSTALL
                        + '\ninstall_artifact identity "$target"\n',
                    ],
                    env=env,
                    capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)
                if failure == "existing":
                    self.assertEqual(target.read_bytes(), b"preserve me")
                else:
                    self.assertFalse(target.exists())

    def test_second_install_cannot_truncate_a_published_inode(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            stage = root / "private"
            stage.mkdir()
            target = root / "live"
            calls = root / "calls"
            env = dict(
                os.environ,
                stage=str(stage),
                target=str(target),
                calls=str(calls),
                host="http://inert",
            )
            script = (
                'set -eu\ncurl() { echo download >> "$calls"; printf complete > "$3"; }\n'
                + guest_job.INSTALL
                + '\ninstall_artifact identity "$target"\ninstall_artifact identity "$target"\n'
            )
            result = subprocess.run(["sh", "-c", script], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(calls.read_text().splitlines(), ["download"])
            self.assertEqual(target.read_bytes(), b"complete")

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

    def test_job_syntax_and_one_open_after_wait(self):
        script = guest_job.job(12345)
        subprocess.run(["sh", "-n"], input=script, text=True, check=True)
        self.assertEqual(script.count("exec 3<>/dev/misc/k40_a7_stage"), 1)
        self.assertLess(script.index("\nwait_a7_node\n"), script.index("exec 3<>"))
        self.assertLess(
            script.index("echo K40-B5-BEGIN"), script.index("install_artifact identity")
        )
        self.assertLess(
            script.index('mkdir -p "$base"'), script.index('mkdir "$stage"')
        )
        self.assertNotIn("mv ", guest_job.INSTALL)
        self.assertNotIn("cp ", guest_job.INSTALL)


if __name__ == "__main__":
    unittest.main()
