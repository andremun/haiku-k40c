#!/usr/bin/env python3
"""Localhost transfer service between the host and a cardless Haiku guest.

Inputs: the work folder (--root, default the current folder). The guest reads
files from <root>/share over http://10.0.2.2:18080.
Outputs: PUT uploads. Names that start with "job" go to <root>/logs. Other names
go to --results (default <root>/results). Each upload is written to a temporary
file and renamed, so a reader never sees a partial file. An existing file in
--results with the same name is replaced, so give each run its own results
folder. A file in logs/ is written once: job.sh takes the exit status from it.
A second upload with the same bytes (a retry) is accepted, other bytes get 409.
All uploads of one server run together are at most --max-total bytes.
--port 0 takes a free port. --port-file receives the port number after the
bind, so a caller never talks to another server on a fixed port.
Prerequisites: Python 3.10 or newer. Listens on 127.0.0.1 only.

Merged on 2026-10-23 from the copies in haiku-k40c-llm and opencode-haiku
(alignment plan decision D4). Behavior equals the opencode-haiku copy, plus the
--root, --results and --port options.
"""
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.

import argparse
import os
import re
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_UPLOAD = 64 * 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


class Budget:
    """Bytes that uploads may still use in this server run (shared by the threads)."""

    def __init__(self, total):
        self.left = total
        self.lock = threading.Lock()

    def take(self, n):
        with self.lock:
            if n > self.left:
                return False
            self.left -= n
            return True


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, root, results, budget, **kwargs):
        self.root = root
        self.results = results
        self.budget = budget
        super().__init__(*args, directory=str(root / "share"), **kwargs)

    def do_PUT(self):
        name = self.path.lstrip("/")
        if not NAME.fullmatch(name):
            self.send_error(400)
            return
        try:
            n = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            self.send_error(400)
            return
        if not 0 <= n <= MAX_UPLOAD:
            self.send_error(413)
            return
        data = self.rfile.read(n)
        if len(data) != n:
            self.send_error(400, "Incomplete upload")
            return
        job = name.startswith("job")
        out = self.root / "logs" if job else self.results
        final = out / name
        if job and final.exists():
            # Write once: a retry of the same result succeeds, a different result does not.
            if final.read_bytes() == data:
                self.send_response(201)
                self.end_headers()
            else:
                self.send_error(409, "Job result already written")
            return
        if not self.budget.take(n):
            self.send_error(507, "Upload budget of this server run is used up")
            return
        out.mkdir(parents=True, exist_ok=True)
        # Readers wait on the final name: never expose a partially written result.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=out, prefix=".upload-", delete=False) as target:
                temporary = Path(target.name)
                target.write(data)
            if job:
                # link() fails when the name exists, so two parallel uploads cannot both win.
                try:
                    os.link(temporary, final)
                except FileExistsError:
                    self.send_error(409, "Job result already written")
                    return
            else:
                os.replace(temporary, final)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self.send_response(201)
        self.end_headers()

    def log_message(self, fmt, *args):
        print(time.strftime("%H:%M:%S"), fmt % args, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--results", type=Path, default=None)
    ap.add_argument("--port", type=int, default=18080, help="0 takes a free port")
    ap.add_argument("--port-file", type=Path, help="write the port number here after the bind")
    ap.add_argument("--max-total", type=int, default=4 << 30, help="bytes for all uploads of this run")
    a = ap.parse_args()
    root = a.root.resolve()
    results = (a.results or root / "results").resolve()
    handler = partial(Handler, root=root, results=results, budget=Budget(a.max_total))
    server = ThreadingHTTPServer(("127.0.0.1", a.port), handler)
    if a.port_file:
        # Rename into place: a reader never sees an empty port file.
        partial_file = a.port_file.with_name(a.port_file.name + ".partial")
        partial_file.write_text(f"{server.server_address[1]}\n")
        partial_file.replace(a.port_file)
    server.serve_forever()


if __name__ == "__main__":
    main()
