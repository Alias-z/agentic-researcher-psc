#!/usr/bin/env python3
"""Snapshot Zotero My Library once, then compare candidate papers locally."""

import argparse
import json
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen


BASE = "http://127.0.0.1:23119/api/users/0/items"


def normalize_doi(value):
    value = unquote(str(value or "")).strip().lower()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip(".,; ")


def normalize_title(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"\w+", value))


def normalize_year(value):
    match = re.search(r"(?:19|20)\d{2}", str(value or ""))
    return match.group(0) if match else ""


def first_author(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("lastName") or value.get("name") or ""
    value = re.split(r"\bet\s+al\b|;|\band\b|&", str(value or ""), maxsplit=1,
                     flags=re.IGNORECASE)[0].strip()
    first = value.split(",", 1)[0].strip()
    words = re.findall(r"\w+", unicodedata.normalize("NFKC", first).casefold())
    if not words:
        return ""
    return words[0] if len(words) == 1 or ("," in value and len(words) == 1) else words[-1]


def item_first_author(data):
    creators = data.get("creators") or []
    authors = [creator for creator in creators if creator.get("creatorType") == "author"]
    return first_author(authors[0]) if authors else ""


def item_journal(data):
    return data.get("publicationTitle") or data.get("proceedingsTitle") or ""


def item_doi(data):
    doi = normalize_doi(data.get("DOI"))
    if doi:
        return doi
    match = re.search(r"(?im)^\s*doi:\s*(\S+)", data.get("extra") or "")
    return normalize_doi(match.group(1)) if match else ""


def fetch_library():
    items = []
    limit = 100
    for start in range(0, 1000000, limit):
        query = urlencode({"format": "json", "itemType": "-attachment", "limit": limit,
                           "start": start})
        request = Request(BASE + "?" + query, headers={"Zotero-API-Version": "3"})
        with urlopen(request, timeout=5) as response:
            page = json.load(response)
            total = int(response.headers["Total-Results"])
        if not isinstance(page, list):
            raise ValueError("Zotero returned an unexpected item list")
        items.extend(page)
        if len(items) >= total:
            return items
        if not page:
            raise ValueError("Zotero returned an incomplete item list")
    raise ValueError("Zotero library exceeded the scan limit")


def build_index(items):
    by_doi = {}
    by_title = {}
    items_by_key = {}
    for item in items:
        data = item.get("data") or {}
        key = item.get("key") or data.get("key")
        if not key:
            continue
        items_by_key[key] = {"title": data.get("title") or "",
                             "first_author": item_first_author(data),
                             "year": normalize_year(data.get("date")),
                             "journal": item_journal(data),
                             "doi": item_doi(data)}
        if doi := item_doi(data):
            by_doi.setdefault(doi, []).append(key)
        if title := normalize_title(data.get("title")):
            by_title.setdefault(title, []).append(key)
    return {"scope": "Zotero My Library", "items_checked": len(items),
            "by_doi": by_doi, "by_title": by_title,
            "items_by_key": items_by_key}


def review_title_match(candidate, item):
    fields = {
        "first_author": (first_author(candidate.get("first_author") or candidate.get("authors")),
                         first_author(item.get("first_author"))),
        "year": (normalize_year(candidate.get("year")), normalize_year(item.get("year"))),
        "journal": (normalize_title(candidate.get("journal")),
                    normalize_title(item.get("journal"))),
    }
    comparison = {field: ("missing" if not left or not right else
                          "match" if left == right else "conflict")
                  for field, (left, right) in fields.items()}
    candidate_doi = normalize_doi(candidate.get("doi"))
    item_doi_value = normalize_doi(item.get("doi"))
    if candidate_doi and item_doi_value and candidate_doi != item_doi_value:
        comparison["doi"] = "conflict"
    return comparison


def check(candidates, index):
    by_doi = index["by_doi"]
    by_title = index["by_title"]
    items_by_key = index.get("items_by_key", {})
    results = []
    for candidate in candidates:
        doi = normalize_doi(candidate.get("doi"))
        title = normalize_title(candidate.get("title"))
        comparisons = []
        if doi and doi in by_doi:
            status, keys = "in_zotero", by_doi[doi]
            reason = "Exact DOI match"
        elif title and title in by_title:
            keys = by_title[title]
            comparisons = [{"item_key": key,
                            "fields": review_title_match(candidate, items_by_key.get(key, {})),
                            "item": items_by_key.get(key, {})} for key in keys]
            confirmed = [row for row in comparisons
                         if all(value == "match" for value in row["fields"].values())]
            if confirmed:
                status, keys = "in_zotero", [row["item_key"] for row in confirmed]
                reason = "Exact title with matching first author, year, and journal"
            else:
                status = "possible_match"
                conflicts = sorted({field for row in comparisons for field, value in row["fields"].items()
                                    if value == "conflict"})
                missing = sorted({field for row in comparisons for field, value in row["fields"].items()
                                  if value == "missing"})
                reason = ("Title match needs review: "
                          + ("conflicting " + ", ".join(conflicts) if conflicts else "")
                          + ("; " if conflicts and missing else "")
                          + ("missing " + ", ".join(missing) if missing else ""))
        elif doi:
            status, keys = "not_found", []
            reason = "DOI and exact title absent from this My Library snapshot"
        else:
            status, keys = "unknown", []
            reason = "No verified DOI or exact title match; absence cannot be confirmed"
        results.append({"doi": candidate.get("doi", ""), "title": candidate.get("title", ""),
                        "status": status, "item_keys": keys,
                        "reason": reason, "title_matches": comparisons})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        help="JSON array of candidate objects with doi and title fields")
    parser.add_argument("--snapshot", type=Path,
                        help="Create this private library index, or reuse it with --input")
    args = parser.parse_args()
    if not args.input and not args.snapshot:
        parser.error("provide --snapshot to scan My Library or --input to check candidates")
    try:
        if args.snapshot and not args.input:
            index = build_index(fetch_library())
            args.snapshot.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(args.snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(index, handle, ensure_ascii=False)
            result = {"accessible": True, "scope": index["scope"],
                      "items_checked": index["items_checked"], "snapshot_created": True,
                      "results": []}
        else:
            candidates = json.loads(args.input.read_text(encoding="utf-8"))
            if not isinstance(candidates, list) or any(not isinstance(c, dict) for c in candidates):
                parser.error("--input must contain a JSON array of candidate objects")
            index = (json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot
                     else build_index(fetch_library()))
            if (not isinstance(index, dict)
                    or index.get("scope") != "Zotero My Library"
                    or not isinstance(index.get("by_doi"), dict)
                    or not isinstance(index.get("by_title"), dict)):
                raise ValueError("Invalid Zotero My Library snapshot")
            result = {"accessible": True, "scope": index["scope"],
                      "items_checked": index["items_checked"],
                      "results": check(candidates, index)}
    except (OSError, ValueError, TypeError, KeyError) as error:
        result = {"accessible": False, "scope": "Zotero My Library",
                  "error": str(error), "results": []}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
