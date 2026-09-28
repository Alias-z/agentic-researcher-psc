# Results by source

When `result_mode` is `compare`, run `scripts/compare_results.py` with each available source ledger, `--max-papers N`, and `--only-not-in-zotero` only if the user selected exclusion. The helper preserves each tool's source rank and includes DOI-less cards when exclusion is off. For example:

```text
python compare_results.py --ledger SCITE.json --ledger CONSENSUS.json --max-papers 6
```

Show one heading and **one three-column table per selected source**, in the order the user selected the tools. Do not merge or reorder its papers. Keep a paper visible under every source that returned it. If a source is unavailable or returns fewer than requested, give only a brief factual reason.

Use the active source list, including later chat additions or replacements, when checking completeness. Preserve the order from the API used for discovery, or from the browser when fallback was necessary. Do not rerun a successful API search in the browser merely to obtain a different ranking.

| Paper | Summary | Source |
| --- | --- | --- |

Put a DOI-linked title with authors and year in the Paper cell whenever the DOI is verified, including through [metadata lookup](metadata-lookup.md). Resolve missing DOIs before rendering results; missing from a card is not a final status. Only after lookup and the needed detail check, link a genuinely unresolved paper to its source URL and give the actual limit briefly. Write an objective paper description in Summary, following [Paper summaries](../SKILL.md#paper-summaries). Tailor it to the user's context using supported content; use the ledger's `paper_summary`, not a pasted abstract or a missing-abstract label. The third cell gives the original discovery source and rank, not Crossref or another DOI lookup provider. When Zotero exclusion is on, call the third column **Source · Zotero** and add **Not found in Zotero (My Library)** for each displayed paper. When exclusion is off, do not mention Zotero per paper.

Do not add a scorecard, search notes, coverage table, or verdict about which tool is better. The user can compare the source lists and rate the tools.
