#!/usr/bin/env python3
"""Probe Zotero desktop directly; no library writes, preference edits, or plugins."""

import argparse
import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


BASE = "http://127.0.0.1:23119"


def probe(opener, path, post=False, timeout=3):
    headers = {"Zotero-API-Version": "3"}
    if path.startswith("/connector/"):
        headers["X-Zotero-Connector-API-Version"] = "3"
    if post:
        headers["Content-Type"] = "application/json"
    request = Request(BASE + path, data=b"{}" if post else None, headers=headers)
    try:
        with opener.open(request, timeout=timeout) as response:
            version = response.headers.get("X-Zotero-Version")
            try:
                body = json.load(response)
            except (ValueError, UnicodeError):
                return {"status": "unexpected_response", "http_status": response.status,
                        "zotero_version": version}, None
            return {"status": "ok", "http_status": response.status,
                    "zotero_version": version}, body
    except HTTPError as error:
        status = {403: "access_denied", 404: "endpoint_unavailable"}.get(error.code, "http_error")
        return {"status": status, "http_status": error.code,
                "zotero_version": error.headers.get("X-Zotero-Version")}, None
    except (URLError, OSError) as error:
        cause = getattr(error, "reason", error)
        status = ("connection_refused" if isinstance(cause, ConnectionRefusedError) else
                  "timeout" if isinstance(cause, (TimeoutError, socket.timeout)) else
                  "transport_error")
        return {"status": status, "http_status": None, "detail": str(cause)}, None


def check(collection=None, library="/api/users/0", parent=None, opener=None):
    # Loopback traffic must not go through a machine's HTTP proxy.
    opener = opener or build_opener(ProxyHandler({}))
    connector, ping = probe(opener, "/connector/ping", post=True)
    local_api, collections = probe(opener, library + "/collections?format=json")
    selected, target = probe(opener, "/connector/getSelectedCollection", post=True)

    if connector["status"] == "ok" and not isinstance(ping, dict):
        connector["status"] = "unexpected_response"
    valid_collections = isinstance(collections, list) and all(
        isinstance(item, dict) and item.get("key") and isinstance(item.get("data"), dict)
        for item in collections)
    if local_api["status"] == "ok" and not valid_collections:
        local_api["status"] = "unexpected_response"
    valid_target = isinstance(target, dict) and "editable" in target and "libraryID" in target
    if selected["status"] == "ok" and not valid_target:
        selected["status"] = "unexpected_response"

    result = {
        "base_url": BASE,
        "connector_server": connector,
        "local_library_api": dict(local_api, library_prefix=library),
        "selected_target": selected,
        "local_checks_passed": all(row["status"] == "ok" for row in (connector, local_api, selected)),
        "browser_extension": "not_checked",
        "computer_use": "not_checked",
    }
    if valid_target:
        selected.update({
            "name": target.get("name"), "internal_id": target.get("id"),
            "library_name": target.get("libraryName"), "internal_library_id": target.get("libraryID"),
            "editable": target.get("editable"), "files_editable": target.get("filesEditable"),
        })
    if valid_collections:
        result["local_library_api"]["collection_count"] = len(collections)
    if collection is not None:
        matches = []
        if valid_collections:
            matches = [item for item in collections if str(item["data"].get("name", "")).casefold() == collection.casefold()
                       and (parent is None or (item["data"].get("parentCollection") or "") == parent)]
        result["destination"] = {
            "name": collection,
            "status": ("unknown" if not valid_collections else "missing" if not matches else
                       "ambiguous" if len(matches) > 1 else "found"),
            "matches": [{"key": item["key"], "name": item["data"]["name"],
                         "parent_key": item["data"].get("parentCollection") or None,
                         "library_name": item.get("library", {}).get("name")}
                        for item in matches],
            "selected_name_matches": str(target.get("name", "")).casefold() == collection.casefold() if valid_target else None,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", help="Exact requested collection name")
    parser.add_argument("--library", default="/api/users/0", help="Local library API prefix")
    parser.add_argument("--parent-key", help="Parent collection key; use an empty string for top level")
    args = parser.parse_args()
    if not re.fullmatch(r"/api/(?:users/0|groups/[1-9]\d*)", args.library):
        parser.error("--library must be /api/users/0 or /api/groups/<numeric group ID>")
    print(json.dumps(check(args.collection, args.library, args.parent_key), ensure_ascii=False))


if __name__ == "__main__":
    main()
