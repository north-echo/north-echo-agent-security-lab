#!/usr/bin/env python3
"""Serve synthetic content on host loopback until interrupted."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"approved-through-broker\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


def stop(_signum, _frame):
    raise SystemExit(0)


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
ready.write_text("ready\n", encoding="utf-8")
try:
    server.serve_forever()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
