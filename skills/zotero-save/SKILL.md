---
name: zotero-save
description: Save user-selected paper DOIs or publisher pages to a Zotero collection through Zotero Connector, then verify each record and PDF.
---

# Save selected papers with Zotero Connector

Use this for papers the user has selected by DOI, publisher URL, or position in a prior search result. Do not perform a new topic search. Keep each publisher DOI page in Codex's built-in browser so its institutional session is available to the official Zotero Connector. Zotero desktop must be running, the Connector installed in the built-in browser, and page-scoped CDP access enabled. The student does not need to run code.

## Before saving

Before opening publisher tabs, ask for any missing choices in one short question and wait for the answer: which papers to save, the destination Zotero collection, and whether to use visible Codex preview tabs (recommended) or background tabs. Use choices already given without asking again. If the user says "use default tabs," use visible tabs. Do not treat papers returned by `paper-search` as automatically selected for saving.

## Save

1. For each selected paper, open its original publisher DOI page in the built-in browser. If a prior search result did not show a DOI, resolve the selected paper first from that source's paper detail or a title lookup corroborated by authors and year; do this only for selected papers. If the DOI cannot be resolved, report that paper as unresolved instead of guessing or saving a different work. Check the DOI, article type, access status, and requested Zotero collection. If the user requests non-open-access research, do not infer that from a PDF link alone.
2. Check whether the DOI is already in the destination collection before saving, to avoid duplicates.
3. Obtain that tab's `cdp` capability through `mcp__cua_repl`. Use `Runtime.evaluate` only in this publisher tab to add a temporary, visible `<a href="https://www.zotero.org/save">Save article with Zotero Connector</a>` element. Give it a unique ID and fixed positioning so the browser accessibility tree exposes it.
4. Read a fresh `getAXState()`, locate that link by ID or accessible name, and activate it with `tab.click(index)`. This must be a real browser click: Zotero Connector requires a trusted, unmodified primary click. Do not call the DOM element's `.click()` method or use CDP to synthesize a click.
5. Remove the temporary element with `Runtime.evaluate` after the click. If the page navigated to zotero.org, the Connector did not intercept the link; report the failure instead of claiming a save.
6. Verify a new item with the expected DOI in the requested collection and a child attachment whose `contentType` is `application/pdf`. Report each paper as saved with PDF, saved without PDF, already present, or failed. Treat metadata-only saves as incomplete when the user requested a PDF. Avoid repeating the save blindly, which can create duplicates.

Zotero's [Connector source](https://github.com/zotero/zotero-connectors/blob/master/src/common/inject/inject.jsx) documents this built-in link behavior in `_addZoteroButtonElementListener()`. Its handler accepts trusted primary clicks on `zotero.org/save` links and calls `onZoteroButtonElementClick()`, the same save action used by its toolbar button. This route does not require browser-wide CDP access or a Connector fork.

## Verify locally

With Zotero desktop running, its read-only local API can list `GET http://127.0.0.1:23119/api/users/0/collections?format=json`, `GET /api/users/0/collections/{collectionKey}/items?format=json`, and `GET /api/users/0/items/{itemKey}/children?format=json`. Match the collection and DOI exactly. For a PDF, check that the attachment has `contentType: application/pdf` and a filename. Where local file access is available, confirm that the saved attachment file exists and is a PDF. These checks inspect the Zotero save; they do not download a separate publisher PDF.

The first observed test on 23 September 2026 saved `10.1111/pce.70864` with a PDF. A fresh-paper test saved `10.1111/pce.70548` with a PDF. Another article, `10.1111/pce.70862`, produced a record without an attachment, so verify every paper individually.
