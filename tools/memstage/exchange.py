# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Fixed phase-scoped transfer service; no key or arbitrary file endpoint."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

from tools.memstage.guest_job import job

LIMITS = {
    "preflight-output.txt": 16384,
    "preflight-exit.txt": 16,
    "preflight-install.txt": 65536,
    "child-result.txt": 16,
    "memory-output.txt": 65536,
    "memory-exit.txt": 16,
    "memory-install.txt": 131072,
    "request.bin": 256,
    "job-output.txt": 131072,
    "job.exit": 16,
}
GATES = ("advance-a7", "advance-memory", "finish-ok")


def save(path, data):
    if isinstance(data, str):
        data = data.encode()
    with Path(path).open("xb") as out:
        out.write(data)


@contextmanager
def exchange(folder, evidence, suite, a7_port):
    downloads = {role: folder / role for role in suite["guest_artifacts"]}
    downloads["job.sh"] = folder / "job.sh"
    lock = threading.Lock()
    ready = {name: threading.Event() for name in (*GATES, "grant.bin", *LIMITS)}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            name = self.path[1:]
            if name in GATES:
                if not ready[name].is_set():
                    self.send_error(404)
                    return
                data = b"continue\n"
            elif name == "grant.bin":
                if not ready[name].is_set():
                    self.send_error(404)
                    return
                data = (evidence / "grant.bin").read_bytes()
            else:
                path = downloads.get(name)
                if path is None:
                    self.send_error(404)
                    return
                data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path[1:]
            try:
                size = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                self.send_error(400)
                return
            if (
                name not in LIMITS
                or not 0 < size <= LIMITS[name]
                or (name == "request.bin" and size != 256)
            ):
                self.send_error(413)
                return
            self.connection.settimeout(20)
            data = self.rfile.read(size)
            if len(data) != size:
                self.send_error(400)
                return
            with lock:
                path = evidence / name
                if path.exists():
                    code = 201 if path.read_bytes() == data else 409
                else:
                    save(path, data)
                    code = 201
                if code == 201:
                    ready[name].set()
            self.send_response(code)
            self.end_headers()

        def log_message(self, fmt, *args):
            with lock, (evidence / "http.log").open("a") as out:
                out.write(fmt % args + "\n")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    save(folder / "job.sh", job(server.server_address[1], a7_port, suite))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1], ready
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
