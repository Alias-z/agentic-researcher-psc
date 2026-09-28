# Setup

## 1. Codex setup

1. **Install Codex:** Download the [desktop app](https://chatgpt.com/download/), sign in, and select **Codex**.
2. **Install Google Chrome:** Download [Chrome](https://www.google.com/chrome/), install it, and open it once.
3. **Install Zotero:** Download and open [Zotero desktop](https://www.zotero.org/download/).
4. **Enable Computer Use:** In **Settings**, search `computer use`, open **Computer use**, and turn on **Any App**.

![Computer Use: search and Any App setting](assets/codex-computer-use-marked-2026-09-23.png)

5. **Enable CDP:** In **Settings**, search `chrome` and turn on **Enable full CDP access**.

![Browser: chrome search and full CDP access](assets/codex-chrome-cdp-marked-2026-09-23.png)

6. **Install Zotero Connector:** In Codex’s browser, open **Chrome Web Store** and install **Zotero Connector**.

![Browser extensions: Zotero Connector enabled](assets/codex-zotero-connector-installed-marked-2026-09-23.png)

## 2. Install the skills

In Codex, type `@`, select **skill-installer**, then paste:

> Install `skills/paper-search` and `skills/zotero-save` from:
>
> `https://github.com/Alias-z/agentic-researcher-psc`
>
> If `python3` is unavailable, use the Python executable from `load_workspace_dependencies` for the installer.

After installation, type `@` to find **paper-search** and **zotero-save**.

**Next:** [Search papers and save to Zotero](01-literature-to-zotero.md).
