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
                (root / "stage").mkdir()
                if failure == "existing":
                    target.write_bytes(b"preserve")
                script = (
                    'set -eu\nhost=http://inert\nstage="STAGE_FIXTURE"\ncurl() { printf "complete binary" > "$3"; '
                    + ("return 1;" if failure == "download" else "")
                    + " }\n"
                )
                if failure == "chmod":
                    script += "chmod() { return 1; }\n"
                if failure == "rename":
                    script += "mv() { return 1; }\n"
                if failure == "copy":
                    script += 'mv() { cp "$1" "$2"; rm "$1"; }\n'
                script = script.replace("STAGE_FIXTURE", str(root / "stage"))
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
            for role in ("identity", "owner", "client", "helper")
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
            output += "A7-DEVICE-PUBLISHED\nA7-OPEN-DEVICE\nA7-OPEN-RESULT status=0xffffffff\n"
            (folder / "job-output.txt").write_text(output)
            (folder / "job.exit").write_text("1\n")
            (folder / "kernel.sha256").write_text("b" * 64 + "\n")
            good = (
                'driver "k40_identity_probe" added\ndriver "k40_a7_stage" added\nk40_a7: OWNER_LOAD a=0x1 b=0x0\nk40_a7: CLIENT_LOAD a=0x1 b=0x0\nk40_a7: PREPARE_CALL a=0x1 b=0x0\nk40_a7: CLIENT_LOAD a=0x2 b=0x3\nK40-A7-RELOAD-END\n'
                + "k40_a7: REFUSED no matching PCI card before reservation\nk40_a7: FAIL client prepare\n"
            )
            (folder / "serial.log").write_text(good)
            rehearse.capture_verdict(folder, suite)
            for bad in ("", "k40_a7: FAIL client prepare\n", good + "k40_a7: PREPARED"):
                (folder / "serial.log").write_text(bad)
                with self.assertRaises(ValueError):
                    rehearse.capture_verdict(folder, suite)

    def test_native_helper_one_open_and_descriptor_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "OS.h").write_text(
                "#include <stddef.h>\ntypedef int thread_id;\n#define B_OK 0\nthread_id find_thread(const char*);\n"
            )
            (root / "syscalls.h").write_text(
                "int _kern_open(int,const char*,int,int);\n"
            )
            (root / "fixture.c").write_text(
                r"""
#include <assert.h>
#include <fcntl.h>
#include <string.h>
char **argv_save; int __main_thread_id;
static int result,opens,duplicates,closes,execs,deny;
int find_thread(const char* unused){(void)unused;return 7;}
int _kern_open(int fd,const char* path,int flags,int mode){assert(fd==-1 && flags==O_RDWR && mode==0);assert(!strcmp(path,"/dev/misc/k40_a7_stage"));++opens;return result;}
int mock_dup2(int fd,int target){assert(fd==9 && target==3);++duplicates;return deny?-1:3;}
int mock_close(int fd){assert(fd==9);++closes;return 0;}
int mock_execve(const char* path,char*const args[],char*const env[]){assert(!strcmp(path,"/bin/sh") && !strcmp(args[1],"/tmp/a7-session.sh") && env);++execs;return -1;}
extern int k40_helper_entry(int,char**,char**);
int main(void){char* args[]={"helper",0};char* env[]={0};
result=-1;assert(k40_helper_entry(1,args,env)==1 && opens==1 && !execs);
result=3;assert(k40_helper_entry(1,args,env)==3 && opens==2 && execs==1 && !duplicates);
result=9;assert(k40_helper_entry(1,args,env)==3 && opens==3 && execs==2 && duplicates==1 && closes==1);
deny=1;assert(k40_helper_entry(1,args,env)==2 && opens==4 && execs==2 && duplicates==2 && closes==1);
return 0;}
"""
            )
            subprocess.run(
                [
                    "cc",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I" + str(root),
                    "-D_start=k40_helper_entry",
                    "-Dexecve=mock_execve",
                    "-Ddup2=mock_dup2",
                    "-Dclose=mock_close",
                    str(
                        Path(__file__).resolve().parents[1] / "tools/a7/open_session.c"
                    ),
                    str(root / "fixture.c"),
                    "-o",
                    str(root / "probe"),
                ],
                check=True,
            )
            result = subprocess.run(
                [str(root / "probe")], capture_output=True, text=True, check=True
            )
            self.assertIn("A7-OPEN-RESULT status=0xffffffff", result.stdout)

    def test_job_syntax_and_one_open_after_wait(self):
        script = guest_job.job(
            12345,
            {
                role: dict(bytes=1, sha256="0" * 64)
                for role in ("identity", "owner", "client", "helper")
            },
        )
        subprocess.run(["sh", "-n"], input=script, text=True, check=True)
        self.assertEqual(script.count("/boot/system/non-packaged/.k40-a7-open\n"), 1)
        self.assertNotIn("exec 3<>", script)
        self.assertLess(
            script.index("\nwait_a7_node\n"), script.index("echo A7-OPEN-DEVICE")
        )
        self.assertLess(
            script.index("echo K40-B5-BEGIN"), script.index("install_artifact identity")
        )
        self.assertIn("base=/boot/system/non-packaged/add-ons/kernel", script)
        self.assertIn("stage=/boot/system/non-packaged/.k40-a7-staging", script)
        self.assertNotIn("ln ", guest_job.INSTALL)
        self.assertNotIn("cp ", guest_job.INSTALL)
        self.assertIn('test "$before" = "$after"', guest_job.INSTALL)
        self.assertLess(
            script.index("install_artifact owner"),
            script.index("install_artifact client"),
        )


if __name__ == "__main__":
    unittest.main()
