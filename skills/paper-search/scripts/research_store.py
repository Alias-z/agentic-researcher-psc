#!/usr/bin/env python3
"""Durable, project-scoped search artifacts and human-reviewed research context.

Standard library only. This helper never contacts a search provider or Zotero.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

SOURCES = ("codex-research", "scite", "consensus", "semantic-scholar", "google-scholar",
           "google-scholar-labs", "scopus-ai", "pubmed", "uniprot")
MANIFEST = "research.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def project_path(path):
    path = Path(path).expanduser().resolve()
    return path.parent if path.name == MANIFEST else path


def load(path):
    project = project_path(path)
    data = read_json(project / MANIFEST)
    if data.get("schema_version") != 1 or not data.get("topic") or not data.get("id"):
        raise ValueError("Not a supported research project")
    return project, data


@contextmanager
def locked(project):
    """Fail rather than lose another search's concurrent update."""
    project = project_path(project)
    project.mkdir(parents=True, exist_ok=True)
    lock = project / ".research.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("Another update holds .research.lock; retry after it finishes") from None
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def save(project, data):
    data["revision"] = data.get("revision", 0) + 1
    data["updated_at"] = now()
    write_json(project / MANIFEST, data)


def discover(workspace):
    """Look only in the supplied workspace, never crawl a user's home or library."""
    root = project_path(workspace)
    paths = [root / MANIFEST] if (root / MANIFEST).is_file() else []
    paths.extend(sorted((root / "research").glob("*/research.json")))
    results = []
    for path in paths:
        project, data = load(path)
        results.append({"project": str(project), "topic": data["topic"], "id": data["id"],
                        "updated_at": data.get("updated_at"),
                        "has_search": bool(data.get("search")),
                        "has_reviewed_context": bool(data.get("context", {}).get("reviewed_sha256"))})
    return results


def initialize(workspace, topic):
    topic = topic.strip()
    if not topic:
        raise ValueError("A research topic is required")
    workspace = Path(workspace).expanduser().resolve()
    for existing in discover(workspace):
        if existing["topic"].casefold() == topic.casefold():
            return Path(existing["project"])
    slug = re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")[:55] or "topic"
    project = workspace / "research" / (slug + "-" + digest(topic)[:8])
    with locked(project):
        if not (project / MANIFEST).exists():
            save(project, {"schema_version": 1, "id": uuid.uuid4().hex, "topic": topic,
                           "created_at": now(), "preferences": {}, "context": {},
                           "notes": [], "known_papers": []})
    return project


def text_key(value):
    return " ".join(re.findall(r"\w+", str(value or "").casefold()))


def doi(record):
    if not record.get("doi_verified"):
        return ""
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "",
                   str(record.get("doi") or "").strip(), flags=re.I).lower().rstrip(".,; ")
    return value if re.fullmatch(r"10\.\d{4,9}/\S+", value) else ""


def family(record):
    if record.get("first_author"):
        return text_key(record["first_author"])
    value = record.get("authors") or ""
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        return text_key(value.get("family") or value.get("lastName"))
    value = re.split(r"\bet\s+al\b|;|\band\b|&", str(value), maxsplit=1, flags=re.I)[0]
    if "," in value:
        value = value.split(",", 1)[0]
    words = [w for w in value.split() if not re.fullmatch(r"(?:[A-Z]\.?){1,4}", w)]
    return text_key(words[-1] if words else value)


def same_paper(left, right):
    a, b = doi(left), doi(right)
    if a and b:
        return a == b  # A conflicting DOI must not collapse to an equal title.
    if left.get("pmid") and str(left["pmid"]) == str(right.get("pmid", "")):
        return True
    if (left.get("source_id") and left["source_id"] == right.get("source_id")
            and (str(left["source_id"]).startswith("https://")
                 or left.get("source") and left.get("source") == right.get("source"))):
        return True
    return bool(text_key(left.get("title")) and text_key(left.get("title")) == text_key(right.get("title"))
                and left.get("year") and str(left["year"]) == str(right.get("year", ""))
                and family(left) and family(left) == family(right))


def identity(record):
    return {key: record[key] for key in ("title", "authors", "first_author", "year", "doi",
            "doi_verified", "source_id", "source", "pmid") if key in record}


def unique(records):
    out = []
    for record in records:
        if not any(same_paper(record, other) for other in out):
            out.append(record)
    return out


def validate_options(options, topic):
    if options.get("topic", topic).strip() != topic:
        raise ValueError("Topic changed; select or create the correct research project")
    selected = options.get("tools")
    if not isinstance(selected, list) or not selected or any(t not in SOURCES for t in selected):
        raise ValueError("Supply the actual selected search tools")
    limit = options.get("max_papers")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("max_papers must be 1–50")
    if options.get("tab_mode") not in ("visible", "background"):
        raise ValueError("Supply the selected tab mode")
    if options.get("result_mode") not in ("compare", "ranked"):
        raise ValueError("Supply the selected result mode")
    if not isinstance(options.get("only_not_in_zotero"), bool):
        raise ValueError("Supply the selected Zotero exclusion option")
    return {**options, "topic": topic, "tools": list(dict.fromkeys(selected))}


