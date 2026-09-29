"""Offline integration tests. All papers, confirmations, and saves here are fixtures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("watch", ROOT / "paper-watch/scripts/watch.py")
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)
store = watch.store
import screen_batch
import compare_results


def paper(number, **overrides):
    return {"title": f"Fixture paper {number}", "authors": "Alice Smith", "year": 2026,
            "doi": f"10.1234/fixture.{number}", "doi_verified": True,
            "sources": ["pubmed"], "topic_fit": "yes", "summary_basis": "abstract",
            "paper_summary": "A fixture summary.", "relevance": "A fixture connection.", **overrides}


def saved(p, status="added", **overrides):
    return {**store.identity(p), "status": status, "item_key": "ITEM" + p["doi"].split(".")[-1],
            "collection_key": "TEST", "library": "/api/users/0", "pdf_status": "verified", **overrides}


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="paper-watch-test-")
        self.root = Path(self.temp.name)
        self.project = store.initialize(self.root, "Fixture research question")
        self.options = {"topic": "Fixture research question", "tools": ["pubmed", "semantic-scholar"],
                        "max_papers": 2, "tab_mode": "visible", "result_mode": "compare",
                        "only_not_in_zotero": False, "context": "Adults; original research."}
        self.queries = [{"source": s, "query": "fixture baseline query"} for s in self.options["tools"]]
        store.record_search(self.project, self.options, self.queries, [paper(0)], "# Fixture comparison", "compare")
        store.set_preferences(self.project, ["pubmed"], "Fixture user chose PubMed", "Test")
        self.settings = {"schedule": "Every Monday at 09:00", "timezone": "Europe/Zurich",
                         "max_papers": 2, "tab_mode": "background",
                         "collection": {"name": "Test", "key": "TEST", "library": "/api/users/0"}}

    def tearDown(self):
        self.temp.cleanup()

    def configure(self):
        return watch.configure(self.project, watch.prepare(self.project)["sha256"], self.settings, True)

    def stage(self, papers, source_status="complete"):
        run = watch.begin(self.project)
        return watch.stage(self.project, run["id"], {"sources": {"pubmed": {"status": source_status}}, "papers": papers})

    def test_artifacts_survive_and_preferred_sources_are_reused(self):
        refined = [{"source": "pubmed", "query": "fixture precise terminology"}]
        store.record_search(self.project, {**self.options, "tools": ["pubmed"]}, refined,
                            [paper(1)], "# Refined results", "refine")
        store.record_search(self.project, self.options, self.queries, [], "# Later unrelated wording")
        result = watch.prepare(self.project)
        self.assertEqual(result["queries"], refined)
        self.assertEqual(result["options"]["tools"], ["pubmed"])
        self.assertTrue((self.project / "comparison.md").exists())
        self.assertEqual(len(store.load(self.project)[1]["known_papers"]), 2)

    def test_discovery_is_workspace_scoped(self):
        other = store.initialize(self.root, "Another topic")
        self.assertEqual(len(store.discover(self.root)), 2)
        self.assertEqual(store.discover(other)[0]["topic"], "Another topic")
        self.assertEqual(store.discover(self.root / "unrelated"), [])

    def test_confirmation_and_stale_proposal(self):
        prepared = watch.prepare(self.project)
        with self.assertRaises(ValueError):
            watch.configure(self.project, prepared["sha256"], self.settings, False)
        store.save_context(self.project, "New unreviewed context")
        with self.assertRaises(ValueError):
            watch.configure(self.project, prepared["sha256"], self.settings, True)
        self.assertFalse(self.configure()["scheduled"])

    def test_context_review_and_rereading_each_run(self):
        store.save_context(self.project, "Original draft")
        fingerprint = store.digest("Original draft")
        with self.assertRaises(ValueError):
            store.review_context(self.project, fingerprint, False)
        store.save_context(self.project, "Revised draft")
        with self.assertRaises(ValueError):
            store.review_context(self.project, fingerprint, True)
        store.review_context(self.project, store.digest("Revised draft"), True)
        self.configure()
        first = self.stage([])
        self.assertEqual(first["plan"]["context"]["reviewed_text"], "Revised draft")
        watch.finish(self.project, first["id"], [])
        store.save_context(self.project, "Human correction")
        store.review_context(self.project, store.digest("Human correction"), True)
        second = watch.begin(self.project)
        self.assertEqual(second["plan"]["context"]["reviewed_text"], "Human correction")
        (self.project / "context.md").write_text("Unreviewed external edit")
        with self.assertRaises(ValueError):
            watch.prepare(self.project)

    def test_linked_notes_review_status(self):
        note = self.root / "note.md"
        note.write_text("---\nhuman_reviewed: false\n---\nDraft finding")
        store.save_context(self.project, "Discussion", [note])
        result = watch.prepare(self.project)["context"]
        self.assertEqual(result["notes"][0]["text"], "")
        self.assertEqual(result["reviewed_text"], "")
        note.write_text("---\nhuman_reviewed: true\n---\nReviewed fixture finding")
        self.assertIn("Reviewed fixture", watch.prepare(self.project)["context"]["notes"][0]["text"])

    def test_duplicates_overflow_resume_and_idempotent_finish(self):
        self.configure()
        run = self.stage([paper(0), paper(1), paper(1, doi="https://doi.org/10.1234/FIXTURE.1"), paper(2), paper(3)])
        self.assertEqual(len(run["pool"]), 3)
        self.assertEqual(len(run["selected"]), 2)
        self.assertEqual(watch.begin(self.project)["id"], run["id"])
        outcomes = [saved(p) for p in run["selected"]]
        result = watch.finish(self.project, run["id"], outcomes)
        self.assertEqual((result["added"], result["pending"]), (2, 1))
        self.assertEqual(watch.finish(self.project, run["id"], outcomes), result)
        Path(result["update_path"]).unlink()
        watch.finish(self.project, run["id"], outcomes)
        self.assertTrue(Path(result["update_path"]).exists())
        next_run = self.stage([paper(1), paper(2)])
        self.assertEqual([p["title"] for p in next_run["selected"]], [paper(3)["title"]])
        watch.finish(self.project, next_run["id"], [saved(p) for p in next_run["selected"]])
        empty = self.stage([paper(0), paper(1), paper(2), paper(3)])
        self.assertFalse(watch.finish(self.project, empty["id"], [])["notify"])

    def test_failure_does_not_advance_checkpoint_or_lose_pending(self):
        self.configure()
        run = self.stage([paper(1)], "partial")
        fail = saved(paper(1), "failed", reason="Zotero not running")
        result = watch.finish(self.project, run["id"], [fail])
        self.assertEqual(result["added"], 0)
        self.assertNotIn("pubmed", watch.state(self.project)["checkpoints"])
        retry = self.stage([])
        self.assertEqual(len(retry["selected"]), 1)
        watch.finish(self.project, retry["id"], [saved(paper(1))])
        self.assertIn("pubmed", watch.state(self.project)["checkpoints"])
        self.assertEqual(watch.state(self.project)["pending"], [])

    def test_three_failures_stop_retries(self):
        self.configure()
        for number in range(3):
            run = self.stage([paper(1)] if number == 0 else [])
            result = watch.finish(self.project, run["id"], [saved(paper(1), "failed", reason="Publisher unavailable")])
            self.assertEqual(result["failed"], 1)
        run = self.stage([])
        self.assertEqual(run["selected"], [])
        self.assertFalse(watch.finish(self.project, run["id"], [])["notify"])

    def test_unchanged_blocked_source_is_quiet(self):
        self.configure()
        first = self.stage([], "blocked")
        self.assertTrue(watch.finish(self.project, first["id"], [])["notify"])
        second = self.stage([], "blocked")
        self.assertFalse(watch.finish(self.project, second["id"], [])["notify"])

    def test_wrong_collection_cannot_be_reported_as_saved(self):
        self.configure()
        run = self.stage([paper(1)])
        with self.assertRaises(ValueError):
            watch.finish(self.project, run["id"], [saved(paper(1), collection_key="WRONG")])
        self.assertEqual(watch.state(self.project)["active"], run["id"])

    def test_pending_pdf_is_checked_without_resaving_parent(self):
        self.configure()
        run = self.stage([paper(1)])
        result = watch.finish(self.project, run["id"], [saved(paper(1), pdf_status="pending")])
        self.assertIn("PDF pending", result["digest"])
        second = self.stage([paper(1)])
        self.assertEqual(second["selected"], [])
        self.assertEqual(len(second["pdf_followups"]), 1)
        result = watch.finish(self.project, second["id"], [], attachment_updates=[{
            "item_key": "ITEM1", "library": "/api/users/0", "pdf_status": "verified"}])
        self.assertEqual(result["added"], 0)
        self.assertIn("PDF update", result["digest"])
        self.assertEqual(watch.state(self.project)["pdf_followups"], [])

    def test_proposals_do_not_mutate_reviewed_context_or_pending_draft(self):
        store.save_context(self.project, "Reviewed understanding")
        store.review_context(self.project, store.digest("Reviewed understanding"), True)
        store.save_context(self.project, "Other pending human discussion")
        self.configure()
        run = self.stage([paper(1)])
        proposal = {"base_context_sha256": store.digest("Reviewed understanding"),
                    "current_understanding": "Previous evidence", "new_evidence": "New evidence",
                    "interpretation": "An apparent disagreement needs review.",
                    "references": ["Fixture reference"], "proposed_context": "Possible revision"}
        result = watch.finish(self.project, run["id"], [saved(paper(1))], proposal)
        self.assertEqual((self.project / "context.md").read_text(), "Reviewed understanding")
        self.assertEqual((self.project / "context-draft.md").read_text(), "Other pending human discussion")
        self.assertTrue(Path(result["proposal_path"]).exists())

    def test_identity_matching_is_conservative(self):
        self.assertFalse(store.same_paper(paper(1), paper(1, doi="10.1234/different")))
        self.assertTrue(store.same_paper(paper(1), paper(1, doi="", doi_verified=False)))
        self.assertFalse(store.same_paper(paper(1), paper(1, doi="", doi_verified=False, authors="Bob Jones")))
        self.assertFalse(store.same_paper({"source_id": "1", "source": "pubmed"},
                                          {"source_id": "1", "source": "semantic-scholar"}))

    def test_history_excluded_before_quota_and_output(self):
        ledger = {"source": "pubmed", "max_papers": 2, "only_not_in_zotero": False,
                  "zotero_checked": False, "records": [paper(1, previously_reported=True), paper(2)]}
        screen_batch.update_statuses(ledger, None)
        progress = screen_batch.progress(ledger)
        self.assertEqual(progress["count_toward_target"], 1)
        self.assertEqual(sum(progress["coverage"]["categories"].values()), 2)
        result = compare_results.build_comparison([ledger], 2, False)
        self.assertEqual(result["sources"][0]["shown"], 1)
        self.assertEqual(result["sources"][0]["results"][0]["title"], paper(2)["title"])

    def test_cli_exclusion(self):
        batch = self.root / "batch.json"
        excluded = self.root / "excluded.json"
        batch.write_text(json.dumps([paper(1), paper(2)]))
        excluded.write_text(json.dumps([store.identity(paper(1))]))
        command = [sys.executable, "-B", str(ROOT / "paper-search/scripts/screen_batch.py"),
                   "--ledger", str(self.root / "ledger.json"), "--source", "pubmed", "--input", str(batch),
                   "--max-papers", "2", "--exclude-papers", str(excluded)]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["count_toward_target"], 1)

    def test_sources_keep_independent_checkpoints(self):
        store.set_preferences(self.project, ["pubmed", "semantic-scholar"], "Fixture chose both")
        self.configure()
        run = watch.begin(self.project)
        watch.stage(self.project, run["id"], {"sources": {
            "pubmed": {"status": "complete"},
            "semantic-scholar": {"status": "blocked", "reason": "Rate limit"}}, "papers": []})
        watch.finish(self.project, run["id"], [])
        checkpoints = watch.state(self.project)["checkpoints"]
        self.assertIn("pubmed", checkpoints)
        self.assertNotIn("semantic-scholar", checkpoints)

    def test_untested_source_cannot_be_silently_added(self):
        store.set_preferences(self.project, ["consensus"], "Fixture changed source")
        self.assertEqual(watch.prepare(self.project)["missing_queries"], ["consensus"])
        with self.assertRaises(ValueError):
            self.configure()

    def test_existing_item_is_not_counted_as_added(self):
        self.configure()
        run = self.stage([paper(1), paper(2)])
        result = watch.finish(self.project, run["id"], [saved(paper(1)),
                              saved(paper(2), "already_present", pdf_status="absent")])
        self.assertEqual((result["added"], result["already_present"]), (1, 1))
        self.assertIn("1 new paper added", result["digest"])
        self.assertIn("Already present; PDF absent", result["digest"])


if __name__ == "__main__":
    unittest.main()
