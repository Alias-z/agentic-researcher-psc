# Instructor setup audit — 23 September 2026

This is a functional check of the current teaching machine, not a claim that every student's machine is configured the same way. Use [the student setup guide](../workshop/00-start-here.md) for installation steps.

| Requirement | Current observation |
| --- | --- |
| Codex built-in browser (`@Browser`) | Working. Codex can read and click publisher pages in the right-side browser. |
| Browser and Computer Use capability | Working in the built-in browser. The local configuration lists both plugins, and live browser interaction succeeds. The exact Settings toggle states were not inspected directly. |
| **Enable full CDP access** | Page-scoped CDP `Runtime.evaluate` succeeded on a live Wiley DOI tab after the setting was enabled. This confirms the capability used by the course skill; it does not imply unrestricted browser-wide target access. |
| Zotero Connector in the built-in browser | Working. Agent-triggered Connector saves produced metadata and PDF attachments for `10.1111/pce.70864` and `10.1111/pce.70548`. A different paper, `10.1111/pce.70862`, produced metadata without a PDF; verify each save. |
| Zotero desktop and `test` collection | Zotero is running. Its read-only local API responds, and `test` exists. |
| Zotero automatic PDF preference | Not read directly. The two successful PDF saves show that PDF attachment worked for those papers. Check **Settings → General → File Handling** before class. |
| Institutional access | The tested Wiley pages showed **Access By ETH-Bibliothek** and **Full Access**. Students need their own institution's access in the browser profile they use. |
| Google Chrome installation | Installed on this Mac. It was not running at audit time. |
| Regular Chrome connection to Codex | Not currently exposed in the Computer Use browser inventory; only the Codex built-in browser is connected. This is optional for the tested `@Browser` exercise. If teaching `@Chrome`, verify the ChatGPT browser extension and **Settings → Computer Use → Google Chrome → Manage**. |
| macOS Screen Recording and Accessibility | Individual permission values were not inspected. Check them if the class will ask Codex to control native app windows. |

The practical pass criterion is one article saved through the **official Connector from its publisher DOI page**, with the expected DOI and a working PDF child attachment in the requested Zotero collection. Do not count a visible PDF link on the publisher page as proof that Zotero attached it.
