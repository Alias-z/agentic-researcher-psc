# Results by source

When `result_mode` is `compare`, run `scripts/compare_results.py` with each available source ledger, `--max-papers N`, and `--only-not-in-zotero` only if the user selected exclusion. The helper preserves each tool's source rank and includes DOI-less cards when exclusion is off. For example:

```text
python compare_results.py --ledger SCITE.json --ledger CONSENSUS.json --max-papers 6
```

Show one heading and **one three-column table per selected source**, in the order the user selected the tools. Do not merge or reorder its papers. Keep a paper visible under every source that returned it. If a source is unavailable or returns fewer than requested, give only a brief factual reason.

| Paper | Source summary | Source |
| --- | --- | --- |

Put a DOI-linked title with authors and year in the Paper cell when the source UI exposes a DOI. Otherwise link the source's paper URL and write **DOI not shown in search result**. The Source summary cell relays the source card's description; label an AI takeaway or snippet as such and do not write an independent assessment. The third cell gives the source name and original rank. When Zotero exclusion is on, call the third column **Source · Zotero** and add **Not found in Zotero (My Library)** for each displayed paper. When exclusion is off, do not mention Zotero per paper.

Do not add a scorecard, search notes, coverage table, or verdict about which tool is better. The user can compare the source lists and rate the tools.
