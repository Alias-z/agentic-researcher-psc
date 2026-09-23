---
name: zotero-connector-collect
description: Save publisher article pages to Zotero through the installed Zotero Connector in Codex's built-in browser, then verify the record and PDF in a requested collection.
---

# Collect a paper with the Zotero Connector

Use this when the user wants Codex to collect an article through the official Zotero Connector in Codex's built-in browser. Keep the publisher DOI page in that browser so its institutional session is available to the Connector. The student needs Zotero desktop running, the Connector installed in the built-in browser, and page-scoped CDP access enabled. The student does not need to run code.

## Save

1. Open the original publisher article page in the built-in browser. Check the DOI, article type, access status, and requested Zotero collection. If the user requests non-open-access research, do not infer that from a PDF link alone.
2. Check whether the DOI is already in the destination collection before saving, to avoid duplicates.
3. Obtain that tab's `cdp` capability through `mcp__cua_repl`. Use `Runtime.evaluate` only in this publisher tab to add a temporary, visible `<a href="https://www.zotero.org/save">Save article with Zotero Connector</a>` element. Give it a unique ID and fixed positioning so the browser accessibility tree exposes it.
4. Read a fresh `getAXState()`, locate that link by ID or accessible name, and activate it with `tab.click(index)`. This must be a real browser click: Zotero Connector requires a trusted, unmodified primary click. Do not call the DOM element's `.click()` method or use CDP to synthesize a click.
5. Remove the temporary element with `Runtime.evaluate` after the click. If the page navigated to zotero.org, the Connector did not intercept the link; report the failure instead of claiming a save.
6. Verify a new item with the expected DOI in the requested collection and a child attachment whose `contentType` is `application/pdf`. Report metadata-only saves as incomplete when the user requested a PDF. Avoid repeating the save blindly, which can create duplicates.

Zotero's [Connector source](https://github.com/zotero/zotero-connectors/blob/master/src/common/inject/inject.jsx) documents this built-in link behavior in `_addZoteroButtonElementListener()`. Its handler accepts trusted primary clicks on `zotero.org/save` links and calls `onZoteroButtonElementClick()`, the same save action used by its toolbar button. This route does not require browser-wide CDP access or a Connector fork.

## Verify locally

With Zotero desktop running, its read-only local API can list `GET http://127.0.0.1:23119/api/users/0/collections?format=json`, `GET /api/users/0/collections/{collectionKey}/items?format=json`, and `GET /api/users/0/items/{itemKey}/children?format=json`. Match the collection and DOI exactly. For a PDF, check that the attachment has `contentType: application/pdf` and a filename. Where local file access is available, confirm that the saved attachment file exists and is a PDF. These checks inspect the Zotero save; they do not download a separate publisher PDF.

The first observed test on 23 September 2026 saved `10.1111/pce.70864` with a PDF. A fresh-paper test saved `10.1111/pce.70548` with a PDF. Another article, `10.1111/pce.70862`, produced a record without an attachment, so verify every paper individually.
