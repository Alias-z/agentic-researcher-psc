---
name: zotero-save
description: Save selected publisher papers and available PDFs through Zotero Connector in Codex's browser, create or select the destination collection, and verify results. Not for library-wide searches, citation exports, or BibTeX/RIS imports.
---

# Save selected papers with Zotero Connector

Use this for papers the user has selected by DOI, publisher URL, or position in a prior search result. Do not perform a new topic search. Keep each publisher DOI page in Codex's built-in browser so its institutional session is available to the official Zotero Connector. Zotero desktop must be running, the Connector installed in the built-in browser, and page-scoped CDP access enabled. This skill uses Zotero desktop's built-in local server directly; it does not require a Codex Zotero plugin, a separately configured MCP server, or a zotero.org API key. The student does not need to run code.

An explicit request to use **zotero-save** uses this workflow throughout. The optional **Zotero plugin** handles existing-library and citation tasks; its BibTeX/RIS imports are not a substitute for publisher Connector saves with PDF verification. Do not install it to resolve this skill's connection or collection steps. Read [Zotero routes](references/tool-routing.md) when both capabilities are available or their roles are unclear.

## Before saving

Before opening publisher tabs, ask for any missing choices in one short question and wait for the answer: which papers to save, the destination Zotero collection, and whether to use visible Codex preview tabs (recommended) or background tabs. Use choices already given without asking again. If the user says "use default tabs," use visible tabs. Do not treat papers returned by `paper-search` as automatically selected for saving.

### Check Zotero and the destination

Run the bundled, non-mutating helper before publisher work, using `python3` or the Python executable from `load_workspace_dependencies` if needed:

```text
python scripts/check_zotero.py --collection "USER'S COLLECTION"
```

It probes desktop Connector ping, local collection access, and the selected destination directly on `127.0.0.1:23119`, bypassing HTTP proxies. For a group library add `--library /api/groups/<groupID>`; add `--parent-key <key>` when resolving a particular subcollection, or `--parent-key ""` for top level. It does not edit preferences, create collections, or save papers. `local_checks_passed` verifies only the local HTTP routes; browser extension and Computer Use access remain separate checks.

Act on the measured result:

- **connection_refused:** open Zotero desktop with available native controls and retry once. A closed desktop port is separate from a missing browser extension or plugin.
- **access_denied (403):** check Zotero's **Settings → Advanced → Allow other applications on this computer to communicate with Zotero** and the requested library's access. Enable the setting if it is off. If it is already on, report the denied endpoint and check the running Zotero instance; do not keep asking the user to enable it or claim it is disabled.
- **endpoint_unavailable (404), timeout, transport_error, or unexpected_response:** retain the exact route, status, and returned Zotero version for diagnosis. Do not turn these into a generic “Zotero server not connected” or change preferences without evidence.

A working desktop Connector server does not prove local library access or that the browser extension is installed. A plugin/MCP error does not prove the desktop server is down. Report the specific failed check; keep passing checks intact. This skill needs local reads to verify the record, collection, and PDF even if Connector saving alone is possible.

Resolve the requested collection and its parent/library before saving. A `missing` destination means create it; it is not a connection error. An `ambiguous` destination needs a parent/library choice. If creation or selection is needed, call `cua.getApp("Zotero")`, read the native app state, and use the current **New Collection…** control and name field. Use fresh observed control IDs, never IDs copied from another session. A named destination in an authorized save request permits creating that destination when absent; use **New Subcollection…** under the specified parent when needed. Verify the resulting collection key by rerunning the helper. If native controls are actually unavailable, ask the user to create/select it and wait. Do not claim creation is unsupported merely because a plugin has no creation command or an older local API lacks writes.

Select the destination in Zotero desktop before activating the Connector. `POST /connector/getSelectedCollection` with JSON `{}` reports the current target and whether it is editable; verify the requested library/collection. Its internal IDs differ from local API collection keys. Keep publisher browsing in Codex's preview. Stop if the destination cannot be selected or is not writable; do not silently save to My Library or a different collection.

Before saving, establish all three independently: local reads/Connector server work, the exact writable destination is selected, and publisher tabs have the browser controls/CDP required below. Check the browser extension through the actual save interception; the helper does not test it. After a failed click, check the destination for an item before retrying. Keep metadata-only results distinct from verified PDFs.

## Process papers concurrently

Use **adaptive concurrency by default**: size the pipeline according to the number of selected papers, browser responsiveness, and publisher rate limits. Honor an optional user-specified `concurrency` limit; `1` means sequential processing. Do not impose a fixed three-paper ceiling. Increase the number in flight when independent work is ready and responses remain healthy; reduce it when there are measured resource constraints or throttling. Keep the chosen visible/background tab mode. Do not run the full open → save → wait for PDF → verify cycle separately for every paper.

