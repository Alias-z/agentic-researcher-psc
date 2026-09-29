import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


SPEC = importlib.util.spec_from_file_location("notes", Path(__file__).parents[1] / "scripts" / "notes.py")
notes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notes)
PAPER = "ABCD2345"
NOTE = "EFGH2345"


def item(key=NOTE, kind="note", version=7, status=notes.DRAFT):
    data = {"itemType": kind, "tags": [{"tag": status}, {"tag": "my-comment", "type": 0}]}
    if kind == "note":
        data.update(parentItem=PAPER, note="<h1>Reading note</h1><p>User comment &amp; evidence.</p>")
    return {"key": key, "version": version, "data": data}


class NotesTests(unittest.TestCase):
    def client(self, existing=None):
        client = Mock()
        client.library = "/api/users/0"
        client.get.return_value = item(PAPER, "journalArticle")
        client.children.return_value = (existing or [], "12")
        return client

    def test_new_note_is_child_draft(self):
        client = self.client()
        plan = notes.prepare_draft(client, PAPER, "<p>Evidence</p>")
        self.assertEqual(plan["payload"]["parentItem"], PAPER)
        self.assertEqual(plan["payload"]["tags"], [{"tag": notes.DRAFT}])
        self.assertEqual(plan["library_version"], "12")
        client.authorize.assert_not_called()
        client.request.assert_not_called()

    def test_edit_reviewed_note_resets_status_and_preserves_other_tags(self):
        previous = item(status=notes.REVIEWED)
        plan = notes.prepare_draft(self.client([previous]), PAPER, "<p>Revision</p>", version=7)
        self.assertEqual(plan["key"], NOTE)
        self.assertEqual(plan["payload"]["tags"], [{"tag": "my-comment", "type": 0}, {"tag": notes.DRAFT}])

    def test_stale_or_missing_version_is_rejected(self):
        for version in (None, 6):
            with self.subTest(version=version), self.assertRaises(notes.Error):
                notes.prepare_draft(self.client([item()]), PAPER, "<p>Revision</p>", version=version)

    def test_duplicate_reading_notes_are_rejected(self):
        with self.assertRaises(notes.Error):
            notes.prepare_draft(self.client([item(), item(key="JKLM2345")]), PAPER, "<p>Draft</p>")

    def test_wrong_parent_type_empty_text_and_wrong_note_are_rejected(self):
        client = self.client()
        client.get.return_value = item(PAPER, "attachment")
        with self.assertRaises(notes.Error):
            notes.prepare_draft(client, PAPER, "<p>Draft</p>")
        with self.assertRaises(notes.Error):
            notes.prepare_draft(self.client(), PAPER, "<p> </p>")
        with self.assertRaises(notes.Error):
            notes.prepare_draft(self.client([item()]), PAPER, "<p>Draft</p>", note_key="JKLM2345", version=7)

    def test_review_needs_explicit_approval_and_current_version(self):
        client = self.client()
        client.get.return_value = item()
        with self.assertRaises(notes.Error):
            notes.prepare_review(client, NOTE, 7, False)
        with self.assertRaises(notes.Error):
            notes.prepare_review(client, NOTE, 6, True)
        plan = notes.prepare_review(client, NOTE, 7, True)
        self.assertEqual(set(plan["payload"]), {"tags"})
        self.assertEqual(plan["payload"]["tags"], [{"tag": "my-comment", "type": 0}, {"tag": notes.REVIEWED}])

    def test_conflicting_review_tags_are_not_reviewed(self):
        record = item()
        record["data"]["tags"].append({"tag": notes.REVIEWED})
        self.assertEqual(notes.state(record["data"]), "conflicting-tags")
        client = self.client()
        client.get.return_value = record
        with self.assertRaises(notes.Error):
            notes.prepare_review(client, NOTE, 7, True)

    def test_cli_preview_never_authorizes_or_writes(self):
        client = self.client()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.html"
            path.write_text("<p>Draft evidence</p>")
            output = io.StringIO()
            with patch.object(notes, "Client", return_value=client), contextlib.redirect_stdout(output):
                notes.main(["save-draft", PAPER, "--html", str(path)])
        self.assertFalse(json.loads(output.getvalue())["applied"])
        client.authorize.assert_not_called()
        client.request.assert_not_called()

    def test_search_includes_unreviewed_notes_with_status_by_default(self):
        client = self.client()
        client.listing.return_value = ([item(status=notes.REVIEWED), item(key="JKLM2345")], "12")
        output = io.StringIO()
        with patch.object(notes, "Client", return_value=client), contextlib.redirect_stdout(output):
            notes.main(["search", "starch"])
        params = client.listing.call_args.args[1]
        self.assertEqual(params["qmode"], "everything")
        self.assertEqual(params["itemType"], "note")
        self.assertNotIn("tag", params)
        self.assertEqual([x["status"] for x in json.loads(output.getvalue())["notes"]], ["reviewed", "draft"])

    def test_search_can_explicitly_filter_out_unreviewed_results(self):
        client = self.client()
        client.listing.return_value = ([item(status=notes.REVIEWED), item(key="JKLM2345")], "12")
        output = io.StringIO()
        with patch.object(notes, "Client", return_value=client), contextlib.redirect_stdout(output):
            notes.main(["search", "starch", "--reviewed-only"])
        params = client.listing.call_args.args[1]
        self.assertEqual(params["qmode"], "everything")
        self.assertEqual(params["itemType"], "note")
        self.assertEqual(params["tag"], notes.REVIEWED)
        self.assertEqual([x["key"] for x in json.loads(output.getvalue())["notes"]], [NOTE])

    def test_pagination_and_library_changes(self):
        client = notes.Client()
        client.request = Mock(side_effect=[([item()] * 100, {"Last-Modified-Version": "12"}),
                                          ([item()], {"Last-Modified-Version": "12"})])
        result, version = client.listing("/api/users/0/items")
        self.assertEqual(len(result), 101)
        self.assertEqual(version, "12")
        self.assertIn("start=100", client.request.call_args.args[0])
        client.request = Mock(side_effect=[([item()] * 100, {"Last-Modified-Version": "12"}),
                                          ([item()], {"Last-Modified-Version": "13"})])
        with self.assertRaises(notes.Error):
            client.listing("/api/users/0/items")

    def test_update_sends_version_precondition_and_checks_saved_parent(self):
        client = self.client()
        client.authorize.return_value = "test-key"
        saved = item(status=notes.REVIEWED)
        client.get.return_value = saved
        result = notes.apply(client, {"action": "mark-reviewed", "key": NOTE, "parent": PAPER,
                                     "version": 7, "payload": {"tags": [{"tag": notes.REVIEWED}]}})
        self.assertTrue(result["applied"])
        self.assertEqual(client.request.call_args.kwargs["headers"]["If-Unmodified-Since-Version"], "7")
        self.assertEqual(client.request.call_args.kwargs["method"], "PATCH")
        saved["data"]["parentItem"] = "JKLM2345"
        with self.assertRaises(notes.Error):
            notes.apply(client, {"action": "mark-reviewed", "key": NOTE, "parent": PAPER,
                                 "version": 7, "payload": {"tags": [{"tag": notes.REVIEWED}]}})

    def test_create_reads_multi_object_success_and_detects_rejection(self):
        client = self.client()
        client.authorize.return_value = "test-key"
        client.request.return_value = ({"successful": {"0": item()}, "failed": {}}, {})
        client.get.return_value = item()
        plan = {"action": "create-draft", "parent": PAPER, "library_version": "12",
                "payload": {"note": item()["data"]["note"], "tags": [{"tag": notes.DRAFT}]}}
        self.assertTrue(notes.apply(client, plan)["applied"])
        self.assertEqual(client.request.call_args.kwargs["headers"]["If-Unmodified-Since-Version"], "12")
        client.request.return_value = ({"failed": {"0": {"code": 400}}}, {})
        with self.assertRaises(notes.Error):
            notes.apply(client, plan)

    def test_saved_markdown_source_link_must_match(self):
        client = self.client()
        client.authorize.return_value = "test-key"
        expected = '<h1>Reading note</h1><p><a href="file:///notes/correct.md">Markdown source</a></p>'
        saved = item()
        saved["data"]["note"] = expected.replace("correct.md", "wrong.md")
        client.get.return_value = saved
        plan = {"action": "update-draft", "parent": PAPER, "key": NOTE, "version": 7,
                "payload": {"note": expected, "tags": [{"tag": notes.DRAFT}]}}
        with self.assertRaises(notes.Error):
            notes.apply(client, plan)

    def test_failed_authorization_never_writes(self):
        client = self.client()
        client.authorize.side_effect = notes.Error("Authorization denied")
        with self.assertRaises(notes.Error):
            notes.apply(client, {"action": "update-draft", "parent": PAPER, "key": NOTE,
                                 "version": 7, "payload": {"note": "<p>Evidence</p>"}})
        client.request.assert_not_called()

    def test_saved_text_mismatch_is_reported(self):
        client = self.client()
        client.authorize.return_value = "test-key"
        client.get.return_value = item()
        with self.assertRaises(notes.Error):
            notes.apply(client, {"action": "update-draft", "parent": PAPER, "key": NOTE, "version": 7,
                                 "payload": {"note": "<p>Different evidence</p>"}})


if __name__ == "__main__":
    unittest.main()
