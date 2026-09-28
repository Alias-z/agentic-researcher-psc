# DOI and public metadata lookup

Resolve DOIs for eligible papers whether Zotero exclusion is on or off. Missing from a search card does not mean a paper has no DOI. Keep the discovery source, URL, and rank; store the verification record separately as `doi_provenance`.

## Lookup order

1. Use the selected source's official API or provider MCP search response and metadata-fetch method first. Prefer batch identifiers or citation exports when supported. A browser visit is not a prerequisite. For a browser fallback result already collected, reuse its DOI link or publisher title URL without opening another page.
2. For PMID-linked papers, use batch PubMed metadata. UniProt's literature API already supplies DOI cross-references and abstracts. Missing fields should trigger API enrichment before browser detail pages.
3. Send unresolved candidates from all sources through **one sequential** `resolve-dois` queue with a shared cache. The helper tries batch PMID lookup, Crossref metadata, then exact-title PubMed search. It accepts a title-query match only when the normalized title and supplied year/first author agree. Conflicts and multiple matching DOIs remain unresolved. Metadata retrieved this way is enrichment, not a new discovery source.
4. Inspect the source detail only for remaining unresolved candidates; use its DOI link or citation export. Open the publisher only if those routes still lack the needed fact. For metadata conflicts, compare the actual source record rather than selecting the first search hit.

Do not open every publisher page. Do not label a DOI as unavailable until the lookup and relevant detail check have actually been attempted. If a service blocks lookup, record that specific limit. Keep genuinely DOI-less papers in results when exclusion is off.

## Helper

Use the same Python interpreter as the intake form; only the standard library is needed. All output and cache files are temporary with `0600` permissions. No command contacts Zotero or downloads PDFs.

```text
python scripts/scholarly_metadata.py --cache DOI_CACHE.json resolve-dois \
  --input CANDIDATES.json --output RESOLVED.json
```

Input is a JSON array of ledger candidates. Output contains `records` (the enriched candidates) and `errors`. Submit `records` back to `screen_batch.py` with unchanged `source_id`. A verified DOI includes `doi_verified: true`, `doi_status: verified`, and `doi_provenance`. An unresolved record has `doi_reason`; use that to decide the next detail check. `needs_doi` applies with either Zotero option.

The helper caches requests, sends NCBI requests at most 2.5 times/second, serializes Crossref requests at most once/second, and retries transient errors with bounded backoff. Run one resolver process across sources; do not launch one per source or overlap it with a PubMed helper command. Other independent sources can advance concurrently using separate caches. Delete caches with the other temporary search files.

## PubMed

Start with ESearch and batch EFetch XML, without opening PubMed in the browser:

```text
python scripts/scholarly_metadata.py --cache PUBMED_CACHE.json pubmed \
  --query "stomatal opening kinetics" --size 5 --start 0 --output PUBMED_PAGE.json
```

Read `records`, screen topic/filters, then pass `next_start` as the next `--start`. Stop when the eligible per-source target is reached or `next_start` is null. `source_rank` continues across pages. PubMed parses queries and supports field/date filters; check `query_translation` rather than assuming every term was interpreted literally. For example, append `AND 2017:3000[dp]` for papers published after 2016, then verify returned years.

Keep the API's returned order. PubMed's website can rank the same query differently; this alone does not justify switching to browser retrieval. If the API is unavailable or lacks a required fact, browser fallback is `https://pubmed.ncbi.nlm.nih.gov/?term=<encoded query>&sort=relevance`. CDP reads `article.full-docsum` cards with title links, authors, journal/year, DOI, PMID, and snippets. Follow **Navigates to the next page of results.**; the tested page-2 URL uses `page=2`.

EFetch supplies title, full authors, journal, publication dates, PMID, author abstract, and DOI from `ArticleId IdType="doi"` (with an `ELocationID` fallback). If no DOI is recorded, use the general lookup above. PubMed is publicly accessible; biomedical and life-science coverage does not include all literature. Book records are not handled by this article helper; screen them separately if requested.

Official docs: [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25499/), [NCBI request limits](https://eutilities.github.io/site/API_Key/usageandkey/).

## UniProt literature

Start with the official literature API, without opening UniProt in the browser. It searches publications linked to protein records, including curated and computationally mapped citations. For a protein-specific question, terms such as **SLAC1** work. Return publications rather than protein entries; coverage is protein-related literature.

```text
python scripts/scholarly_metadata.py --cache UNIPROT_CACHE.json uniprot \
  --query SLAC1 --size 5 --output UNIPROT_PAGE.json
```

Continue with the exact returned `next_url`, passing `--next-url "<returned URL>" --start <records consumed>` and the same query. Follow the server's cursor; do not invent page numbers. Screen explicit user filters before counting, and preserve the service's result order. Do not call that order a validated relevance score.

The JSON `results[].citation` contains title, authors, journal, `publicationDate`, `literatureAbstract`, and `citationCrossReferences` with DOI/PubMed IDs. If an abstract is absent and the supplied information does not support a useful paper description, use batch PMID metadata before source-detail fallback. A missing abstract does not require an empty summary; follow [Paper summaries](../SKILL.md#paper-summaries). An empty result set is a coverage limit, not an API failure.

If API retrieval cannot complete the search, use `https://www.uniprot.org/citations?query=<encoded query>`. CDP reads table rows containing `a[href*="/citations/"]`: ID, title, authors, year, and journal. Use an identified protein's **Publications** section only when the question needs that protein's linked references.

Official docs: [UniProt literature API](https://www.uniprot.org/api-documentation/support-data), [programmatic access](https://www.uniprot.org/help/programmatic_access).
