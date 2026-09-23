# Start here

Use Codex's right-side `@Browser` for this exercise. These are screenshots from the teaching Mac on 23 September 2026; red boxes mark what to find.

1. **Install Codex:** Download the [desktop app](https://chatgpt.com/download/) and open Codex.
2. **Install Google Chrome:** Use the [official Chrome download](https://www.google.com/chrome/), run the installer, and open Chrome once. Chrome is required for this workshop.
3. **Install Zotero:** Download and open [Zotero desktop](https://www.zotero.org/download/).
4. **Enable Computer Use:** In Codex **Plugins → Computer Use**, enable the server and skill. In **Settings**, search `computer use`, open that page, and turn on **Any App**.

![Red boxes around the computer use search and Any App setting](assets/codex-computer-use-marked-2026-09-23.png)

5. **Enable CDP:** In **Settings**, search `chrome`, choose the **Browser** result for full Chrome DevTools access, then turn on **Enable full CDP access**. The screenshot shows regular Chrome connected on this Mac.

![Red boxes around the chrome search, Browser result, and full CDP access setting](assets/codex-chrome-cdp-marked-2026-09-23.png)

6. **Install Zotero Connector:** In **Settings**, search `extension`, open **Browser → Extensions**, and click **Chrome Web Store**. Install the official [Zotero Connector](https://chromewebstore.google.com/detail/zotero-connector/ekhagklcjbdpajgpjgmbionohlpdbjgc). It should appear enabled as shown below. The **Developer mode** switch in the screenshot is not needed for installation.

![Red boxes around the extension search and enabled Zotero Connector](assets/codex-zotero-connector-installed-marked-2026-09-23.png)

7. **Check:** In Zotero, create a `test` collection. In `@Browser`, open a publisher DOI page and ask Codex to save it through Zotero Connector. Confirm the DOI, collection, and opening PDF attachment in Zotero.

The separate [ChatGPT browser extension](https://learn.chatgpt.com/docs/chrome-extension#set-up-your-browser) in regular Chrome is needed only if you also want to use `@Chrome`. The workshop exercise uses `@Browser` with Zotero Connector installed there.
