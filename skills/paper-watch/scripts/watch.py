#!/usr/bin/env python3
"""Prepare recurring searches, preserve run state, and render verified Zotero updates.

No scheduler, search, or Zotero writes are hidden in this helper. The agent uses
Codex's scheduler and the existing search/save/reading skills for those actions.
"""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paper-search" / "scripts"))
import research_store as store


def state(project):
    path = project / "watch.json"
    return store.read_json(path) if path.exists() else {
        "checkpoints": {}, "reported": [], "pending": [], "completed": {}, "active": None}


def prepare(project):
    project, data = store.load(project)
    search = data.get("strategy") or data.get("search")
    if not search:
        raise ValueError("Run paper-search for this topic first")
    preferences = data.get("preferences", {})
    options = dict(search["options"])
    options["tools"] = preferences.get("tools") or options["tools"]
    queries = [q for q in search["queries"] if q["source"] in options["tools"]]
    missing = [source for source in options["tools"] if not any(q["source"] == source for q in queries)]
    context = store.read_context(project, data)
    proposal = {"project": str(project), "topic": data["topic"], "options": options,
                "queries": queries, "context": context,
                "tool_choice": preferences.get("user_selection", "Last search choices; no preference recorded"),
                "collection": preferences.get("zotero_collection"), "missing_queries": missing}
    proposal["sha256"] = store.digest(proposal)
    return proposal


def configure(project, expected_hash, settings, confirmed):
    if not confirmed:
        raise ValueError("Confirm the prefilled routine with the user first")
    with store.locked(project):
        project, _ = store.load(project)
        proposal = prepare(project)
        if expected_hash != proposal["sha256"]:
            raise ValueError("Research artifacts changed; show the updated proposal")
        if proposal["missing_queries"]:
            raise ValueError("Test queries for the newly selected sources before scheduling")
        required = ("schedule", "timezone", "collection", "tab_mode", "max_papers")
        if any(not settings.get(key) for key in required):
            raise ValueError("Confirm schedule, timezone, collection, tab mode, and paper limit")
        ZoneInfo(settings["timezone"])
        if settings["tab_mode"] not in ("visible", "background"):
            raise ValueError("Invalid tab mode")
        if type(settings["max_papers"]) is not int or not 1 <= settings["max_papers"] <= 50:
            raise ValueError("max_papers must be 1–50")
        collection = settings["collection"]
        if not isinstance(collection, dict) or not all(collection.get(k) for k in ("name", "key", "library")):
            raise ValueError("Resolve the exact Zotero collection name, key, and library first")
        current = state(project)
        if current["active"]:
            raise ValueError("Finish the current run before changing the routine")
        current["config"] = {**settings, "confirmed_at": store.now(), "artifact_sha256": expected_hash}
        store.write_json(project / "watch.json", current)
        return {"configured": True, "scheduled": bool(current.get("automation_id")),
                "automation_id": current.get("automation_id")}


def attach(project, automation_id):
    if not automation_id.strip():
        raise ValueError("Use the actual automation ID returned by Codex")
    with store.locked(project):
        project, _ = store.load(project)
        current = state(project)
        if "config" not in current:
            raise ValueError("Confirm the routine first")
        current["automation_id"] = automation_id
        store.write_json(project / "watch.json", current)


def begin(project):
    with store.locked(project):
        project, data = store.load(project)
        current = state(project)
        if "config" not in current:
            raise ValueError("Confirm the routine first")
        if current["active"]:
            run = store.read_json(project / "watch-runs" / current["active"] / "run.json")
            return {**run, "resuming": True}
        plan = prepare(project)
        if plan["missing_queries"]:
            raise ValueError("Saved source choices have no tested queries: " + ", ".join(plan["missing_queries"]))
        started = store.now()
        until = datetime.fromisoformat(started)
        windows = {}
        for source in plan["options"]["tools"]:
            previous = current["checkpoints"].get(source)
            since = datetime.fromisoformat(previous) - timedelta(days=7) if previous else until - timedelta(days=30)
            windows[source] = {"since": since.isoformat(), "until": started}
        plan["options"].update({"max_papers": current["config"]["max_papers"],
                                "tab_mode": current["config"]["tab_mode"], "result_mode": "ranked"})
        run_id = until.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        folder = project / "watch-runs" / run_id
        excluded = store.unique(data.get("known_papers", []) + current["reported"] +
                                [store.identity(p) for p in current["pending"]])
        store.write_json(folder / "exclude-papers.json", excluded)
        run = {"id": run_id, "started_at": started, "plan": plan, "windows": windows,
               "collection": current["config"]["collection"], "stage": "searching",
               "exclude_papers": str(folder / "exclude-papers.json"),
               "pdf_followups": current.get("pdf_followups", [])}
        store.write_json(folder / "run.json", run)
        current["active"] = run_id
        store.write_json(project / "watch.json", current)
        return run


