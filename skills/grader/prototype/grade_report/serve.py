#!/usr/bin/env python3
"""PROTOTYPE — throwaway static server for grade_report UI variants."""
from __future__ import annotations

import functools
import http.server
import os
import socketserver
import webbrowser

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)


def main() -> None:
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/?variant=A"
        print(f"PROTOTYPE grade_report UI -> {url}")
        print("Ctrl+C to stop. Throwaway — not production.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()


if __name__ == "__main__":
    main()