def record_search(project, options, queries, papers, markdown, stage="search"):
    if stage not in ("compare", "refine", "search"):
        raise ValueError("Unknown search stage")
    with locked(project):
        project, data = load(project)
        options = validate_options(options, data["topic"])
        if not isinstance(queries, list) or not queries:
            raise ValueError("Save the actual queries, not an invented strategy")
        for q in queries:
            if q.get("source") not in options["tools"] or not str(q.get("query", "")).strip():
                raise ValueError("Each query needs a selected source and its actual search text")
        if not isinstance(papers, list) or any(not p.get("title") for p in papers):
            raise ValueError("papers must contain the records actually shown to the user")
        prefix = "comparison" if stage == "compare" else "search-results"
        artifact = {"created_at": now(), "stage": stage, "options": options,
                    "queries": queries, "papers": papers}
        write_json(project / (prefix + ".json"), artifact)
        write_text(project / (prefix + ".md"), markdown)
        data["search"] = {"options": options, "queries": queries, "stage": stage,
                          "results_json": prefix + ".json", "results_md": prefix + ".md"}
        if stage == "compare":
            data["comparison"] = {"json": "comparison.json", "markdown": "comparison.md"}
        if stage == "refine":
            data["strategy"] = {"options": options, "queries": queries,
                                "tested_at": artifact["created_at"]}
        data["known_papers"] = unique(data["known_papers"] + [identity(p) for p in papers])
        save(project, data)
    return str(project)


def set_preferences(project, tools, reason, collection=None):
    if not tools or any(t not in SOURCES for t in tools) or not reason.strip():
        raise ValueError("Save the user's chosen tools and the actual basis for that choice")
    with locked(project):
        project, data = load(project)
        data["preferences"].update({"tools": list(dict.fromkeys(tools)),
                                    "user_selection": reason, "updated_at": now()})
        if collection is not None:
            data["preferences"]["zotero_collection"] = collection
        save(project, data)


def save_context(project, content, note_paths=()):
    if not content.strip():
        raise ValueError("The discussion context is empty")
    paths = [str(Path(p).expanduser().resolve()) for p in note_paths]
    if any(not Path(p).is_file() for p in paths):
        raise ValueError("A linked reading note does not exist")
    with locked(project):
        project, data = load(project)
        write_text(project / "context-draft.md", content)
        data["context"]["draft_path"] = "context-draft.md"
        data["context"]["draft_sha256"] = digest(content)
        data["notes"] = list(dict.fromkeys(data.get("notes", []) + paths))
        save(project, data)


def review_context(project, expected_hash, approved):
    if not approved:
        raise ValueError("Explicit user approval of this content is required")
    with locked(project):
        project, data = load(project)
        context = data["context"]
        if not context.get("draft_path"):
            raise ValueError("No context draft is waiting for review")
        draft = project / context["draft_path"]
        content = draft.read_text(encoding="utf-8")
        if digest(content) != expected_hash or expected_hash != context.get("draft_sha256"):
            raise ValueError("The draft changed; review the current text before approving")
        write_text(project / "context.md", content)
        data["context"] = {"reviewed_path": "context.md", "reviewed_sha256": expected_hash,
                           "reviewed_at": now()}
        save(project, data)
        draft.unlink()


def read_context(project, data):
    context = data.get("context", {})
    result = {"reviewed_text": "", "reviewed_path": None,
              "draft_pending": bool(context.get("draft_path")), "notes": []}
    if context.get("reviewed_path"):
        path = project / context["reviewed_path"]
        content = path.read_text(encoding="utf-8")
        if digest(content) != context.get("reviewed_sha256"):
            raise ValueError("Reviewed context changed outside the review workflow; review it again")
        result.update(reviewed_text=content, reviewed_path=str(path))
    for filename in data.get("notes", []):
        path = Path(filename)
        if not path.exists():
            result["notes"].append({"path": filename, "status": "missing"})
            continue
        content = path.read_text(encoding="utf-8")
        front = content.split("---", 2)[1] if content.startswith("---") and content.count("---") >= 2 else ""
        reviewed = bool(re.search(r"^human_reviewed:\s*true\s*$", front, re.M))
        result["notes"].append({"path": filename, "status": "reviewed" if reviewed else "draft",
                                "sha256": digest(content), "text": content if reviewed else ""})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("discover"); p.add_argument("--workspace", type=Path, required=True)
    p = sub.add_parser("init"); p.add_argument("--workspace", type=Path, required=True); p.add_argument("--topic", required=True)
    p = sub.add_parser("record-search")
    p.add_argument("--project", required=True); p.add_argument("--input", type=Path, required=True)
    p.add_argument("--markdown", type=Path, required=True); p.add_argument("--stage", choices=("compare", "refine", "search"), default="search")
    p = sub.add_parser("prefer"); p.add_argument("--project", required=True); p.add_argument("--tools", required=True)
    p.add_argument("--user-selection", required=True); p.add_argument("--collection")
    p = sub.add_parser("save-context"); p.add_argument("--project", required=True); p.add_argument("--input", type=Path, required=True)
    p.add_argument("--note", type=Path, action="append", default=[])
    p = sub.add_parser("review-context"); p.add_argument("--project", required=True); p.add_argument("--sha256", required=True)
    p.add_argument("--user-approved", action="store_true")
    p = sub.add_parser("read"); p.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        if args.command == "discover":
            out = discover(args.workspace)
        elif args.command == "init":
            out = {"project": str(initialize(args.workspace, args.topic))}
        elif args.command == "record-search":
            value = read_json(args.input)
            out = {"project": record_search(args.project, value["options"], value["queries"], value["papers"],
                                           args.markdown.read_text(encoding="utf-8"), args.stage)}
        elif args.command == "prefer":
            set_preferences(args.project, args.tools.split(","), args.user_selection, args.collection)
            out = {"saved": True}
        elif args.command == "save-context":
            save_context(args.project, args.input.read_text(encoding="utf-8"), args.note)
            out = load(args.project)[1]["context"]
        elif args.command == "review-context":
            review_context(args.project, args.sha256, args.user_approved)
            out = {"reviewed": True}
        else:
            project, data = load(args.project)
            out = {"project": str(project), **data, "context_contents": read_context(project, data)}
        print(json.dumps(out, ensure_ascii=False))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
