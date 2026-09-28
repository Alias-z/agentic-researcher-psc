#!/usr/bin/env python3
"""Keep a private per-source paper ledger and count Zotero-filtered candidates."""

import argparse
import json
import os
import re
import uuid
from pathlib import Path

from zotero_check import check, first_author, normalize_doi, normalize_title


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def candidate_key(candidate):
    title = str(candidate.get("title") or "").strip()
    if not title:
        raise ValueError("Every candidate needs a title")
    source_id = str(candidate.get("source_id") or "").strip()
    return source_id or normalize_title(title) + "|" + str(candidate.get("year") or "")


def validate_candidate(candidate):
    if not isinstance(candidate, dict):
        raise ValueError("Candidates must be JSON objects")
    candidate_key(candidate)
    if candidate.get("topic_fit", "uncertain") not in ("yes", "no", "uncertain"):
        raise ValueError("topic_fit must be yes, no, or uncertain")
    if "doi_verified" in candidate and not isinstance(candidate["doi_verified"], bool):
        raise ValueError("doi_verified must be a boolean")
    if candidate.get("doi_verified") and not re.match(
            r"^10\.\d{4,9}/\S+$", normalize_doi(candidate.get("doi"))):
        raise ValueError("A verified DOI must have a DOI-shaped value")


def merge_batch(ledger, batch):
    records = {record["key"]: record for record in ledger["records"]}
    for candidate in batch:
        validate_candidate(candidate)
        key = candidate_key(candidate)
        record = records.setdefault(key, {"key": key, "topic_fit": "uncertain",
                                          "doi_verified": False})
        new_doi = str(candidate.get("doi") or "").strip()
        if new_doi and new_doi != str(record.get("doi") or "").strip():
            record["doi_verified"] = False
        for field, value in candidate.items():
            if field == "doi_verified" and value is False and record.get("doi_verified"):
                continue
            if field == "topic_fit" and value == "uncertain" and record["topic_fit"] != "uncertain":
                continue
            if value is not None and value != "":
                record[field] = value
    ledger["records"] = list(records.values())


def update_statuses(ledger, index):
    if index is None:
        for record in ledger["records"]:
            record["zotero_status"] = "unchecked"
            record["zotero_item_keys"] = []
        return
    candidates = [
        {"title": record["title"],
         "doi": record.get("doi", "") if record.get("doi_verified") else "",
         "authors": record.get("authors", ""),
         "first_author": record.get("first_author", ""),
         "year": record.get("year", ""),
         "journal": record.get("journal", "")}
        for record in ledger["records"]
    ]
    for record, match in zip(ledger["records"], check(candidates, index)):
        record["zotero_status"] = match["status"]
        record["zotero_item_keys"] = match["item_keys"]
        record["zotero_reason"] = match["reason"]
        record["zotero_title_matches"] = match["title_matches"]


def coverage(records):
    """Partition source records into exclusive buckets; cross-source overlap is separate."""
    counts = {key: 0 for key in (
        "repeated_doi", "off_topic", "topic_unclear", "in_zotero",
        "absent", "title_review", "doi_pending", "zotero_unchecked")}
    seen_dois = set()
    for record in records:
        doi = normalize_doi(record.get("doi")) if record.get("doi_verified") else ""
        if doi and doi in seen_dois:
            bucket = "repeated_doi"
        elif record.get("topic_fit") == "no":
            bucket = "off_topic"
        elif record.get("topic_fit") != "yes":
            bucket = "topic_unclear"
        else:
            status = record.get("zotero_status", "unchecked")
            bucket = {"in_zotero": "in_zotero", "not_found": "absent",
                      "possible_match": "title_review", "unchecked": "zotero_unchecked"}.get(
                          status, "doi_pending")
        counts[bucket] += 1
        if doi:
            seen_dois.add(doi)
    return {"screened_records": len(records), "categories": counts}


