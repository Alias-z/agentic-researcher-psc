---
name: paper-reading
description: Read selected Zotero papers, automatically save Markdown reading notes with human-review status and searchable Zotero copies, and discuss research questions using notes and original evidence. Not for discovering or saving new papers.
---

# Read, review, and discuss papers

Keep papers in Zotero and author reading notes as UTF-8 Markdown files. Reading a paper includes saving or updating its Markdown note and a generated, searchable Zotero copy, including when reading is done to answer a discussion question. Save what was actually read and learned before finishing the response. Human review determines the note's status, not whether the note exists. Use Zotero's existing search without building a separate database or retrieval system.

## Start from the selected papers

Reuse papers and collections already identified in the conversation. Ask only when the selection is genuinely ambiguous. Use the bundled `scripts/notes.py` helper with Python 3 to read items, notes, attachments, and indexed text through Zotero's local API. It has no third-party dependencies. Zotero must be running with local API access enabled. Do not modify Zotero's SQLite database directly.

Keep one authoritative `.md` file per paper in the user's writing/notes folder, or the workspace deliverables folder when no folder has been chosen. Reuse its existing location; do not keep the only copy in scratch storage. Include simple YAML frontmatter with `title`, `doi`, `zotero_item_key`, `zotero_note_key` (once created), `citation_key` when verified, and `human_reviewed: false` or `true`. Keep prose, headings, lists, and LaTeX math portable. Do not invent an existing BibTeX key; obtain it from the matching Zotero/BibTeX export when needed for writing.

The generated Zotero note and PDF are separate child items under the same parent paper. Keep one generated note per paper, with a **Markdown source** link to the `.md` file. Tag this note `reading:draft` when `human_reviewed` is false, or `reading:reviewed` when true. Zotero indexes the generated HTML note for search; the Markdown file remains the editable source. These statuses are workflow conventions, not Zotero's certification of scientific accuracy.

## Read and draft a note

Read the available full text, relevant methods, and figures supporting the main findings. Inspect figures visually when their interpretation matters. Check supplements when needed for a claim, and identify unavailable material. An abstract-only reading must be labeled as such.

Save the Markdown file and its Zotero copy headed **Reading note** as part of the reading task, without waiting for human review or a separate request to save. Reuse existing files and child notes rather than creating duplicates. Only keep a note unsaved when the user explicitly requests that or saving is unavailable. Keep it concise, using this flexible structure:

- **Question:** What does the paper investigate?
- **Methods and context:** The design, organism, tissue, treatments, and conditions needed to interpret the findings.
- **Key findings:** Main results with page, figure, table, or section references that were actually checked.
- **Limitations and open questions:** What the evidence does not resolve.
- **Relevance and comments:** Connections to the user's research, with space for their corrections and ideas.

Identify the paper and state reading coverage. Distinguish reported results, the authors' interpretation, and the agent's inference. Add links back to the source where available; never invent page numbers, quotations, or evidence. Indexed text is useful for reading/search, but inspect the original PDF for precise page references and figures. Use the available PDF skill when extraction or rendering is needed.

Read the Markdown file and existing Zotero note before revising either, and preserve the user's comments from both. Save Markdown first, then render its body to simple HTML in a workspace scratch file and add the Markdown-source link. The helper accepts this generated HTML via `save-draft --html`; it does not render Markdown. Check that LaTeX backslashes, subscripts, and citation keys survive rendering; fenced `latex` blocks are suitable when literal equation source is needed. Preview, then apply with `--write`; a preview alone does not complete synchronization. For updates, supply the version from the note you actually read. A version conflict requires rereading and reconciling edits, never blindly retrying. The helper reuses the tagged note, preserves unrelated tags, and verifies saved parent, status, text, and link targets. Agent content revisions set `human_reviewed: false` and the Zotero tag to draft. Reusing unchanged content does not require a rewrite. If Zotero saving is unavailable, keep the Markdown file and clearly report that its Zotero copy is unsynchronized.

There is no background synchronization. On subsequent reading, editing, review, or discussion, follow the source link and reconcile changes before relying on or replacing the generated copy. For LaTeX writing, use the Markdown source and matching bibliography export.

