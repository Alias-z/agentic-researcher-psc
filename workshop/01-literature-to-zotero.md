# Search, save, read, and discuss papers

Complete [setup](00-start-here.md) first.

## 1. Find papers

> Use `paper-search` and show me the search form in Codex's right-side browser.

1. Enter a topic. Add context or filters if needed, such as “published after 2016” or “original studies only.”
2. Tick the search tools and set **Maximum papers per tool**.
3. Choose **Visible** to watch in Codex's right-side preview, or **Background**. Keep this task open when using visible tabs.
4. Choose **Results by source** for separate lists, or **Combined list** to remove duplicates across tools.
5. To exclude saved papers, open Zotero and tick **Only show papers not in Zotero**.
6. Click **Start search**.

If a tool asks for sign-in, sign in through the Codex browser tab and tell Codex when done, or ask to skip that tool.

## 2. Save selected papers

Keep Zotero desktop open. In the **same Codex task**, paste:

> Use `zotero-save` to save papers **[numbers from the table]** to a collection called `test`. Create it if missing. Use visible tabs. Report each DOI and whether its PDF opens in Zotero.

Check the title, DOI, and collection in Zotero, then open the attached PDF.

## 3. Read one paper and save its notes

Start with one of the papers you just saved. Replace the bracketed text:

> Use `paper-reading` to read **[paper title or DOI]** in my `test` collection. Save its Markdown reading note in **[my writing project's notes folder]** and its searchable copy under the same Zotero paper. Include the question, methods, key findings with checked evidence locations, limitations, and relevance to **[my research question]**. Tell me what you could actually read and show me the note.

Every reading saves notes automatically, including reading done during a discussion. If only the abstract or part of the paper is available, the note must say so. Zotero may show an **Allow Paper Reading** dialog when saving. This is application access, not approval of the note's scientific content.

Open the `.md` file and expand the paper in Zotero. Check that its PDF and **Reading note** are under the same record, and that the note's **Markdown source** link opens the file. The file starts with `human_reviewed: false`; the Zotero note carries `reading:draft`.

## 4. Review the note

Check the findings against the paper, especially the cited figures or passages. Ask for corrections, or edit the Markdown file and ask Codex to refresh the Zotero copy. The `.md` file is the editable source; keep it in the chosen folder for later writing.

Only after you have checked the content, say:

> I have reviewed and approve the current reading note for **[paper title or DOI]**. Mark it human-reviewed in both the Markdown file and Zotero.

Check `human_reviewed: true` and `reading:reviewed`. Later agent revisions return it to draft so you can review the changes.

## 5. Discuss the evidence

> Use `paper-reading` to search my `test` collection's reading notes for **[topic or keywords]** and discuss **[research question]**. Include unreviewed notes but state their status. Compare conditions and conflicting findings, cite the papers, and check the original evidence where needed.

For a restricted discussion, add: “Use only human-reviewed notes.” Searches use the text of the saved Zotero notes; there is no separate search database to set up. Any new paper-specific findings from the discussion are saved back to the corresponding Markdown notes and Zotero copies.
