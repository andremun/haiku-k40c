#!/usr/bin/env python3
"""Localhost transfer service between the host and a cardless Haiku guest.

Inputs: the work folder (--root, default the current folder). The guest reads
files from <root>/share over http://10.0.2.2:18080.
Outputs: PUT uploads. Names that start with "job" go to <root>/logs. Other names
go to --results (default <root>/results). Each upload is written to a temporary
file and renamed, so a reader never sees a partial file. An existing file with
the same name is replaced, so give each run its own results folder.
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
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_UPLOAD = 64 * 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, root, results, **kwargs):
        self.root = root
        self.results = results
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
        out = self.root / "logs" if name.startswith("job") else self.results
        out.mkdir(parents=True, exist_ok=True)
        # Readers wait on the final name: never expose a partially written result.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=out, prefix=".upload-", delete=False) as target:
                temporary = Path(target.name)
                target.write(data)
            os.replace(temporary, out / name)
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
    ap.add_argument("--port", type=int, default=18080)
    a = ap.parse_args()
    root = a.root.resolve()
    results = (a.results or root / "results").resolve()
    handler = partial(Handler, root=root, results=results)
    ThreadingHTTPServer(("127.0.0.1", a.port), handler).serve_forever()


if __name__ == "__main__":
    main()
