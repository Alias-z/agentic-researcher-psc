#!/usr/bin/env python3
"""Read Zotero notes and prepare or explicitly apply reading-note changes."""

import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


BASE = "http://127.0.0.1:23119"
DRAFT = "reading:draft"
REVIEWED = "reading:reviewed"
KEY = re.compile(r"[23456789ABCDEFGHIJKLMNPQRSTUVWXYZ]{8}\Z")


class Error(Exception):
    pass


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.links.append(href)


def plain(value):
    parser = PlainText()
    parser.feed(value or "")
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def link_targets(value):
    parser = PlainText()
    parser.feed(value or "")
    return parser.links


def item_key(value):
    if not KEY.fullmatch(value):
        raise argparse.ArgumentTypeError("Expected an eight-character Zotero item key")
    return value


def tags(data):
    return {tag["tag"] for tag in data.get("tags", [])}


def state(data):
    current = tags(data) & {DRAFT, REVIEWED}
    if len(current) > 1:
        return "conflicting-tags"
    return "reviewed" if REVIEWED in current else "draft" if DRAFT in current else "unmarked"


def with_status(data, status):
    return [tag for tag in data.get("tags", []) if tag["tag"] not in {DRAFT, REVIEWED}] + [{"tag": status}]


def summarize(item, include_note=False):
    data = item["data"]
    result = {"key": item["key"], "version": item["version"], "itemType": data["itemType"]}
    for field in ("title", "DOI", "parentItem", "contentType", "filename", "tags"):
        if field in data:
            result[field] = data[field]
    if data["itemType"] == "note":
        text = plain(data.get("note", ""))
        result.update(status=state(data), title=text.splitlines()[0] if text else "", excerpt=text[:500])
        if include_note:
            result.update(note=data.get("note", ""), text=text)
    return result


