#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serve the 720 preview. Port 8786 — do not bind 8787/8790 or start another Hub."""
from __future__ import print_function

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "ai-terminal"))

from project import SCHEMA, default_fixture, fixture_now, load_json, project_snapshot  # noqa: E402
from q10_monitor import fetch_first_snapshot, list_hub_urls, set_ui_lang  # noqa: E402

PREVIEW_PORT = 8786
INDEX = os.path.join(HERE, "index.html")


def empty_projection(note, offline=True):
    return {
        "schema": SCHEMA,
        "source_schema": "",
        "upstream": "none",
        "freshness": "不可用",
        "offline": bool(offline),
        "collected_label": "",
        "waiting": 0,
        "quota": [],
        "spend": [],
        "tasks": [],
        "attention": [],
        "note": note or "",
    }


def build_projection(opts):
    set_ui_lang("zh")
    if opts.mode == "fixture":
        snap = load_json(opts.fixture)
        return project_snapshot(snap, demo=True, source=opts.fixture, now=fixture_now(snap))
    urls = [opts.hub] if opts.hub else list_hub_urls()
    try:
        snap, url = fetch_first_snapshot(urls)
    except Exception as exc:
        return empty_projection("Aindle 不可用：{0}".format(exc), offline=True)
    model = project_snapshot(snap, source=url)
    model["upstream"] = "aindle"
    return model


def make_handler(opts):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _send(self, code, body, content_type):
            raw = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                with open(INDEX, "rb") as fh:
                    self._send(200, fh.read(), "text/html; charset=utf-8")
                return
            if path == "/projection.json":
                payload = build_projection(opts)
                text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
                self._send(200, text, "application/json; charset=utf-8")
                return
            self._send(404, "not found\n", "text/plain; charset=utf-8")

    return Handler


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Q10 Console 720 preview (no Octoooo).")
    parser.add_argument("--port", type=int, default=PREVIEW_PORT)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--lan", action="store_true", help="bind 0.0.0.0 so the phone browser can open it")
    parser.add_argument("--demo", action="store_true", help="use in-repo fixture (default)")
    parser.add_argument("--hub", nargs="?", const="", default=None, help="live Aindle; optional snapshot URL")
    parser.add_argument("--fixture", default=default_fixture())
    args = parser.parse_args(argv)
    if args.port in (8787, 8790):
        parser.error("do not bind 8787/8790")
    if args.lan:
        args.bind = "0.0.0.0"
    want_hub = args.hub is not None
    if args.hub == "":
        args.hub = None
    if want_hub and not args.demo:
        args.mode = "aindle"
    else:
        args.mode = "fixture"
    return args


def main(argv):
    opts = parse_args(argv)
    if opts.port in (8787, 8790):
        print("refuse port %s" % opts.port, file=sys.stderr)
        return 2
    httpd = ThreadingHTTPServer((opts.bind, opts.port), make_handler(opts))
    print("preview http://127.0.0.1:%s/  bind=%s  mode=%s" % (opts.port, opts.bind, opts.mode), flush=True)
    if opts.bind == "0.0.0.0":
        print("phone factory browser: http://169.254.0.2:%s/  (USB Dev Mode)" % opts.port, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstop")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
