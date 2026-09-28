#!/usr/bin/env python3
"""Build per-source paper lists from search ledgers."""

import argparse
import json
from pathlib import Path

from zotero_check import first_author, normalize_doi, normalize_title


def source_rank(record):
    try:
        return int(record.get("source_rank"))
    except (TypeError, ValueError):
        return 10**9


def included(record, only_not_in_zotero):
    return (record.get("topic_fit") == "yes"
            and (not only_not_in_zotero or
                 (record.get("doi_verified") is True
                  and bool(normalize_doi(record.get("doi")))
                  and record.get("zotero_status") == "not_found")))


def paper_keys(record):
    doi = normalize_doi(record.get("doi")) if record.get("doi_verified") else ""
    title = ("title:" + normalize_title(record.get("title")) + "|"
             + str(record.get("year") or "") + "|"
             + first_author(record.get("first_author") or record.get("authors")))
    return {title, "doi:" + doi} if doi else {title}


def build_comparison(ledgers, max_papers, only_not_in_zotero):
    limit = max_papers + int(only_not_in_zotero)
    sources = []
    for ledger in ledgers:
        if (ledger.get("max_papers") != max_papers
                or ledger.get("only_not_in_zotero") != only_not_in_zotero):
            raise ValueError("All ledgers must use the same paper limit and Zotero option")
        source = ledger.get("source")
        records = ledger.get("records")
        if not isinstance(source, str) or not isinstance(records, list):
            raise ValueError("Invalid source ledger")
        eligible = sorted((record for record in records
                           if included(record, only_not_in_zotero)), key=source_rank)
        qualified = []
        seen_papers = set()
        for record in eligible:
            keys = paper_keys(record)
            if not keys.intersection(seen_papers):
                qualified.append(record)
            seen_papers.update(keys)
        shown = qualified[:limit]
        results = [{"title": record["title"],
                    "doi": normalize_doi(record.get("doi")) if record.get("doi_verified") else "",
                    "authors": record.get("authors", ""),
                    "year": record.get("year", ""),
                    "source_rank": record.get("source_rank"),
                    "source_url": record.get("source_url") or record.get("source_id", ""),
                    "snippet": record.get("snippet", ""),
                    "zotero_status": record.get("zotero_status", "unchecked")}
                   for record in shown]
        sources.append({"tool": source, "shown": len(results),
                        "shortfall": max(0, limit - len(qualified)),
                        "results": results})

    return {"mode": "compare", "per_tool_limit": limit, "sources": sources}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, action="append", required=True,
                        help="One per-source ledger path; repeat for every searched tool")
    parser.add_argument("--max-papers", type=int, required=True)
    parser.add_argument("--only-not-in-zotero", action="store_true")
    args = parser.parse_args()
    if args.max_papers < 1:
        parser.error("--max-papers must be positive")
    ledgers = [json.loads(path.read_text(encoding="utf-8")) for path in args.ledger]
    names = [ledger.get("source") for ledger in ledgers]
    if len(names) != len(set(names)):
        parser.error("Each source needs one ledger")
    print(json.dumps(build_comparison(ledgers, args.max_papers,
                                      args.only_not_in_zotero), ensure_ascii=False))


if __name__ == "__main__":
    main()
