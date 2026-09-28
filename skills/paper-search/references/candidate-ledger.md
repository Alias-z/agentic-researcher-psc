# Candidate ledger

Use one temporary ledger file per selected source. Extract **structured objects** from rendered result cards with tab-scoped CDP; keep the card URL or paper ID as `source_id`. Set `source_rank` to the paper's position across pages, so page 2 does not restart at rank 1. Record the metadata already shown by the search UI:

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
    "snippet": "Result-card text",
    "topic_fit": "yes",
    "doi": "10.1234/example",
    "doi_verified": true
  }
]
```

`topic_fit` is `yes`, `no`, or `uncertain` after checking the user's filters and the available title/snippet. Set `doi_verified` when the DOI appears in the rendered source card, a DOI link, or its title URL; otherwise leave it false. Capture first author, year, and journal when available. With Zotero exclusion **off**, keep topic-eligible cards without DOIs, do not resolve missing DOIs merely for output, and do not check Zotero. Open a source detail only when the user's filter or the card's missing information requires it. Read an abstract only when the card cannot establish topic eligibility.

With Zotero exclusion **on**, compare the source card against the pre-search snapshot. An exact title match with first author, year, and journal agreeing confirms `in_zotero` **without requiring a DOI**, unless both records have conflicting DOIs. A missing or conflicting field yields `possible_match` plus the reason and Zotero record metadata in `title_matches_to_review`; inspect source details and that Zotero item only if needed to resolve it. A possible match cannot count as absent. For papers still needing a DOI to confirm absence, inspect the source's own detail UI first, then submit updates with the **same `source_id`**. Use publisher metadata only if the source cannot provide the needed fact.

Run the helper after each batch of roughly 3–5 cards or DOI updates, using the same Python interpreter as the intake form:

```text
python screen_batch.py --ledger CONSENSUS.json --source consensus --input BATCH.json --max-papers 6
```

Add `--snapshot SNAPSHOT.json --only-not-in-zotero` **only** when the user selected Zotero exclusion. The output gives `count_toward_target` and `target_reached`; `needs_doi` and `title_matches_to_review` apply only to exclusion. Read the target count before loading more results. The ledger deduplicates repeated cards by source ID. Use separate ledger paths for concurrent sources. Delete temporary batches, ledgers, and any snapshot when the search ends. Keep internal coverage counters out of the user-facing results.
