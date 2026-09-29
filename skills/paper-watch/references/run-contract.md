# Local artifacts and run commands

Run from this skill directory or use the absolute script path. These commands do not contact providers, save to Zotero, or create an automation. Test fixtures are not evidence of a live scheduled save.

```text
python3 scripts/watch.py --project PROJECT prepare
python3 scripts/watch.py --project PROJECT configure --sha256 PROPOSAL_HASH --settings SETTINGS.json --user-confirmed
python3 scripts/watch.py --project PROJECT attach --automation-id ACTUAL_CODEX_ID
python3 scripts/watch.py --project PROJECT begin
python3 scripts/watch.py --project PROJECT stage --run RUN_ID --input BATCH.json
python3 scripts/watch.py --project PROJECT finish --run RUN_ID --outcomes SAVES.json
```

`prepare` gathers current artifacts and returns a hash. `configure` requires an unchanged proposal and the user's confirmation; the flag records approval, it does not obtain it. `attach` records a successful native scheduler response. Before creating a routine, inspect the saved ID and use the native tool to view/update it; if no ID was saved after an interruption, inspect existing native automations for this project to avoid a duplicate. Preserve existing fields and notification preferences when updating.

Confirmed settings:

```json
{
  "schedule": "Every Monday at 09:00",
  "timezone": "Europe/Zurich",
  "max_papers": 5,
  "tab_mode": "background",
  "collection": {"name": "Research", "key": "ACTUAL_KEY", "library": "/api/users/0"}
}
```

Use measured keys from zotero-save, not these example values. Do not silently choose a same-named collection in another library. A schedule change requires the native tool as well as updated settings. Do not store credentials or tokens in these artifacts.

## Search and stage

`begin` rereads the latest saved strategy, user tool preferences, and reviewed context. It returns the run ID, options, query list, source windows, exact collection, history exclusion file, and pending PDF checks. If a run was interrupted it returns the existing run, including its staged selection, so resume it instead of repeating publisher saves. Pending attachment checks stop automatically after three inconclusive checks; ask the user to inspect those files. Do not confuse them with a new paper save.

Before each new candidate is enriched, apply the history file via paper-search's `--exclude-papers`. Early screening repeats after identifiers are enriched. It excludes previously displayed exercise results and queued/reported routine papers without contacting Zotero. Failed saves and overflow remain in the local pending pool even if their publication dates leave the search window.

Stage a JSON object with `sources` and `papers`:

```json
{
  "sources": {"pubmed": {"status": "complete"}},
  "papers": [{
    "title": "Actual paper title", "authors": "Actual authors", "year": 2026,
    "doi": "10.1234/example", "doi_verified": true,
    "doi_provenance": "URL where this DOI was verified",
    "sources": ["pubmed"], "topic_fit": "yes",
    "paper_summary": "Supported findings in your own words.",
    "summary_basis": "abstract",
    "relevance": "The specific connection to the saved research question.",
    "read_next": "Optional: what warrants a closer read."
  }]
}
```

Include every selected source, with `complete`, `partial`, or `blocked` and a reason when incomplete. `complete` means the requested target or accessible results were exhausted; it does not mean all literature has been found. Order eligible new papers by relevance to the user's context; no invented numerical scores. Only genuine papers enter this JSON. `stage` preserves all eligible overflow, deduplicates, and returns the bounded selection. Previously queued papers receive priority so they are not lost. It cannot replace an already staged selection; resume that selection.

## Save, report, and propose

`SAVES.json` is an array identifying each selected paper by verified DOI/PMID or corroborated title/author/year, plus:

- `status`: `added`, `already_present`, or `failed`.
- For successful saves: measured `item_key`, `collection_key`, `library`, and `pdf_status` (`verified`, `pending`, `absent`, or `unverified`). A matching metadata item does not prove a PDF was saved.
- For failures: the specific `reason`. Failed saves remain pending for up to three attempts; afterward surface the problem and stop retrying until the user requests it. Retain their records.

To update pending PDFs, add `--attachment-updates UPDATES.json`: an array with measured `item_key`, `library`, and `pdf_status`. Inspect the existing attachment, never re-save its parent just to obtain another PDF. Check only followups whose `checks` is less than three; later manual corrections can still update their status.

Optionally pass `--proposal PROPOSAL.json` with:

- `base_context_sha256`: hash of the reviewed text loaded at run start.
- `current_understanding`: earlier claim and its supporting reference.
- `new_evidence`: what the new study actually found, with reading coverage and checked references.
- `interpretation`: why it may change the context, including differences in methods or conditions.
- `references`: paper/reading-note links.
- `proposed_context`: precise replacement/addition for human review.

These proposals stay in their own run folder. They never replace `context.md` or a pending human draft. Apply a reviewed proposal through paper-reading's context workflow, comparing against any more recent context first.

`finish` writes the digest, retains failed/overflow candidates, and advances only complete sources. An identical retry returns the same saved outcome. Show the digest only when `notify` is true; unchanged empty/failing sources stay quiet after the first actionable report. A stored update is recoverable if the chat delivery is interrupted. Each run keeps `run.json`, `exclude-papers.json`, `outcomes.json`, `update.md`, and a proposal only when needed. `watch.json` holds the automation ID, checkpoints, pending work, and reporting history. Keep this state in the research workspace, not the shared teaching repository.
