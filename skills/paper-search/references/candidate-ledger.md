# Candidate ledger

Use one temporary ledger per selected source. Collect **structured objects from the official API or provider MCP tool first**; use rendered cards and tab-scoped CDP only for browser fallback. Keep the stable paper ID or URL as `source_id` and the actual retrieval route as `retrieval_route` (`api` or `browser`). Set `source_rank` to the paper's position across pages of that route, so page 2 does not restart at rank 1. Enrich metadata without changing source ID or rank:

```json
[
  {
    "source_id": "https://example.org/paper/123",
    "title": "Example paper",
    "authors": "A. Researcher et al.",
    "year": 2024,
    "journal": "Example Journal",
    "source_url": "https://example.org/paper/123",
    "source_rank": 3,
    "retrieval_route": "api",
    "snippet": "Result-card text",
    "topic_fit": "yes",
    "doi": "10.1234/example",
    "doi_verified": true
  }
]
```

`topic_fit` is `yes`, `no`, or `uncertain` after checking the user's filters and the available title/snippet. Set `doi_verified` when the DOI appears in the rendered source card, a DOI link, its title URL, or corroborated official metadata. Capture first author, year, and journal when available. Resolve eligible papers' missing DOIs with [metadata lookup](metadata-lookup.md), regardless of Zotero exclusion. Preserve the discovery URL, ID, and rank; record the DOI verification URL as `doi_provenance`. Do not contact Zotero when exclusion is off. Use content already returned by metadata APIs; retrieve further information only when needed to establish eligibility or write a supported paper description. Before final output, add `paper_summary` and `summary_basis` according to [Paper summaries](../SKILL.md#paper-summaries), retaining the evidence fields separately.

With Zotero exclusion **on**, compare the source card against the pre-search snapshot. An exact title match with first author, year, and journal agreeing confirms `in_zotero` **without requiring a DOI**, unless both records have conflicting DOIs. A missing or conflicting field yields `possible_match` plus the reason and Zotero record metadata in `title_matches_to_review`; inspect source details and that Zotero item only if needed to resolve it. A possible match cannot count as absent. Resolve DOIs for the remaining candidates in batches and submit updates with the **same `source_id`**. Open source or publisher details only for facts unresolved by the metadata route.

Run the helper after each small API batch, fallback card batch, or DOI update, using the same Python interpreter as the intake form:

```text
python screen_batch.py --ledger CONSENSUS.json --source consensus --input BATCH.json --max-papers 6
```

Add `--snapshot SNAPSHOT.json --only-not-in-zotero` **only** when the user selected Zotero exclusion. The output gives `count_toward_target`, `target_reached`, and `needs_doi` with either Zotero option; `title_matches_to_review` applies only to exclusion. Read the target count before loading more results, and resolve pending DOIs for the papers that will be shown before final output. The ledger deduplicates repeated cards by source ID. Use separate ledger paths for concurrent sources. Delete temporary batches, ledgers, caches, and any snapshot when the search ends. Keep internal coverage counters out of the user-facing results.
