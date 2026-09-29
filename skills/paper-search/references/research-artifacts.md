# Save the search for later work

Save completed results in the current research workspace, not the installed skill or a temporary folder. Use `scripts/research_store.py` with the same Python interpreter as the search form. It uses only the standard library and does not contact Zotero.

1. `discover --workspace ABSOLUTE_WORKSPACE` finds existing topics. Reuse the matching topic; ask when multiple projects are plausible. Otherwise use `init --workspace ABSOLUTE_WORKSPACE --topic "TOPIC"`.
2. Save the result tables as Markdown and a JSON object containing `options`, `queries`, and `papers`. `options` is the actual submitted form data, including context/filters. `queries` contains each actual query as `{source, query}`; keep tested alternatives and their observed differences, not hypothetical searches. `papers` contains the displayed structured records, including verified identifiers, discovery sources/ranks, summaries, and evidence provenance.
3. Run `record-search --project PROJECT --input RESULTS.json --markdown RESULTS.md --stage compare|refine|search`. Use `compare` for Exercise 1 and `refine` for tested query wording in Exercise 2. The tested strategy survives subsequent ordinary searches. Preserve all paper identities actually shown before deleting temporary ledgers.
4. When the student chooses preferred tools after comparing results, save that actual choice with `prefer --project PROJECT --tools pubmed,google-scholar --user-selection "THE USER'S CHOICE"`. Do not choose a winning tool on their behalf. Add `--collection` only for a destination they named. If they have not chosen, leave preferences unset; later paper-watch can prefill the most recent choices.

The topic folder contains `research.json`, `comparison.md/.json` when applicable, and `search-results.md/.json`. Add one link to the saved results below the normal tables. No extra status table or search-process commentary is needed.

## Recurring searches

When called by a confirmed `paper-watch` run, use its supplied topic, context, queries, tools, limits, tab mode, and Zotero filter without reopening the form. Read the current saved artifacts at the start of every run. Use `screen_batch.py --exclude-papers PATH` with the run's paper identities to discard previously reported and queued papers **before** enrichment and source quotas; rerun after DOI enrichment. This is local history, not a Zotero absence check. Exclusion from My Library still requires the explicit Zotero option.

Keep sources concurrent and paginate as usual. A routine source is `complete` when its requested eligible target is collected or the accessible results are exhausted; use `partial` for incomplete pagination/rate limits and `blocked` for authentication/access failure. Preserve actual reasons and all eligible overflow records. Return structured records to paper-watch instead of overwriting the student's comparison or tested strategy. In unattended runs, retain blocked sources for the next run and request login in a visible Codex tab when the user returns; do not wait indefinitely, assume consent, or silently substitute a different source.
