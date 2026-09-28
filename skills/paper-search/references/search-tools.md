# Tested search routes — 23–28 September 2026

## Retrieval priority

In **visible mode**, search each selected scholarly website in Codex's visible preview using the browser controls, cards, and pagination documented below. Use metadata APIs only to fill missing fields; retain the browser discovery source and rank. Codex research has no browser search UI and uses native web search in either mode.

In **background mode**, try the selected source's official API or provider MCP tool first, then use browser fallback when needed. The table below applies to background discovery. PubMed and UniProt API searches are live-tested; the Scite and Consensus tool contracts below were inspected, so read their current schemas and check access when selected.

| Source | Background first route | Background browser fallback |
| --- | --- | --- |
| PubMed | Bundled `scholarly_metadata.py pubmed`: ESearch and batch EFetch; paginate with `next_start`. | API unavailable or a required fact remains missing. Keep API order when it works, even if website order differs. |
| UniProt | Bundled `scholarly_metadata.py uniprot`: literature citations API; follow `next_url`. | API unavailable or incomplete for the user's question. |
| Scite | Discover provider `search_literature`; use a focused `term`, small `limit`, and `offset` pagination. Its contract returns DOI, authors, abstract, year, and journal. | Connected API unavailable, access error, or an unmet retrieval requirement. |
| Consensus | Discover provider `search`, then `fetch(id)` for each paper that will be cited; the provider requires fetching before citation. Its current search schema has no pagination parameter. | API access fails or cannot supply enough eligible results; use the tested browser pagination. |
| Semantic Scholar, Scopus AI | Check available official search tools or documented API access first. Read the actual schema; do not guess endpoints or credentials. | No usable supported API, or an unmet retrieval requirement. |
| Google Scholar, Google Scholar Labs | No supported official search API is configured in this skill. | Use the tested interactive browser search and pagination. Do not substitute a third-party scraping API. |
| Codex research | Available first-party web search tool. | Browser only for unresolved paper facts. |

Use official metadata APIs to fill missing DOI/abstract fields before opening individual paper pages. Record API failures internally without adding process notes to the final paper tables.

## DOI lookup, PubMed, and UniProt tests — 28 September 2026

All browser checks used background Codex in-app tabs and read-only CDP extraction. Public metadata requests used the official APIs, without credentials, Zotero access, or PDF downloads. Commands and fields are in [metadata lookup](metadata-lookup.md).

- **DOI recovery:** Google Scholar's `stomatal opening kinetics` search supplied three title links without embedded DOIs: Grantz and Zeiger (1986), Eyland et al. (2021), and Horaruang et al. (2022). The sequential resolver matched their titles, first authors, and years to Crossref records and returned **10.1104/pp.81.3.865**, **10.1093/plphys/kiab114**, and **10.1038/s41477-022-01255-2**. Discovery URLs and ranks 8–10 were retained; no publisher pages were opened.
- **PubMed:** The same query returned 94 records. CDP read the first three cards' titles, authors, years, DOI strings, and PMID links. Clicking the next-page control loaded different cards at ranks 11–20. ESearch plus batch EFetch returned the same first three PMIDs, verified DOI fields, and author abstracts; a second API page returned distinct records with continuing ranks 4–6.
- **UniProt:** Literature search for `SLAC1` returned 96 citations. CDP read the first three table rows' IDs, titles, authors, years, and journals. The official `/citations/search` response supplied those same records plus DOIs and author abstracts. Following its returned `Link: rel="next"` cursor returned three different citations at ranks 4–6. This tests the literature search, not a general scholarly index or every protein.

The updated form submitted PubMed and UniProt selections once, preserved background mode and the three-paper limit, and closed its submission tab. Both tab-mode prefills were checked. The three real Scholar cards passed through the ledger, resolver, and comparison helper with Zotero exclusion off; DOI links and original source ranks were retained without calling the Zotero checker. Conflicting titles, authors, and years were rejected; repeating the DOI lookup used only the cache.

These checks cover two pages and one DOI-recovery batch. They do not establish that every paper has a DOI, abstract, or full text.

## Codex native research test — 25 September 2026

