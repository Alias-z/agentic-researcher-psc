# Instructor setup audit — 23 September 2026

Observations from the teaching Mac. [Student setup instructions](../workshop/00-start-here.md).

| Requirement | Current observation |
| --- | --- |
| Codex built-in browser (`@Browser`) | Working. Codex can read and click publisher pages in the right-side browser. |
| Browser and Computer Use capability | Working in the built-in browser. A local screenshot shows **Any App** on and Google Chrome connected. The student instructions follow this settings page. |
| **Enable full CDP access** | A local screenshot shows the switch on under **Computer use → Google Chrome**. Page-scoped CDP `Runtime.evaluate` also succeeded on a live Wiley DOI tab in the built-in browser. |
| Zotero Connector in the built-in browser | A local screenshot shows Zotero Connector installed and enabled. Agent-triggered Connector saves produced metadata and PDFs for `10.1111/pce.70864` and `10.1111/pce.70548`; `10.1111/pce.70862` saved metadata without a PDF. |
| Zotero desktop and `test` collection | Zotero is running. Local API reads respond, and `test` exists. |
| Zotero automatic PDF preference | Not read directly. The two successful PDF saves show that PDF attachment worked for those papers. Check **Settings → General → File Handling** before class. |
| Institutional access | The tested Wiley pages showed **Access By ETH-Bibliothek** and **Full Access**. Students need their own institution's access in the browser profile they use. |
| Google Chrome installation | Required by the workshop setup and installed on this Mac. |
| Regular Chrome connection to Codex | A local screenshot shows **Google Chrome: Browser extension installed** with **Manage**. The `@Chrome` Zotero workflow has not been tested for this exercise. |
| macOS Screen Recording and Accessibility | Individual permission values were not inspected. Check them if the class will ask Codex to control native app windows. |

**Pass:** Save one article through Zotero Connector from its publisher DOI page. Verify its DOI and collection, then open the PDF attachment in Zotero.

## Slide review — 28 September 2026

- Setup instructions were checked against the saved teaching screenshots. Direct inspection of Codex's own settings was blocked by Computer Use.
- Removed the separate plugin configuration step from the Computer Use slide. The slide now describes **Settings → Computer use → Any App**.
- Confirmed the download pages, clarified selecting Codex after sign-in, and kept Zotero Connector installation inside Codex's browser.
- The local `skill-installer` instructions say installed skills become available on the next turn. The guide explains how to select them with `@` when needed later.
- The distributed skills are `skills/paper-search` and `skills/zotero-save`, replacing `skills/zotero-connector-collect`.
- Added the instructor's Zotero Advanced settings screenshot showing local access enabled, and the Codex Plugins screenshot showing the Zotero listing. Red outlines mark the controls; original screenshots are preserved.
- Our skills discover papers and save them through Connector. The Zotero plugin is for later library reading and citations; saving with our skill does not require it.

References: [desktop setup](https://learn.chatgpt.com/docs/quickstart), [browser and CDP](https://learn.chatgpt.com/docs/browser), [Computer Use](https://learn.chatgpt.com/docs/computer-use), [plugins](https://learn.chatgpt.com/docs/plugins), [Zotero local access](https://www.zotero.org/support/dev/web_api/v3/local_api).

## Reading notes and setup update — 29 September 2026

- Added `paper-reading` to the installation prompt and explained the three skill roles in the setup guide. The optional Zotero plugin supports general library searches and citation export; reading notes use the skill's bundled helper.
- The guide and exercise prompts explain immediate Markdown saves, generated Zotero child notes beside PDFs, source links, keyword search, human-review status, and refreshing the Zotero copy after manual file edits. The Markdown folder requires its own backup.
- Rechecked Zotero's local API documentation: writes require Zotero 10+ and authorization. One-time **Allow** covers one API write; it does not mark note content as human-reviewed.
- Tested the reading workflow on two existing cell-image segmentation papers after the BAM1 trial: *Cellpose 2.0* (DOI `10.1038/s41592-022-01663-4`) and *Segmentation metric misinterpretations in bioimage analysis* (DOI `10.1038/s41592-023-01942-8`). Saved two Markdown notes and two searchable Zotero child notes, checked source links and LaTeX source, and updated a note without duplication.
- Keyword retrieval found the drafts; reviewed-only retrieval excluded them. Stale-version writes and attempts to mark notes reviewed without content approval were rejected. All 16 helper unit tests passed. The approved review transition was tested with mocked writes; the live notes remain unreviewed because their content has not been approved by a human.
- The setup deck now has ten slides, including reading-note storage and example prompts. The editable source, PowerPoint, PDF, and student guides are updated together. PowerPoint package, layout, and re-import checks passed; all ten PowerPoint renders and exported PDF pages were visually inspected. The PDF retains selectable text and hyperlinks.

Sources: [paper-reading instructions](../skills/paper-reading/SKILL.md), [helper tests](../skills/paper-reading/tests/test_notes.py), [Zotero local API](https://www.zotero.org/support/dev/web_api/v3/local_api), [skill use](https://learn.chatgpt.com/docs/skills-and-plugins).
