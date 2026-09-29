# Setup

## 1. Codex setup

1. **Install Codex:** Download the [desktop app](https://chatgpt.com/download/), sign in, and select **Codex**.
2. **Install Google Chrome:** Download [Chrome](https://www.google.com/chrome/), install it, and open it once.
3. **Install Zotero:** Download and open [Zotero desktop](https://www.zotero.org/download/), version **10 or later** for saving reading notes through the local API. In **Settings → Advanced**, enable **Allow other applications on this computer to communicate with Zotero**. Keep Zotero open.

![Zotero: Advanced settings and local access enabled](assets/zotero-local-access-marked-2026-09-28.svg)

This lets Codex check your library and read saved paper text. When `paper-reading` saves a note, Zotero asks whether to allow **Paper Reading** to make changes. **Allow** authorizes one write, so later saves can ask again. This grants application access; human review of the note's content happens separately. See [Zotero's local API documentation](https://www.zotero.org/support/dev/web_api/v3/local_api).

4. **Enable Computer Use:** In **Settings**, search `computer use`, open **Computer use**, and turn on **Any App**.

![Computer Use: search and Any App setting](assets/codex-computer-use-marked-2026-09-23.png)

5. **Enable CDP:** In **Settings**, search `chrome` and turn on **Enable full CDP access**.

![Browser: chrome search and full CDP access](assets/codex-chrome-cdp-marked-2026-09-23.png)

6. **Install Zotero Connector:** In Codex’s browser, open **Chrome Web Store** and install **Zotero Connector**.

![Browser extensions: Zotero Connector enabled](assets/codex-zotero-connector-installed-marked-2026-09-23.png)

## 2. Install the three skills

In Codex, paste:

> Use `skill-installer` to install `skills/paper-search`, `skills/zotero-save`, and `skills/paper-reading` from:
>
> `https://github.com/Alias-z/agentic-researcher-psc`
>
> If `python3` is unavailable, use the Python executable from `load_workspace_dependencies` for the installer.

The skills are available on the next turn. If you installed the first two earlier, ask to install only `skills/paper-reading`. To use one, name it in your request, for example: “Use `paper-reading` to read this saved paper.”

- **paper-search:** find papers and DOIs.
- **zotero-save:** save selected papers and available PDFs through Zotero Connector.
- **paper-reading:** read saved papers, automatically save Markdown notes, record human review, and discuss the evidence.

## 3. Choose where reading notes live

Tell Codex which folder in your writing project should hold the notes. If you do not choose one, it uses the task's deliverables folder and gives you links.

Each paper gets one editable `.md` file and a generated, searchable Zotero note. The Zotero note and PDF sit under the **same paper record**. The note includes a **Markdown source** link back to the file, which you can reuse for LaTeX writing.

Notes are saved immediately with `human_reviewed: false` and the Zotero tag `reading:draft`. After you check and explicitly approve a note's content, Codex changes these to `true` and `reading:reviewed`. An agent revision returns the note to draft. Unreviewed notes remain available for discussion, with their status stated.

Zotero searches the generated note text by keyword; Codex can also search the Markdown files. If you edit a file yourself, ask Codex to refresh its Zotero copy. There is no background synchronization. Keep the Markdown folder backed up separately; the source link does not upload the file into Zotero.

## 4. Zotero plugin for citations (optional)

For general library searches and BibTeX/citation export, open **Plugins** in Codex, search `zotero`, and install **Zotero**. The plugin will be available in new chats. `paper-reading` includes its own helper for reading and saving notes and does not require this plugin.

![Codex Plugins: Zotero search and plugin](assets/codex-zotero-plugin-marked-2026-09-28.svg)

**Exercises:** [Search, save, read, and discuss papers](01-literature-to-zotero.md).