Codex's first-party [web search](https://learn.chatgpt.com/docs/web-search) was tested with **speedy stomata**. An initial query found papers and DOI candidates; focused follow-up queries found the [Oxford Academic article](https://academic.oup.com/plphys/article/186/2/998/6162873), whose publisher page exposed its title, author abstract, and DOI **10.1093/plphys/kiab114**. The same article opened with `cua.createBrowserTab("iab", url, { visible: true })` in Codex's preview; its rendered page showed the title, authors, DOI, and abstract. The [Wiley article](https://onlinelibrary.wiley.com/doi/10.1111/pce.14775) appeared in search, but the web tool's direct page fetch returned 403, so its abstract could not be verified through that route. Search results are leads: report their snippets as source snippets, and inspect a primary record only before making a stronger finding claim or resolving a selected paper's missing fact. This test covered discovery and verification, not Zotero saving or a dedicated Deep research run.

This option means iterative Codex web search within the current task. OpenAI documents the separate [Deep research experience in ChatGPT Work](https://learn.chatgpt.com/docs/web-search); it is not a Codex search mode exposed by this skill. Hosted searches have no visible/background browser tab. Any browser page opened for verification follows the user's selected tab mode.

## Zotero availability and exclusion test — 25 September 2026

The read-only [Zotero local API](https://www.zotero.org/support/dev/web_api/v3/local_api) responded on `127.0.0.1:23119`. A paginated `itemType=-attachment` scan of **My Library** read 2,059 items in under one second. Exact DOI comparison found `10.1111/pce.14775` in Zotero and did not find `10.1111/pce.70509`. Zotero's `q` query returned zero rows even for a known DOI; [official API documentation](https://www.zotero.org/support/dev/web_api/v3/basics) says quick search targets titles and creators by default. The form's green status, checked exclusion option, and one-click saved selection were tested. An unavailable API renders a red status and cannot support an absence claim. These checks do not save papers or inspect group libraries.

The pre-search snapshot mode was tested against the same 2,059-item library. It wrote a temporary index with `0600` permissions; candidate checks reused that index and correctly labeled a known DOI `in_zotero` and a nonexistent DOI `not_found`. The test removed its temporary files. Full per-source search with this exclusion strategy has not yet been run.

The title-match revision was checked against a real My Library item with no DOI: its title, first author, year, and journal matched and the checker returned `in_zotero`. Synthetic checks confirmed that a missing or conflicting field, or conflicting DOI, remains `possible_match` with an explicit reason. Source coverage buckets were checked to sum to screened records; cross-source DOI overlap stayed separate.

Staged Consensus screening was tested on its first three rendered result cards. `screen_batch.py` marked two titles `possible_match` in Zotero and returned only the third as `needs_doi`. Opening that paper's Consensus detail page exposed DOI `10.1111/gcb.13371`; updating the same ledger record changed the count to one confirmed `not_found` toward a seven-paper target. The temporary ledger and snapshot were removed. This proves the early-filter path for one small batch, not a complete multi-source run.

## Scholarly website tests

Test question: **artificial light at night and insect pollination**. All five tested sources were opened in Codex's built-in browser (iab). CDP reads used tab.capabilities.get('cdp') and Runtime.evaluate on the current tab's rendered DOM. Page changes and expansion used tab.click() against a fresh accessibility tree. Selectors describe the tested pages; inspect the current DOM before reuse.

Concurrent tab test: Scite and Semantic Scholar opened in separate background Codex tabs with `Promise.allSettled`; simultaneous tab-scoped `Runtime.evaluate` calls found ten rendered result cards on each page. Both temporary tabs were closed. This confirms concurrent tab reads, not a full multi-source search run.

Earlier compare-mode mini test: one DOI was verified from a Scite report and one from a Semantic Scholar paper page for this question. Separate one-paper ledgers passed through the comparison helper. Its output format has since been simplified to source lists only. The form was selected and submitted once in a visible Codex preview tab, then that tab was closed. A full multi-source search run has not yet been tested.

| Source | Search and pagination observed | Candidate fields and DOI route |
| --- | --- | --- |
| **Scite** | https://scite.ai/search?mode=all&q=...; result cards div[class*="PaperCard__paperCard"]. Clicking accessible **Go to page 2** changed the URL to page=2 and loaded new cards. | Cards exposed title link /reports/..., authors, year, journal, and expandable section[aria-label="Abstract"]. Report rendered DOI and article type. The 2026 Li result was labeled **Preprint**; screen before collecting. |
| **Consensus** | Question search opened a results panel with a[data-testid="search-result"]. Clicking **Load more results** increased rendered cards from 20 to 30 in the anonymous view; no further load button appeared. On 25 September, the current Codex browser session showed a signed-in Consensus account; an actual sign-in gate was not tested. | Card exposed title, year, lead author, journal, and **AI key takeaway**. Its /papers/.../ detail page exposed an a[href*="doi.org/"] and a full **Abstract**. Do not treat its generated Study Snapshot as article metadata: in this test its snapshot contained unrelated BMI/older-adult fields. If a later session blocks these details behind sign-in, use the visible login handoff in SKILL.md. |
| **Semantic Scholar** | /search?q=... rendered 10 div.cl-paper-row cards per page, 53 total for the test query. **navigate to page 2** changed the URL and loaded different cards. | Card exposed title, authors, journal/date, a[href*="doi.org/"] when present, and excerpt or **TLDR**. **Expand truncated text** revealed a labeled author **Abstract** for the tested paper. Resolve missing DOIs through the documented metadata lookup, then inspect source details only if unresolved. |
| **Google Scholar** | /scholar?q=... rendered 10 .gs_r.gs_or.gs_scl cards. Clicking page **2** changed the URL to start=10 and showed different cards. Use only a small interactive check; [Scholar does not provide bulk access](https://scholar.google.com/intl/en/scholar/help.html). | h3 a supplied title/publisher link, .gs_a abbreviated authors/source/year, .gs_rs a **snippet**. DOI and full abstract were not dependable. Use the documented DOI resolver when no DOI is embedded in the title URL. Raw CDP read page 1. After in-tab pagination it reported a paused-document error; opening a **new Codex tab at the page-2 URL observed in the browser** restored raw CDP extraction. Read-only tab.playwright.evaluate() also worked on the paginated tab. |
| **Google Scholar Labs** | `https://scholar.google.com/scholar_labs/search` redirected to Google sign-in in Codex's visible preview. After the user signed in, an English question about stomatal responses returned 10 cards. Clicking **More results** appended 10 more, for 20 on the same session page; the button remained available. [Google's 2025 launch post](https://scholar.googleblog.com/2025/11/scholar-labs-ai-powered-scholar-search.html) described Labs as experimental, English-only, and limited to some signed-in users; availability may change. | CDP read `.gs_r.gs_or.gs_scl` cards with `data-cid` and `data-rp`; `h3 a` gave title/publisher URL, `.gs_a` gave abbreviated authors/journal/year, `.gs_rs > div` and `.gs_asl li` gave **AI-generated takeaways**. A Wiley title URL contained its DOI. An Oxford title URL did not; its publisher page showed title, author abstract, and DOI `10.1104/pp.114.237107`. Resolve missing DOIs through metadata lookup and label the AI takeaway; do not convert it into an author finding. |
| **Scopus AI** | At https://www.scopus.com/pages/home select **Scopus AI**, enter a natural-language question, and submit. The ETH session returned a summary with nine cited references. **Show all 9 references** opened all nine. **Show more documents** opened five foundational and ten related documents in separate tabs; no further page control was observed. | Each expanded document exposed title, authors, journal, year, citations, and **Show abstract**. The paper detail page `/pages/publications/{id}` exposed article type, Open Access label when applicable, DOI, authors, and full author abstract. Read the rendered links and text; do not treat the generated summary as an abstract. |
| **PubMed** | `https://pubmed.ncbi.nlm.nih.gov/?term=...&sort=relevance`; `article.full-docsum` cards. The **Navigates to the next page of results.** control loaded page 2. API pagination uses ESearch `retstart`/`retmax`. | Cards expose title, authors, journal/year, DOI, PMID, and snippet. Batch EFetch supplies full author metadata and abstracts. Extract DOI from `ArticleId IdType="doi"`; use general metadata lookup for records without it. |
| **UniProt literature** | `https://www.uniprot.org/citations?query=...`; table rows with `/citations/` links. Official `/citations/search` API pagination follows its `Link: rel="next"` cursor. | Table exposes citation ID, title, authors, year, and journal. JSON `citation` adds DOI/PubMed cross-references and `literatureAbstract` when present. Search covers publications linked to protein records; preserve service order. |

For page-scoped CDP extraction, use the card selector in the table, then read only visible text and link hrefs. Scite's card title is its /reports/ anchor; Consensus's card title and takeaway are in the search-result anchor, while year/author/journal sit in its surrounding card. Semantic Scholar's DOI is a doi.org anchor inside the paper row. Both Google Scholar modes expose the publisher title anchor inside h3; only Labs adds AI takeaways in `.gs_rs` and a **More results** control. On Scopus AI, a CDP read of visible `a[href*="/pages/publications/"]` returned the reference and related-document links. Do not infer open-access status from a search-card PDF link. Resolve missing DOIs with [metadata lookup](metadata-lookup.md) regardless of Zotero exclusion, using batch official records and a sequential cached fallback. Open source or publisher details only for unresolved facts. Compare title, year, and authors before accepting title-search matches.

## Prior end-to-end tests (background evidence)

These tests checked that each discovery source could lead to a publisher DOI page and then a verified Zotero save. They are historical evidence; `paper-search` itself returns papers and DOIs without saving. The first four examples used visible preview tabs; Scopus AI used a background tab. Each PDF child was checked on disk for a %PDF- header. These examples do not imply that every paper will attach a PDF.

| Discovery source | DOI and publisher | Zotero item / PDF child |
| --- | --- | --- |
| Scite | 10.1111/een.12174 — [Wiley](https://resjournals.onlinelibrary.wiley.com/doi/10.1111/een.12174) | 2325KQE6 / LMCH4SF6 |
| Consensus | 10.1093/jpe/rtag160 — [Oxford Academic](https://academic.oup.com/jpe/advance-article/doi/10.1093/jpe/rtag160/8731923) | 9VB2NRK5 / Q6XN2ZNR |
| Semantic Scholar | 10.1007/s43538-022-00134-w — [Springer Nature](https://link.springer.com/article/10.1007/s43538-022-00134-w) | Z42NMKW5 / FDDAVELE |
| Google Scholar | 10.1002/ecs2.2550 — [Wiley](https://esajournals.onlinelibrary.wiley.com/doi/10.1002/ecs2.2550) | 4VE6FGCM / TP78QSTZ |
| Scopus AI | 10.1093/icb/icab010 — [Oxford Academic](https://academic.oup.com/icb/article/61/3/1122/6173993) | 4ZDD9NR5 / USNHX3I9; background Codex tab |

## University access checked separately

| Source | ETH | UZH | Basel |
| --- | --- | --- | --- |
| Scite | [Library access](https://library.ethz.ch/en/find-media/media-types/databases-standards-patents/scite.html); confirmed in tested browser | [Library access](https://www.ub.uzh.ch/en/ueber-die-ub/news/sciteai0.html) | Licence not confirmed |
| Consensus | [Pro access](https://library.ethz.ch/en/find-media/media-types/databases-standards-patents/consensus.html) | Public tier; institutional licence not confirmed | [Premium access](https://ub.unibas.ch/en/search-find/ai/) |
| Semantic Scholar, Google Scholar | Public search | Public search | Public search |
| PubMed, UniProt literature | Public search and metadata API | Public search and metadata API | Public search and metadata API |
| Google Scholar Labs | Google sign-in and limited rollout; tested in Codex preview | Account eligibility not checked | Account eligibility not checked |
| Scopus AI | ETH institution shown and search tested in browser; [ETH Library announcement](https://library.ethz.ch/en/about-us-and-locations/news/news-articles/2025/02/discover-the-new-ai-powered-tools-by-the-eth-library-scopus-ai-and-scite.html) | Licence not checked | Licence not checked |

Publisher full-text access still depends on each student's session. The Scopus AI test paper was not labeled Open Access in Scopus; Zotero saved its publisher PDF in `test`, and the file had a `%PDF-` header. This proves one non-OA example, not all papers or publishers.

## Investigated, not yet supported — 25 September 2026

| Tool | Background-tab finding | Missing proof |
| --- | --- | --- |
| [LeapSpace](https://www.sciencedirect.com/leapspace) | Search box loaded, but **Sign in to ask** led through Elsevier institutional selection to ETH's username/password page. [ETH Library](https://library.ethz.ch/en/find-media/media-types/databases-standards-patents/sciencedirect-ai.html) restricts access to the `ethz.ch` domain. | Search results, DOI extraction, and Zotero save require an authenticated session. |
| [Elicit](https://elicit.com/) | **Try now** opened the sign-up page. | No search results or DOI route tested without an account. |
| [Web of Science Research Assistant](https://www.webofscience.com/wos/alldb/basic-search) | ETH Zurich was shown on the ordinary search page, but **Research Assistant** was rendered as a disabled tab (`tab-disabled`); its info icon only explained the product. | Assistant search and result extraction unavailable in this session. Ordinary Web of Science search is a separate route. |
| [ResearchRabbit](https://app.researchrabbit.ai/) | The app opened its login form with email/password or Google sign-in. | Seed-paper graph and DOI extraction require an account session. |
