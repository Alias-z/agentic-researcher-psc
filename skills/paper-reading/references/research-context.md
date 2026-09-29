# Keep research context across searches

For a discussion building on paper-search, locate its `research.json` in the current workspace or use the project path already given. The sibling **paper-search** skill provides `scripts/research_store.py`; use Python 3, falling back to Codex's bundled interpreter. If that skill is unavailable, preserve `context-draft.md` in the user's notes folder and report the missing handoff helper without losing the notes.

1. Read existing `context.md`, any pending draft, and the linked paper notes. Preserve the user's corrections and views, distinguishing them from established findings and the agent's inference.
2. Before reading new papers, state the current understanding briefly in the discussion. After reading, save a concise context draft: research focus; current understanding; revisions supported by evidence; disagreements/limitations; useful search terms; next questions. Cite the actual reading notes and papers. Use recent papers discovered in the preceding search when those are the selected reading material.
3. Run `research_store.py save-context --project PROJECT --input DRAFT.md --note NOTE.md` (repeat `--note` for additional files). This saves `context-draft.md`, links the existing per-paper notes, and leaves reviewed `context.md` intact. Saving this draft is part of the exercise, not an extra student task.
4. Show the substantive changes for review. Only after the user approves that version, run `review-context --project PROJECT --sha256 DRAFT_HASH --user-approved`; the save command returns the hash. If the user corrects it, save and review the revised version. Never treat a general request to research, an automation confirmation, or silence as approval of scientific claims.

Context review and individual paper-note review are separate. Updating context does not mark all notes reviewed. Later changes create a new draft; future paper-watch runs use the latest reviewed context and identify unresolved drafts. Local artifacts, rather than assumed permanent model memory, carry this understanding between runs.

## Reviewing a routine update

paper-watch saves evidence and proposed wording in a run-specific `context-proposal.json`. Compare its `base_context_sha256` with the current reviewed context before applying it. If the user has updated the context since that run, merge the proposal against the newer version and show the difference. Do not overwrite an existing pending draft. Preserve both sets of proposed changes, resolve real conflicts with the user, then use the same draft/review workflow above. Read the full paper when an abstract cannot support the proposed correction.