## Let the user review

Report that the notes were saved and are awaiting human review; continue the requested synthesis or discussion using their labeled status. Incorporate the user's corrections. Apply `reading:reviewed` and `human_reviewed: true` only after explicit approval of the current content, or recognize a status the user has applied themselves after checking which content was reviewed. Approval of this skill's design, permission to read papers, and silence are not approval of a reading note. The agent cannot approve its own work. Use `mark-reviewed --user-approved` only when approval is present. Read the note and Markdown source again, check that they agree with the reviewed content and version, apply the Zotero status change, then update the Markdown flag. Any later agent content revision returns both to unreviewed. Report any partial synchronization failure.

## Discuss using the library

Search reading notes with `search`, which uses `itemType=note` and `qmode=everything` and includes both human-reviewed and unreviewed notes by default. Use `--reviewed-only` when the user requests that restriction. The existing general Zotero helper's default top-level search is insufficient for this. Use a few relevant keyword queries or read all notes in a small selected collection; Zotero's keyword search does not supply semantic understanding. Use `read NOTE_KEY` to retrieve complete matching notes, follow the Markdown-source link to read current content, follow `parentItem` to the papers, and consult original passages and figures as needed. A local Markdown folder can also be searched directly with `rg`. State the human-review status of the evidence used.

Compare experimental conditions and conflicting evidence. Cite the papers and useful evidence locations. Label new interpretations; do not present them as user-reviewed conclusions. Say when the available papers cannot answer the question.

Save new paper-specific findings and corrections into the corresponding Markdown notes and regenerate their Zotero copies automatically. Also preserve the evolving cross-paper understanding for later searches, following [research context](references/research-context.md). Begin with the agent's current understanding, then compare it with the selected recent papers and the user's expertise. Record what changed, why, unresolved conflicts, and the evidence. Newer publication dates alone do not settle a conflict. Drafts remain distinct from the context the user has reviewed.

## Helper commands

Run from this skill directory, or substitute the absolute path to `scripts/notes.py`:

```sh
python3 scripts/notes.py status
python3 scripts/notes.py read PAPER_KEY
python3 scripts/notes.py fulltext PDF_ATTACHMENT_KEY
python3 scripts/notes.py file PDF_ATTACHMENT_KEY
python3 scripts/notes.py search starch --collection COLLECTION_KEY
python3 scripts/notes.py search starch --collection COLLECTION_KEY --reviewed-only
python3 scripts/notes.py read NOTE_KEY
python3 scripts/notes.py save-draft PAPER_KEY --html /absolute/work/draft.html
python3 scripts/notes.py save-draft PAPER_KEY --html /absolute/work/draft.html --version NOTE_VERSION --write
python3 scripts/notes.py mark-reviewed NOTE_KEY --version NOTE_VERSION --user-approved --write
```

For the first save, omit `--version`; for subsequent content updates it is required. Write commands preview by default unless `--write` is present. For a group library, put `--library /api/groups/GROUP_ID` before the command. `file` returns a local file URL for PDF inspection. Search results contain excerpts; `read` returns the full note.

Local API writes require Zotero 10+ and Zotero's own authorization dialog. Explain that dialog before the first authorized save; it grants application access and does not approve the reading note. Zotero's one-time Allow authorizes one API write, not a sequence of writes; do not cache that key for later writes. The helper requests authorization only for `--write`, keeps the returned key in memory, and never prints or saves it. An existing key can be supplied through `ZOTERO_LOCAL_API_KEY`; never print it. On denied authorization, stop the write and retain the draft. On an uncertain write outcome, inspect the paper's notes before retrying.

API references: [local access and authorization](https://www.zotero.org/support/dev/web_api/v3/local_api), [search and child items](https://www.zotero.org/support/dev/web_api/v3/basics), [note updates and version checks](https://www.zotero.org/support/dev/web_api/v3/write_requests).

Run local helper checks with `python3 -m unittest discover -s tests`. These use mocked writes. A live reading/review test must keep the note draft until the user actually approves its content.
