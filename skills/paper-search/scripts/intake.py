#!/usr/bin/env python3
"""One-use local form for paper-search inputs; prints its loopback URL."""

import argparse
import html
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs
from urllib.request import urlopen


TOOLS = ("codex-research", "scite", "consensus", "semantic-scholar", "google-scholar",
         "google-scholar-labs", "scopus-ai", "pubmed", "uniprot")
DEFAULT_TOOLS = ("scite", "consensus", "semantic-scholar")
TEMPLATE = (Path(__file__).resolve().parent.parent / "assets" / "search-form.html").read_text()


def zotero_available():
    try:
        with urlopen("http://127.0.0.1:23119/api/users/0/items?format=json&limit=1", timeout=1) as response:
            return response.status == 200 and isinstance(json.load(response), list)
    except (OSError, ValueError):
        return False


def render_form(token, topic, context, selected, mode, max_papers, only_not_in_zotero=False,
                zotero_connected=False, result_mode="compare"):
    values = {
        "TOKEN": html.escape(token, quote=True),
        "TOPIC": html.escape(topic, quote=True),
        "CONTEXT": html.escape(context),
        "MAX_PAPERS": str(max_papers),
        "VISIBLE_CHECKED": "checked" if mode == "visible" else "",
        "BACKGROUND_CHECKED": "checked" if mode == "background" else "",
        "RANKED_CHECKED": "checked" if result_mode == "ranked" else "",
        "COMPARE_CHECKED": "checked" if result_mode == "compare" else "",
        "ONLY_NOT_IN_ZOTERO_CHECKED": "checked" if only_not_in_zotero else "",
        "ZOTERO_STATUS_CLASS": ("unchecked" if not only_not_in_zotero else
                                "connected" if zotero_connected else "unavailable"),
        "ZOTERO_STATUS_TEXT": ("⚪ Zotero not checked" if not only_not_in_zotero else
                               "🟢 Zotero connected — My Library accessible" if zotero_connected else
                               "🔴 Zotero unavailable — open Zotero or enable its local API"),
    }
    for tool in TOOLS:
        values[tool.upper().replace("-", "_") + "_CHECKED"] = "checked" if tool in selected else ""
    page = TEMPLATE
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)
    return page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--tools", default=",".join(DEFAULT_TOOLS))
    parser.add_argument("--mode", choices=("visible", "background"), default="visible")
    parser.add_argument("--result-mode", choices=("ranked", "compare"), default="compare")
    parser.add_argument("--max-papers", type=int, default=10)
    parser.add_argument("--only-not-in-zotero", action="store_true")
    args = parser.parse_args()
    selected = [tool.strip() for tool in args.tools.split(",") if tool.strip()]
    if not selected or any(tool not in TOOLS for tool in selected):
        parser.error("--tools must contain one or more supported tool names")
    if not 1 <= args.max_papers <= 50:
        parser.error("--max-papers must be between 1 and 50")
    token = secrets.token_urlsafe(24)
    draft = {"topic": args.topic, "context": args.context, "tools": selected,
             "tab_mode": args.mode, "result_mode": args.result_mode,
             "max_papers": args.max_papers,
             "only_not_in_zotero": args.only_not_in_zotero}
    submitted = False

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body, content_type="text/html; charset=utf-8"):
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if submitted:
                self.respond(410, "Search already submitted")
                return
            if self.path == "/zotero-status":
                self.respond(200, json.dumps({"connected": zotero_available()}),
                             "application/json; charset=utf-8")
                return
            if self.path != "/":
                self.respond(404, "Not found")
                return
            self.respond(200, render_form(token, draft["topic"], draft["context"],
                                          draft["tools"], draft["tab_mode"], draft["max_papers"],
                                          draft["only_not_in_zotero"],
                                          zotero_available() if draft["only_not_in_zotero"] else False,
                                          draft["result_mode"]))

        def do_POST(self):
            nonlocal submitted
            if submitted:
                self.respond(410, "Search already submitted")
                return
            if self.path != "/submit":
                self.respond(404, "Not found")
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 10000:
                self.respond(413, "Form too large")
                return
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            get = lambda key: fields.get(key, [""])[0].strip()
            topic = get("topic")
            context = get("context")
            tools = list(dict.fromkeys(fields.get("tools", [])))
            mode = get("tab_mode")
            result_mode = get("result_mode")
            only_not_in_zotero = get("only_not_in_zotero") == "1"
            try:
                max_papers = int(get("max_papers"))
            except ValueError:
                max_papers = 0
            if (get("token") != token or not 0 < len(topic) <= 240
                    or len(context) > 2000 or not tools
                    or any(tool not in TOOLS for tool in tools)
                    or mode not in ("visible", "background")
                    or result_mode not in ("ranked", "compare")
                    or not 1 <= max_papers <= 50):
                self.respond(400, '<p>Check the required fields and select at least one tool.</p><a href="/">Return to form</a>')
                return

            selection = {"topic": topic, "context": context, "tools": tools,
                         "tab_mode": mode, "result_mode": result_mode,
                         "max_papers": max_papers,
                         "only_not_in_zotero": only_not_in_zotero}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_name(args.output.name + ".tmp")
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(selection, handle, ensure_ascii=False)
            os.replace(temporary, args.output)
            submitted = True
            self.respond(200, '<!doctype html><meta charset="utf-8"><title></title>')
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *_):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    print(f"http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