def stage(project, run_id, batch):
    """Persist the complete eligible pool before selecting papers to save."""
    with store.locked(project):
        project, data = store.load(project)
        current = state(project)
        if current["active"] != run_id:
            raise ValueError("Not the active run")
        path = project / "watch-runs" / run_id / "run.json"
        run = store.read_json(path)
        if run["stage"] == "staged":
            if run["batch_sha256"] != store.digest(batch):
                raise ValueError("A staged run cannot be replaced; resume its saved selection")
            return run
        sources = run["plan"]["options"]["tools"]
        statuses = batch.get("sources", {})
        if set(statuses) != set(sources) or any(s.get("status") not in ("complete", "partial", "blocked") for s in statuses.values()):
            raise ValueError("Record complete, partial, or blocked for every selected source")
        papers = batch.get("papers")
        if not isinstance(papers, list):
            raise ValueError("Supply every eligible paper, ordered by relevance to the saved context")
        for p in papers:
            if (not p.get("title") or p.get("topic_fit") != "yes" or not p.get("paper_summary")
                    or not p.get("summary_basis") or not p.get("relevance")
                    or not p.get("sources") or any(s not in sources for s in p["sources"])):
                raise ValueError("Each eligible paper needs title, sources, summary, evidence basis, and relevance")
        known = data.get("known_papers", []) + current["reported"]
        fresh = [p for p in papers if not any(store.same_paper(p, old) for old in known)]
        # Retain unsaved/overflow papers even when they leave the search date window.
        pool = store.unique(current["pending"] + fresh)
        selected = [p for p in pool if p.get("save_attempts", 0) < 3][:run["plan"]["options"]["max_papers"]]
        run.update(stage="staged", batch_sha256=store.digest(batch), sources=statuses,
                   pool=pool, selected=selected)
        store.write_json(path, run)
        return run


def paper_link(p):
    doi = store.doi(p)
    url = "https://doi.org/" + doi if doi else p.get("source_url", "")
    title = p["title"].replace("[", "\\[").replace("]", "\\]")
    return f"[{title}]({url})" if url else title