def progress(ledger):
    records = ledger["records"]
    eligible = [r for r in records if r.get("topic_fit") == "yes"]
    def count_status(status):
        keys = set()
        for record in eligible:
            if record["zotero_status"] == status:
                doi = normalize_doi(record.get("doi")) if record.get("doi_verified") else ""
                key = "doi:" + doi if doi else (
                    "title:" + normalize_title(record.get("title")) + "|"
                    + str(record.get("year") or ""))
                keys.add(key)
        return len(keys)

    def unique_verified(rows):
        papers = {}
        for record in rows:
            doi = normalize_doi(record.get("doi")) if record.get("doi_verified") else ""
            if doi:
                papers.setdefault(doi, record)
        return list(papers.values())

    absent = unique_verified(r for r in eligible if r["zotero_status"] == "not_found")
    target = ledger["max_papers"] + int(ledger["only_not_in_zotero"])
    verified = unique_verified(eligible)
    seen_papers = set()
    source_count = 0
    for record in eligible:
        title_key = ("title:" + normalize_title(record.get("title")) + "|"
                     + str(record.get("year") or "") + "|"
                     + first_author(record.get("first_author") or record.get("authors")))
        doi = normalize_doi(record.get("doi")) if record.get("doi_verified") else ""
        keys = {title_key, "doi:" + doi} if doi else {title_key}
        if not keys.intersection(seen_papers):
            source_count += 1
        seen_papers.update(keys)
    count = len(absent) if ledger["only_not_in_zotero"] else source_count
    return {
        "source": ledger["source"], "target": target, "target_reached": count >= target,
        "source_records_seen": len(records), "topic_eligible": len(eligible),
        "verified_doi": len(verified), "confirmed_absent": len(absent),
        "count_toward_target": count, "zotero_checked": ledger["zotero_checked"],
        "in_zotero": count_status("in_zotero"),
        "possible_match": count_status("possible_match"),
        "needs_doi": [r["key"] for r in eligible if ledger["only_not_in_zotero"]
                      and not r.get("doi_verified")
                      and r["zotero_status"] != "possible_match"
                      and r["zotero_status"] != "in_zotero"],
        "uncertain_topic": sum(r.get("topic_fit") == "uncertain" for r in records),
        "coverage": coverage(records),
        "title_matches_to_review": [
            {"key": r["key"], "reason": r.get("zotero_reason", "Title match needs review"),
             "matches": r.get("zotero_title_matches", [])}
            for r in eligible if r.get("zotero_status") == "possible_match"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--input", required=True, type=Path,
                        help="Small JSON array of result-card candidates or DOI updates")
    parser.add_argument("--max-papers", required=True, type=int)
    parser.add_argument("--only-not-in-zotero", action="store_true")
    args = parser.parse_args()
    if args.max_papers < 1:
        parser.error("--max-papers must be positive")
    if args.only_not_in_zotero and not args.snapshot:
        parser.error("Zotero exclusion requires --snapshot")
    index = read_json(args.snapshot) if args.snapshot else None
    if args.snapshot and (not isinstance(index, dict)
                          or index.get("scope") != "Zotero My Library"
                          or not isinstance(index.get("by_doi"), dict)
                          or not isinstance(index.get("by_title"), dict)):
        parser.error("--snapshot is not a Zotero My Library index")
    batch = read_json(args.input)
    if not isinstance(batch, list):
        parser.error("--input must be a JSON array")
    if args.ledger.exists():
        ledger = read_json(args.ledger)
        if (ledger.get("source") != args.source
                or ledger.get("max_papers") != args.max_papers
                or ledger.get("only_not_in_zotero") != args.only_not_in_zotero
                or ledger.get("zotero_checked") != bool(args.snapshot)):
            parser.error("Ledger source or search settings changed")
    else:
        ledger = {"source": args.source, "max_papers": args.max_papers,
                  "only_not_in_zotero": args.only_not_in_zotero,
                  "zotero_checked": bool(args.snapshot), "records": []}
    merge_batch(ledger, batch)
    update_statuses(ledger, index)
    write_private_json(args.ledger, ledger)
    print(json.dumps(progress(ledger), ensure_ascii=False))


if __name__ == "__main__":
    main()
