#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Serialize Haiku guest starts and refuse existing QEMU guests.

Reads the host process inventory and takes a lock in the persistent VM folder.
Writes only the lock file. Requires Linux /proc and user-owned VM storage.
"""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import select
import signal
import subprocess
import sys


def refuse_running_guest(proc=Path("/proc")):
    """Refuse any live QEMU system guest, including legacy launchers."""
    for folder in sorted(proc.glob("[0-9]*")):
        try:
            name = (folder / "comm").read_text().strip()
        except (FileNotFoundError, ProcessLookupError):
            continue
        if name.startswith("qemu-system"):
            raise ValueError("a QEMU guest is running (PID " + folder.name + ")")


@contextmanager
def guest_lock(vm):
    """Hold the common lock until the guest exits."""
    vm.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW
    fd = os.open(vm / ".guest.lock", flags, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another Haiku guest holds the launch lock") from exc
        refuse_running_guest()
        yield fd
    finally:
        os.close(fd)


@contextmanager
def deadline(process, seconds, record):
    """Kill the exact guest on deadline or launcher death, without PID reuse."""
    fd = os.pidfd_open(process.pid)
    watcher = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--watch",
         str(fd), str(seconds), str(record)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, pass_fds=(fd,),
    )
    os.close(fd)
    try:
        ready, _, _ = select.select([watcher.stdout], [], [], 3)
        if not ready or watcher.stdout.readline() != b"ready\n":
            process.kill()
            process.wait(timeout=5)
            raise RuntimeError("host watchdog did not start")
        yield
    finally:
        try:
            watcher.stdin.write(b"done")
            watcher.stdin.flush()
            watcher.stdin.close()
        except BrokenPipeError:
            try:
                watcher.stdin.close()
            except BrokenPipeError:
                pass
        watcher.wait(timeout=5)
        watcher.stdout.close()


def watch(fd, seconds, record):
    """Watch the launcher's pipe in an independent host process."""
    try:
        os.write(sys.stdout.fileno(), b"ready\n")
    except BrokenPipeError:
        pass
    ready, _, _ = select.select([sys.stdin.buffer], [], [], seconds)
    if ready and sys.stdin.buffer.read(4) == b"done":
        return
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("launcher exited\n" if ready else "deadline expired\n")
    try:
        signal.pidfd_send_signal(fd, signal.SIGKILL)
    except ProcessLookupError:
        pass


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "--watch":
        raise SystemExit("internal watchdog: --watch PIDFD SECONDS RECORD")
    watch(int(sys.argv[2]), float(sys.argv[3]), Path(sys.argv[4]))
