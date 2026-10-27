#!/usr/bin/env python3
"""Offline tests of the shared VM tools in tools/haiku/ (no QEMU, no guest).

Covers: transfer server upload routing, name and size checks, atomic writes,
write-once job logs, the upload budget, the port file and share serving; job.sh
request, result and exit-status handling; app_vm.py key mapping, the monitor
socket folder and the read-only monitor allowlist.
Run from the repository root: python3 tests/test_vm_tools.py
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import importlib.util
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools/haiku"
checks = 0
failures = 0


def check(condition, what):
    global checks, failures
    checks += 1
    if not condition:
        failures += 1
        print("FAIL:", what)


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def put(port, name, data):
    request = urllib.request.Request(f"http://127.0.0.1:{port}/{name}", data=data, method="PUT")
    try:
        return urllib.request.urlopen(request, timeout=5).status
    except urllib.error.HTTPError as exc:
        return exc.code


def test_transfer_server(tmp):
    root = tmp / "work"
    (root / "share").mkdir(parents=True)
    (root / "share/hello.txt").write_text("hello\n")
    results = root / "results/20261023-test"
    port_file = tmp / "port"
    proc = subprocess.Popen([sys.executable, str(TOOLS / "transfer_server.py"), "--root", str(root),
                             "--results", str(results), "--port", "0", "--port-file", str(port_file),
                             "--max-total", "100"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # fmt: skip
    try:
        for _ in range(50):
            if port_file.exists():
                break
            time.sleep(0.1)
        port = int(port_file.read_text())
        check(port > 0, "--port 0 takes a free port and writes it to --port-file")
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/hello.txt", timeout=5).read()
        check(body == b"hello\n", "share/ files are served")
        check(put(port, "guest-run.log", b"abc") == 201, "a valid upload is accepted")
        check((results / "guest-run.log").read_bytes() == b"abc", "a result goes to the results folder")
        check(put(port, "job7.out", b"exit=0\n") == 201, "a job upload is accepted")
        check((root / "logs/job7.out").read_text() == "exit=0\n", "a job upload goes to logs/")
        check(put(port, "job7.out", b"exit=0\n") == 201, "a retry with the same job result is accepted")
        check(put(port, "job7.out", b"exit=1\n") == 409, "a different job result is refused")
        check((root / "logs/job7.out").read_text() == "exit=0\n", "the first job result stays")
        check(put(port, "big.log", b"x" * 95) == 507, "an upload over the budget is refused")
        check(not (results / "big.log").exists(), "a refused upload writes nothing")
        check(put(port, "../escape", b"x") in (400, 404), "a path outside the folder is refused")
        check(put(port, ".hidden", b"x") == 400, "a name that starts with a dot is refused")
        check(not list(results.glob(".upload-*")), "no temporary file is left")
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_job_runner(tmp):
    root = tmp / "jobs"
    env = {**os.environ, "HAIKU_JOB_ROOT": str(root)}
    job = str(TOOLS / "job.sh")

    def answer(n, text, delay=0.5):
        def write():
            time.sleep(delay)
            (root / "logs").mkdir(parents=True, exist_ok=True)
            (root / "logs" / f"job{n}.out").write_text(text)
        threading.Thread(target=write).start()

    answer(1, "output\nexit=3\n")
    r = subprocess.run(["sh", job, "1", "echo hi", "10"], env=env, capture_output=True, text=True)
    check(r.returncode == 3, "the guest exit status is the exit status")
    check((root / "share/job1.sh").read_text() == "echo hi\n", "the request is written to share/")
    r = subprocess.run(["sh", job, "1", "echo again", "10"], env=env, capture_output=True, text=True)
    check(r.returncode == 2, "a used job number is refused")
    answer(2, "no status line\n")
    r = subprocess.run(["sh", job, "2", "true", "10"], env=env, capture_output=True, text=True)
    check(r.returncode == 125, "a result without a status line fails")
    r = subprocess.run(["sh", job, "3", "true", "1"], env=env, capture_output=True, text=True)
    check(r.returncode == 124, "a wait timeout returns 124")
    r = subprocess.run(["sh", job, "04", "true"], env=env, capture_output=True, text=True)
    check(r.returncode == 2, "a non-canonical job number is refused")


def test_app_vm(tmp):
    os.environ["HAIKU_PERSISTENT_VM_DIR"] = str(tmp / "vm")
    app_vm = load("app_vm")
    check(app_vm.VM == tmp / "vm", "the VM folder comes from HAIKU_PERSISTENT_VM_DIR")
    check(app_vm.SOCKET.parent == tmp / "vm", "the monitor socket is in the VM folder, not in /tmp")
    check(app_vm.key("A") == "shift-a" and app_vm.key("_") == "shift-minus", "key mapping")
    try:
        app_vm.key("\u00e9")
        check(False, "a non-ASCII key is refused")
    except ValueError:
        check(True, "a non-ASCII key is refused")
    check("quit" not in app_vm.READ_ONLY_COMMANDS, "quit is not a read-only command")
    check(all(c.startswith("info ") for c in app_vm.READ_ONLY_COMMANDS), "only info commands")


def test_cardless_probe_result():
    runner = load("cardless_run")
    check(not runner.probe_complete("Welcome to kernel debugger output!\n"), "normal banner is not completion")
    check(runner.probe_complete("k40_os: PASS native memory\nK40-CARDLESS-END\n"), "completed native probe passes")
    for transcript in ("K40-CARDLESS-END\n", "k40_os: FAIL status -1\n",
                       "k40_os: FAIL first load\nk40_os: PASS second load\nK40-CARDLESS-END\n",
                       "k40_os: PASS\ncleanup failed\nK40-CARDLESS-END\n"):
        try:
            runner.probe_complete(transcript)
            check(False, "a failed or incomplete probe must not pass")
        except RuntimeError:
            check(True, "a failed or incomplete probe is rejected")


def main():
    with tempfile.TemporaryDirectory(prefix="vm_tools_") as name:
        tmp = Path(name)
        test_transfer_server(tmp)
        test_job_runner(tmp)
        test_app_vm(tmp)
        test_cardless_probe_result()
    print(f"test_vm_tools.py: {checks} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