def finish(project, run_id, outcomes, proposal=None, attachment_updates=None):
    """Commit verified outcomes, digest, and checkpoints once; failures remain pending."""
    attachment_updates = attachment_updates or []
    payload_hash = store.digest({"outcomes": outcomes, "proposal": proposal, "attachments": attachment_updates})
    with store.locked(project):
        project, data = store.load(project)
        current = state(project)
        folder = project / "watch-runs" / run_id
        if run_id in current["completed"]:
            saved = current["completed"][run_id]
            if saved["payload_sha256"] != payload_hash:
                raise ValueError("This run was already completed with different outcomes")
            # Repair a missing output after interruption, without repeating saves.
            store.write_text(folder / "update.md", saved["digest"])
            return saved
        if current["active"] != run_id:
            raise ValueError("Not the active run")
        run = store.read_json(folder / "run.json")
        if run["stage"] != "staged" or len(outcomes) != len(run["selected"]):
            raise ValueError("Record one verified save outcome for every selected paper")
        results = []
        for paper in run["selected"]:
            matches = [o for o in outcomes if store.same_paper(paper, o)]
            if len(matches) != 1:
                raise ValueError("Save outcomes must identify each selected paper uniquely")
            outcome = matches[0]
            status = outcome.get("status")
            if status not in ("added", "already_present", "failed"):
                raise ValueError("Save status must be added, already_present, or failed")
            if status != "failed":
                if (not outcome.get("item_key") or outcome.get("collection_key") != run["collection"]["key"]
                        or outcome.get("library") != run["collection"]["library"]):
                    raise ValueError("Verify the saved item in the exact confirmed library and collection")
                if outcome.get("pdf_status") not in ("verified", "pending", "absent", "unverified"):
                    raise ValueError("Record the actual PDF status")
            elif not outcome.get("reason"):
                raise ValueError("A failed save needs its measured reason")
            results.append({**paper, "save": outcome})
        successful = [p for p in results if p["save"]["status"] != "failed"]
        pending = [p for p in run["pool"] if not any(store.same_paper(p, done) for done in successful)]
        for p in pending:
            if any(store.same_paper(p, failed) for failed in results if failed["save"]["status"] == "failed"):
                p["save_attempts"] = p.get("save_attempts", 0) + 1
        added = sum(p["save"]["status"] == "added" for p in results)
        existing = sum(p["save"]["status"] == "already_present" for p in results)
        failed = len(results) - len(successful)
        lines = [f"## {added} new paper{'s' if added != 1 else ''} added to Zotero"] if results else []
        if existing or failed:
            lines += [f"{existing} already present; {failed} could not be saved."]
        for p in results:
            save = p["save"]
            status = "Could not save: " + save["reason"] if save["status"] == "failed" else (
                ("Added" if save["status"] == "added" else "Already present") + "; PDF " + save["pdf_status"])
            coverage = " (Abstract only.)" if p["summary_basis"] == "abstract" else ""
            lines += ["", f"- **{paper_link(p)}** — {status}. {p['paper_summary']}{coverage} {p['relevance']}"]
            if p.get("read_next"):
                lines += [f"  **Worth reading:** {p['read_next']}"]
        failures = {s: info for s, info in run["sources"].items() if info["status"] != "complete"}
        changed_failures = failures != current.get("last_failures", {})
        if failures and (changed_failures or results):
            lines += ["", "Search incomplete: " + "; ".join(s + " — " + info.get("reason", info["status"]) for s, info in failures.items()) + "."]
        blocked = [p for p in pending if p.get("save_attempts", 0) == 3 and
                   any(store.same_paper(p, result) for result in results)]
        if blocked:
            lines += ["", f"{len(blocked)} save(s) need attention after three failed attempts; automatic retries stopped."]
        pdf_followups = list(current.get("pdf_followups", []))
        for p in successful:
            if p["save"]["pdf_status"] in ("pending", "unverified"):
                pdf_followups.append({**store.identity(p), "save": p["save"], "checks": 0})
        for update in attachment_updates:
            matches = [p for p in pdf_followups if p["save"]["item_key"] == update.get("item_key")
                       and p["save"]["library"] == update.get("library")]
            if len(matches) != 1 or update.get("pdf_status") not in ("verified", "absent", "pending", "unverified"):
                raise ValueError("An attachment update must identify a pending item and its measured PDF status")
            paper = matches[0]
            paper["checks"] += 1
            paper["save"]["pdf_status"] = update["pdf_status"]
            if update["pdf_status"] in ("verified", "absent"):
                pdf_followups.remove(paper)
                lines += ["", f"PDF update: {paper_link(paper)} — {update['pdf_status']}."]
            elif paper["checks"] == 3:
                lines += ["", f"PDF still unverified: {paper_link(paper)}. Check this attachment in Zotero."]
        proposal_path = None
        if proposal:
            required = ("current_understanding", "new_evidence", "interpretation", "references", "proposed_context")
            if any(not proposal.get(k) for k in required):
                raise ValueError("Context proposals need the prior view, new evidence, interpretation, references, and proposed text")
            if proposal.get("base_context_sha256") != store.digest(run["plan"]["context"]["reviewed_text"]):
                raise ValueError("Link the proposal to the context actually used for this run")
            # Proposals are separate files; no automated run can replace reviewed context.
            proposal_path = str(folder / "context-proposal.json")
            store.write_json(proposal_path, proposal)
            lines += ["", "**Context to review:** " + proposal["interpretation"],
                      "", f"[Review the proposed context update]({proposal_path}). Keep or revise it before it is used in future searches."]
        digest = "\n".join(lines).strip() + ("\n" if lines else "")
        result = {"payload_sha256": payload_hash, "digest": digest, "added": added,
                  "already_present": existing, "failed": failed, "pending": len(pending),
                  "update_path": str(folder / "update.md"), "proposal_path": proposal_path,
                  "notify": bool(digest)}
        current["reported"] = store.unique(current["reported"] + [store.identity(p) for p in successful])
        current["pending"] = pending
        current["pdf_followups"] = pdf_followups
        current["last_failures"] = failures
        for source, info in run["sources"].items():
            if info["status"] == "complete":
                current["checkpoints"][source] = run["started_at"]
        current["completed"][run_id] = result
        current["active"] = None
        store.write_json(folder / "outcomes.json", outcomes)
        store.write_text(folder / "update.md", digest)
        store.write_json(project / "watch.json", current)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    p = sub.add_parser("configure"); p.add_argument("--sha256", required=True)
    p.add_argument("--settings", type=Path, required=True); p.add_argument("--user-confirmed", action="store_true")
    p = sub.add_parser("attach"); p.add_argument("--automation-id", required=True)
    sub.add_parser("begin")
    p = sub.add_parser("stage"); p.add_argument("--run", required=True); p.add_argument("--input", type=Path, required=True)
    p = sub.add_parser("finish"); p.add_argument("--run", required=True); p.add_argument("--outcomes", type=Path, required=True)
    p.add_argument("--proposal", type=Path)
    p.add_argument("--attachment-updates", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.project)
        elif args.command == "configure":
            result = configure(args.project, args.sha256, store.read_json(args.settings), args.user_confirmed)
        elif args.command == "attach":
            result = attach(args.project, args.automation_id)
        elif args.command == "begin":
            result = begin(args.project)
        elif args.command == "stage":
            result = stage(args.project, args.run, store.read_json(args.input))
        else:
            result = finish(args.project, args.run, store.read_json(args.outcomes),
                            store.read_json(args.proposal) if args.proposal else None,
                            store.read_json(args.attachment_updates) if args.attachment_updates else None)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