- Resolve/create/select the destination once, then read its items with pagination and build a normalized DOI index. Deduplicate selected DOIs before scheduling them, and reserve each scheduled DOI so two jobs cannot save it.
- Prepare independent publisher tabs concurrently: resolve missing DOIs, load pages, and read article metadata/access status. Use `Promise.allSettled` for independent tab reads where the browser API supports it, and inspect every result. A login or page challenge blocks that paper, not the other ready papers.
- Keep collection selection and trusted Connector clicks in one sequential queue. Check the destination before each click, then use a fresh accessibility state from that exact tab. Never share a tab, temporary link ID, or accessibility index between paper jobs.
- As soon as the matching record appears in the correct collection, queue its attachment checks and start the next ready paper. **Do not wait for that PDF to finish before proceeding.** Keep the originating tab open while the Connector is still working; navigating it to the next paper can interrupt the save.
- Check pending records and their child attachments concurrently in short rounds while other tabs load or saves start. Read the collection once per round, then query each matched item's children independently. Match results by DOI and item key, not completion order. Refill the pipeline as papers finish; never let an entire batch wait for one slow PDF.
- A PDF attachment may appear before its file finishes downloading. Keep checking for the saved file where local access is available. Use a bounded wait, extending it only when there is observed progress; report a remaining download as **PDF pending/unverified**, not as a confirmed absent PDF. After a failed click, check for an existing record before any retry.

The Connector [creates per-page save sessions](https://github.com/zotero/zotero-connectors/blob/master/src/common/inject/pageSaving.js), and Zotero desktop [associates attachments with their save session](https://github.com/zotero/zotero/blob/master/chrome/content/zotero/xpcom/server/server_connector.js). Keep the destination fixed while these jobs are pending. This supports overlapping page preparation and attachment work; it does not require simultaneous UI clicks or direct `/connector/saveItems` calls.

## Save each paper

Apply these steps within the pipeline above; completion of step 6 must not block preparation or verification of other papers.

1. For each selected paper, open its original publisher DOI page in the built-in browser. If a prior search result did not show a DOI, resolve the selected paper first from that source's paper detail or a title lookup corroborated by authors and year; do this only for selected papers. If the DOI cannot be resolved, report that paper as unresolved instead of guessing or saving a different work. Check the DOI, article type, access status, and requested Zotero collection. If the user requests non-open-access research, do not infer that from a PDF link alone.
2. Check whether the DOI is already in the destination collection before saving, to avoid duplicates.
3. Obtain that tab's `cdp` capability through `mcp__cua_repl`. Use `Runtime.evaluate` only in this publisher tab to add a temporary, visible `<a href="https://www.zotero.org/save">Save article with Zotero Connector</a>` element. Give it a unique ID and fixed positioning so the browser accessibility tree exposes it.
4. Read a fresh `getAXState()`, locate that link by ID or accessible name, and activate it with `tab.click(index)`. This must be a real browser click: Zotero Connector requires a trusted, unmodified primary click. Do not call the DOM element's `.click()` method or use CDP to synthesize a click.
5. Remove the temporary element with `Runtime.evaluate` after the click. If the page navigated to zotero.org, the Connector did not intercept the link; report the failure instead of claiming a save.
6. Verify a new item with the expected DOI in the requested collection and a child attachment whose `contentType` is `application/pdf`. Report each paper as saved with PDF, saved without PDF, already present, failed, or PDF pending/unverified when downloading has not finished. Treat metadata-only saves as incomplete when the user requested a PDF. Avoid repeating the save blindly, which can create duplicates.

Zotero's [Connector source](https://github.com/zotero/zotero-connectors/blob/master/src/common/inject/inject.jsx) documents this built-in link behavior in `_addZoteroButtonElementListener()`. Its handler accepts trusted primary clicks on `zotero.org/save` links and calls `onZoteroButtonElementClick()`, the same save action used by its toolbar button. This route does not require browser-wide CDP access or a Connector fork.

## Verify locally

With Zotero desktop running and local API access enabled, read `GET http://127.0.0.1:23119/api/users/0/collections?format=json`, `GET /api/users/0/collections/{collectionKey}/items?format=json`, and `GET /api/users/0/items/{itemKey}/children?format=json` for My Library. For a group destination, use the returned collection's `/api/groups/{groupID}/` library prefix. Match the collection and DOI exactly. For a PDF, check that the attachment has `contentType: application/pdf` and a filename. Where local file access is available, confirm that the saved attachment file exists and is a PDF. These checks inspect the Zotero save; they do not download a separate publisher PDF. See [local API requirements](https://www.zotero.org/support/dev/web_api/v3/local_api) and [collection controls](https://www.zotero.org/support/collections_and_tags#creating_collections).

The first observed test on 23 September 2026 saved `10.1111/pce.70864` with a PDF. A fresh-paper test saved `10.1111/pce.70548` with a PDF. Another article, `10.1111/pce.70862`, produced a record without an attachment, so verify every paper individually.

The 23 September saves used an existing `test` collection. In a separate session on 28 September, Codex created **CLL** through Zotero desktop's native collection dialog using `cua.getApp("Zotero")`, clicks, and `setValue`; a direct local API read verified the new collection. That session then saved four distinct papers through the browser Connector and verified all four PDF files. No Codex Zotero plugin was used. Separate direct Connector ping, collection listing, and selected-target checks also returned HTTP 200 on the teaching Mac.
