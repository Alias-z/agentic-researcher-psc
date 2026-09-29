# Search source instructions

## Choose the route

- **Visible mode:** use each selected website in Codex's visible browser preview. Metadata APIs may fill missing fields while preserving browser discovery IDs and ranks.
- **Background mode:** try the source's official API or connected provider tool first; fall back to its browser route when unavailable or insufficient. Read current tool schemas before calling them.
- **Codex research:** use native web search in either mode. This is iterative web search, not a dedicated Deep research run; browser verification follows the selected tab mode.

## Background API routes

| Source | Search, pagination, and metadata |
| --- | --- |
| PubMed | Use `scholarly_metadata.py pubmed`: ESearch plus batch EFetch. Follow `next_start`. Records supply PMID, title, authors, year, DOI and author abstract when available. |
| UniProt literature | Use `scholarly_metadata.py uniprot`: citations API. Follow `next_url`. Records supply citation ID, DOI/PMID cross-references and `literatureAbstract` when available. This searches protein-linked publications. |
| Scite | Discover provider `search_literature`; use `term`, a small `limit`, and `offset` where supported. The provider contract supplies DOI, authors, abstract, year and journal. Verify access and the current schema. |
| Consensus | Discover provider `search`, then `fetch(id)` for papers to be cited when required by its contract. Do not invent pagination parameters; use browser pagination if the API cannot return enough eligible papers. |
| Semantic Scholar, Scopus AI | Check available official search tools or documented API access. If none is usable, use the browser route. |
| Google Scholar, Scholar Labs | No supported official search API is configured. Use interactive browser search and pagination. |
| Codex research | Use the available first-party web search tool; refine queries and verify unresolved paper facts. |

Helper commands and DOI recovery are in [metadata lookup](metadata-lookup.md).

## Browser search and extraction

Use the following controls as starting points and check the current page before reusing selectors. Read structured arrays from rendered cards with tab-scoped CDP; use visible text and link targets.

| Source | Search and pagination | Metadata and DOI |
| --- | --- | --- |
| **Scite** | `https://scite.ai/search?mode=all&q=...`; cards `div[class*="PaperCard__paperCard"]`. Use the numbered page controls, including **Go to page 2**. | `/reports/` title links; authors, year, journal and expandable `section[aria-label="Abstract"]`. Report pages expose DOI and article type. Screen preprints against the user's filters. |
| **Consensus** | Question search; cards `a[data-testid="search-result"]`. Use **Load more results** until the requested target or an access limit. | Card and surrounding container expose title, year, author, journal and an **AI key takeaway**. Paper details expose `a[href*="doi.org/"]` and **Abstract**. Generated Study Snapshots can contain unrelated fields; do not treat them as article metadata. |
| **Semantic Scholar** | `/search?q=...`; cards `div.cl-paper-row`. Use **navigate to page 2** and later page controls. | Title, authors, journal/date and sometimes a DOI link. Distinguish **TLDR** from the author abstract. **Expand truncated text** can reveal the labeled abstract. |
| **Google Scholar** | `/scholar?q=...`; cards `.gs_r.gs_or.gs_scl`. Numbered pages advance the results, e.g. `start=10`. | `h3 a`: title/publisher URL; `.gs_a`: abbreviated authors/source/year; `.gs_rs`: snippet. DOI and full abstract are not dependable; use metadata lookup for missing fields. |
| **Google Scholar Labs** | `https://scholar.google.com/scholar_labs/search`; enter an English question. **More results** appends cards. Follow the visible sign-in handoff in SKILL.md if access is blocked. | Cards `.gs_r.gs_or.gs_scl` have `data-cid`/`data-rp`; title/author selectors match Scholar. `.gs_rs > div` and `.gs_asl li` contain AI takeaways. Inspect the publisher title URL for an explicit DOI; resolve missing DOIs via metadata lookup. |
| **Scopus AI** | At `https://www.scopus.com/pages/home`, select **Scopus AI** and submit a question. Expand **Show all … references** and **Show more documents** where available. | Expanded documents expose title, authors, journal/year and **Show abstract**. `/pages/publications/{id}` details expose DOI, article type and any Open Access label. The generated answer is not an author abstract. |
| **PubMed** | `https://pubmed.ncbi.nlm.nih.gov/?term=...&sort=relevance`; cards `article.full-docsum`. Use **Navigates to the next page of results.** | Cards expose title, authors, journal/year, DOI, PMID and snippet. Batch EFetch supplies full metadata and abstracts; DOI is `ArticleId IdType="doi"`. |
| **UniProt literature** | `https://www.uniprot.org/citations?query=...`; table rows with `/citations/` links. API pagination follows `Link: rel="next"`. | Rows expose citation ID, title, authors, year and journal. Enrich from citation metadata for DOI/PMID and author abstract, retaining discovery ranks. |

If Scholar CDP reads fail with a paused-document error after pagination, try supported tab-scoped rendered-page evaluation. Alternatively, open a new Codex tab at the page URL actually observed after clicking pagination, preserving tab mode and rank. Do not guess page URLs.

For missing DOI or abstract fields, use [metadata lookup](metadata-lookup.md) before opening individual source or publisher pages. Accept title-based matches only after comparing authors and year. Never treat a search-card PDF link as proof of open access or a generated takeaway as an author finding.

Use Scholar and Scholar Labs interactively. [Scholar's official help](https://scholar.google.com/intl/en/scholar/help.html) does not offer bulk access; do not build a scraping or page-crawling loop.

Institutional access and full-text availability depend on the user's current account and session. Follow SKILL.md's visible login handoff when needed; continue independent sources while waiting.