class Client:
    def __init__(self, library="/api/users/0"):
        if not re.fullmatch(r"/api/(users|groups)/\d+", library):
            raise Error("Library must be /api/users/<ID> or /api/groups/<ID>")
        self.library = library
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.server_id = None

    def request(self, path, *, method="GET", payload=None, headers=None, timeout=15):
        request_headers = {"Zotero-API-Version": "3", **(headers or {})}
        if self.server_id:
            request_headers["Zotero-Server-ID"] = self.server_id
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(BASE + path, data=body, headers=request_headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                response_headers = dict(response.headers)
                content = response.read().decode("utf-8")
                try:
                    data = json.loads(content) if content else None
                except json.JSONDecodeError:
                    data = content
                return data, response_headers
        except urllib.error.HTTPError as exc:
            hints = {401: "Write authorization is missing or expired.",
                     403: "Access or authorization was denied.",
                     404: "The item, indexed text, or endpoint was not found.",
                     412: "The Zotero instance or item version changed. Read again before writing."}
            raise Error(f"{method} {path}: HTTP {exc.code}. {hints.get(exc.code, 'Inspect Zotero before retrying.')} No automatic retry was made.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            suffix = " Check the item before retrying: the write outcome may be uncertain." if method != "GET" else " Check that Zotero is running and its local API is enabled."
            raise Error(f"{method} {path}: {type(exc).__name__}.{suffix}") from exc

    def connect(self):
        _, headers = self.request("/api/")
        lowered = {k.lower(): v for k, v in headers.items()}
        self.server_id = lowered.get("zotero-server-id")
        return {"base_url": BASE, "library": self.library,
                "zotero_version": lowered.get("x-zotero-version"),
                "server_id": self.server_id}

    def get(self, key):
        return self.request(f"{self.library}/items/{key}")[0]

    def listing(self, path, params=None):
        result, start, version = [], 0, None
        while True:
            query = urllib.parse.urlencode({**(params or {}), "format": "json", "limit": 100, "start": start})
            batch, headers = self.request(path + "?" + query)
            if not isinstance(batch, list):
                raise Error("Expected a Zotero item list")
            current_version = next((v for k, v in headers.items() if k.lower() == "last-modified-version"), None)
            if version is not None and current_version != version:
                raise Error("Library changed during pagination. Read again before writing.")
            version = current_version
            result.extend(batch)
            if len(batch) < 100:
                return result, version
            start += len(batch)

    def children(self, key):
        return self.listing(f"{self.library}/items/{key}/children")

    def authorize(self):
        if not self.server_id:
            raise Error("This Zotero instance did not provide a server ID; local writes require Zotero 10+")
        key = os.environ.get("ZOTERO_LOCAL_API_KEY")
        if key:
            return key
        print("Zotero will display an authorization dialog for Paper Reading. No key is printed or saved.", file=sys.stderr)
        data, _ = self.request("/api/local/authorize", method="POST", payload={"appName": "Paper Reading"}, timeout=55)
        if not isinstance(data, dict) or not data.get("key"):
            raise Error("Zotero did not grant write authorization")
        return data["key"]


def check_version(item, expected):
    if expected is None:
        raise Error(f"Read note {item['key']} first, then supply --version {item['version']}")
    if item["version"] != expected:
        raise Error("Note changed since it was read. Read it again and preserve the user's edits.")


def prepare_draft(client, parent, body, note_key=None, version=None):
    paper = client.get(parent)
    if paper["data"]["itemType"] in {"note", "attachment", "annotation"} or paper["data"].get("deleted"):
        raise Error("Select the live parent paper record, not a PDF, note, or trashed item")
    if not plain(body).strip():
        raise Error("The reading note is empty")
    children, library_version = client.children(parent)
    candidates = [x for x in children if x["data"]["itemType"] == "note" and tags(x["data"]) & {DRAFT, REVIEWED}]
    if len(candidates) > 1:
        raise Error("More than one reading note exists under this paper; resolve the duplicate before saving")
    existing = candidates[0] if candidates else None
    if note_key and (not existing or existing["key"] != note_key):
        raise Error("The requested note is not the managed reading note under this paper")
    if existing:
        check_version(existing, version)
        if state(existing["data"]) == "conflicting-tags":
            raise Error("The note has both draft and reviewed tags; resolve its status first")
        return {"action": "update-draft", "parent": parent, "key": existing["key"],
                "version": existing["version"], "payload": {"note": body, "tags": with_status(existing["data"], DRAFT)}}
    if version is not None:
        raise Error("A version was supplied, but no reading note exists under this paper")
    if library_version is None:
        raise Error("Zotero did not return a library version; cannot protect note creation against a concurrent change")
    return {"action": "create-draft", "parent": parent, "library_version": library_version,
            "payload": {"itemType": "note", "parentItem": parent, "note": body,
                        "tags": [{"tag": DRAFT}], "collections": [], "relations": {}}}


def prepare_review(client, key, version, approved):
    if not approved:
        raise Error("Use --user-approved only after the user explicitly approves this note")
    item = client.get(key)
    data = item["data"]
    if data["itemType"] != "note" or not data.get("parentItem") or state(data) not in {"draft", "reviewed"} or data.get("deleted"):
        raise Error("Expected a live reading note attached to a paper")
    check_version(item, version)
    return {"action": "mark-reviewed", "key": key, "parent": data["parentItem"],
            "version": item["version"], "payload": {"tags": with_status(data, REVIEWED)}}


def apply(client, plan):
    # Authorization is requested only after a valid, explicit --write operation.
    headers = {"Zotero-API-Key": client.authorize()}
    if plan["action"] == "create-draft":
        headers["If-Unmodified-Since-Version"] = str(plan["library_version"])
        response, _ = client.request(client.library + "/items", method="POST", payload=[plan["payload"]], headers=headers)
        if response.get("failed"):
            raise Error("Zotero rejected note creation: " + json.dumps(response["failed"]))
        created = response.get("successful", {}).get("0")
        key = created.get("key") if isinstance(created, dict) else None
        key = key or response.get("success", {}).get("0")
        if not key:
            raise Error("Zotero returned no new item key. Inspect the paper's children before retrying.")
    else:
        key = plan["key"]
        headers["If-Unmodified-Since-Version"] = str(plan["version"])
        client.request(f"{client.library}/items/{key}", method="PATCH", payload=plan["payload"], headers=headers)
    saved = client.get(key)
    expected = REVIEWED if plan["action"] == "mark-reviewed" else DRAFT
    if saved["data"].get("parentItem") != plan["parent"] or state(saved["data"]) != expected.split(":")[1]:
        raise Error("The write returned, but parent/status verification failed. Inspect the note before retrying.")
    if "note" in plan["payload"] and plain(saved["data"].get("note", "")) != plain(plan["payload"]["note"]):
        raise Error("The saved note text differs from the submitted draft. Inspect before retrying.")
    if "note" in plan["payload"] and link_targets(saved["data"].get("note", "")) != link_targets(plan["payload"]["note"]):
        raise Error("The saved note links differ from the submitted draft. Inspect the Markdown source link before retrying.")
    return {"applied": True, "item": summarize(saved, include_note=True)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default="/api/users/0")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    item = commands.add_parser("read", help="Read an item; paper records include their notes and attachments")
    item.add_argument("key", type=item_key)
    search = commands.add_parser("search", help="Search reading notes with their human-review status; empty query lists notes")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--collection", type=item_key)
    review_filter = search.add_mutually_exclusive_group()
    review_filter.add_argument("--reviewed-only", action="store_true")
    review_filter.add_argument("--include-drafts", action="store_true", help="Compatibility option; drafts are included by default")
    for name in ("fulltext", "file"):
        command = commands.add_parser(name)
        command.add_argument("key", type=item_key)
    draft = commands.add_parser("save-draft", help="Preview by default; --write saves a draft")
    draft.add_argument("parent", type=item_key)
    draft.add_argument("--html", type=Path, required=True)
    draft.add_argument("--note-key", type=item_key)
    draft.add_argument("--version", type=int)
    draft.add_argument("--write", action="store_true")
    review = commands.add_parser("mark-reviewed", help="Requires explicit user approval; previews unless --write")
    review.add_argument("key", type=item_key)
    review.add_argument("--version", type=int, required=True)
    review.add_argument("--user-approved", action="store_true")
    review.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    client = Client(args.library)
    connection = client.connect()
    if args.command == "status":
        result = connection
    elif args.command == "read":
        record = client.get(args.key)
        result = {"item": summarize(record, include_note=True)}
        if record["data"]["itemType"] not in {"note", "attachment", "annotation"}:
            result["children"] = [summarize(x, include_note=True) for x in client.children(args.key)[0]]
    elif args.command == "search":
        path = client.library + (f"/collections/{args.collection}/items" if args.collection else "/items")
        params = {"itemType": "note", "qmode": "everything", "q": args.query}
        if args.reviewed_only:
            params["tag"] = REVIEWED
        records, _ = client.listing(path, params)
        allowed = {"reviewed"} if args.reviewed_only else {"draft", "reviewed"}
        result = {"query": args.query, "notes": [summarize(x) for x in records
                  if x["data"]["itemType"] == "note" and x["data"].get("parentItem") and state(x["data"]) in allowed]}
    elif args.command in {"fulltext", "file"}:
        suffix = "fulltext" if args.command == "fulltext" else "file/view/url"
        result = client.request(f"{client.library}/items/{args.key}/{suffix}")[0]
    else:
        if args.command == "save-draft":
            plan = prepare_draft(client, args.parent, args.html.read_text(encoding="utf-8"), args.note_key, args.version)
        else:
            plan = prepare_review(client, args.key, args.version, args.user_approved)
        result = apply(client, plan) if args.write else {"applied": False, "plan": plan}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (Error, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
