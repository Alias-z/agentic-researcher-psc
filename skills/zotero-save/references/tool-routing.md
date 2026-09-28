# Zotero routes

| User task | Route |
| --- | --- |
| Discover papers by topic and return DOIs | `paper-search`; Zotero is checked only when exclusion is selected. |
| Save selected publisher papers and available PDFs | `zotero-save`; use the Connector in Codex's browser with its publisher session. |
| Create/select the destination for that save | Zotero desktop through Computer Use, then verify with the local API. |
| Search existing Zotero items, export BibTeX, insert citations, read indexed text, or import supplied BibTeX/RIS | The optional Zotero plugin can handle these library tasks. |

An explicit `zotero-save` request keeps the Connector save workflow even when the plugin is installed. The plugin may assist a separate library task; its absence or tool failure does not establish that Zotero desktop is disconnected. Direct local probes determine that.

## Plugin inspection — 28 September 2026

The installed Zotero plugin **0.1.2** contains a Python helper using the desktop's local HTTP server. Its commands cover status/probes, enabling the API and restarting Zotero, items/collections/tags/groups, search, BibTeX export, formatted citations, draft citation insertion, attachment paths, indexed full text, and BibTeX/RIS imports. Its current helper has no collection creation command and no publisher-browser Connector activation workflow. Importing records is a library write, but does not establish that a publisher PDF was obtained using the browser's institutional session.

Its read-only `status --json` command returned API and Connector HTTP 200 with Zotero 10.0.4 on the teaching Mac. Import commands were inspected in source; no records were imported during this inspection.

The plugin's reference says the local API is always read-only. This is outdated for Zotero 10+: [official documentation](https://www.zotero.org/support/dev/web_api/v3/local_api) describes authorized local writes. Do not infer available commands from API capabilities or repeat that obsolete limit. Our tested collection creation route uses native desktop controls.
