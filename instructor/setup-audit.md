# Instructor setup audit — 23 September 2026

This is a functional check of the current teaching machine, not a claim that every student's machine is configured the same way. Use [the student setup guide](../workshop/00-start-here.md) for installation steps.

The student guide uses screenshots from this Mac's Codex settings. They show the settings on 23 September 2026; students must check their own machines.

| Requirement | Current observation |
| --- | --- |
| Codex built-in browser (`@Browser`) | Working. Codex can read and click publisher pages in the right-side browser. |
| Browser and Computer Use capability | Working in the built-in browser. A local screenshot shows **Any App** on and Google Chrome connected. The plugin server and skill toggles are not shown. |
| **Enable full CDP access** | A local screenshot shows the switch on under **Computer use → Google Chrome**. Page-scoped CDP `Runtime.evaluate` also succeeded on a live Wiley DOI tab in the built-in browser. |
| Zotero Connector in the built-in browser | A local screenshot shows Zotero Connector installed and enabled. Agent-triggered Connector saves produced metadata and PDFs for `10.1111/pce.70864` and `10.1111/pce.70548`; `10.1111/pce.70862` saved metadata without a PDF. |
| Zotero desktop and `test` collection | Zotero is running. Its read-only local API responds, and `test` exists. |
| Zotero automatic PDF preference | Not read directly. The two successful PDF saves show that PDF attachment worked for those papers. Check **Settings → General → File Handling** before class. |
| Institutional access | The tested Wiley pages showed **Access By ETH-Bibliothek** and **Full Access**. Students need their own institution's access in the browser profile they use. |
| Google Chrome installation | Required by the workshop setup and installed on this Mac. |
| Regular Chrome connection to Codex | A local screenshot shows **Google Chrome: Browser extension installed** with **Manage**. The `@Chrome` Zotero workflow has not been tested for this exercise. |
| macOS Screen Recording and Accessibility | Individual permission values were not inspected. Check them if the class will ask Codex to control native app windows. |

The practical pass criterion is one article saved through the **official Connector from its publisher DOI page**, with the expected DOI and a working PDF child attachment in the requested Zotero collection. Do not count a visible PDF link on the publisher page as proof that Zotero attached it.
