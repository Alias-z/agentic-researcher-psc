---
name: paper-watch
description: Routinely search a research topic using saved tool choices, tested queries, and reviewed context; save new papers to Zotero and propose evidence-based context updates for human review.
---

# Routinely keep up with papers

Reuse **paper-search**, **zotero-save**, and **paper-reading**. This skill coordinates those workflows and Codex's native scheduler. It does not replace publisher Connector saves or ask students to recreate their earlier work.

## Gather and confirm once

1. Discover `research.json` with the sibling paper-search `scripts/research_store.py discover --workspace WORKSPACE`. Use the current workspace or explicit project paths from this chat; do not search unrelated folders. Select the matching topic, asking only when ambiguous. If earlier work exists only in this chat, recover its actual choices/results into artifacts without inventing a tested strategy or human-reviewed context.
2. Run `scripts/watch.py --project PROJECT prepare`. It loads preferred sources, tested query variants, filters, paper limit, and reviewed context. Unreviewed drafts are flagged and excluded from established context. Missing choices are explicit. If no source preference was recorded, show the last selected tools as a proposal. If a newly selected tool has no tested query, test it before scheduling.
3. Show one compact, prefilled proposal: topic; sources/query variants; linked context; frequency/time/timezone; maximum papers per update; tab mode; destination Zotero collection. Reuse the user's choices. Suggest background mode and a weekly schedule only when unspecified. Ask the user to confirm or edit the proposal in one response, including only genuinely missing choices. Do not reopen the paper-search form or ask for a second confirmation.
4. Resolve the named Zotero destination using zotero-save. Save the confirmed settings using `configure` as documented in [run contract](references/run-contract.md). Create/update a **heartbeat in this chat** with the native `automation_update` tool, preserving any existing automation ID and notification settings. Use standalone scheduled chats only when explicitly requested. Attach the returned ID only after tool success; configuring files does not schedule anything.

The saved automation prompt must identify the absolute research project path, invoke paper-watch's routine workflow, reread its artifacts each run, skip intake, use the confirmed destination/limits, and propose rather than approve scientific context changes. Keep it human-readable. Include: notify on new papers, a meaningful finding, failure, or required action; remain quiet when nothing has changed. Keep notification settings in the tool fields. Check the tool's returned schedule against the confirmed local timezone/time. Local scheduled work requires the computer awake and Codex running; mention this once when confirming setup. [Native automations](https://learn.chatgpt.com/docs/automations) support recurring work with skills.

## Each routine run

1. Run `begin`; resume any unfinished run before starting another. Read the returned current context and query strategy. Use its history exclusion file in paper-search **before enrichment or counting eligible papers**. History exclusion is separate from the optional Zotero-library exclusion. Only scan My Library if that option was selected; destination checks needed to save are still allowed.
2. Dispatch selected sources concurrently with their existing workflows. Background mode uses API first, browser fallback; visible mode keeps all website searches in Codex's preview. Each source gathers its own eligible maximum (N+1 with Zotero exclusion), then pool and deduplicate. Keep the tested wording focused on the same question. Use the supplied overlapping time windows where indexing/update filters support them. If only publication dates are supported, supplement with the saved relevance queries without a publication cutoff to catch older papers indexed late. Respect source access limits and interactive Scholar pagination. An access failure is not an empty search.
3. Save the eligible pool with `stage` before publisher work. Preserve overflow and failed saves across runs. Follow the returned selection and confirmed maximum; use saved context to order new candidates and explain relevance. Blocked sources remain incomplete and keep their previous checkpoint. Do not wait indefinitely for unattended logins: report the needed action and continue other sources.
4. Save selected new papers through **zotero-save**, passing the exact destination and tab mode; the confirmed routine already authorizes these saves. Recheck the destination for an existing item after interruptions. Keep concurrency for preparation/verification and sequential trusted Connector clicks. Do not use direct metadata imports. Record actual item keys, library, collection, and PDF state. Retry failures on later runs up to three attempts, then request attention. Check pending PDF attachments without saving another copy.
5. Read enough evidence to explain the findings. Use **paper-reading** for deeper reading of particularly relevant papers or an apparent conflict, saving draft notes as usual. Distinguish abstract-only evidence and incomplete access; compare populations, methods, and conditions before saying two studies conflict. Do not call a paper important solely because it is new.
6. Use `finish` to persist verified outcomes and the update before advancing successful-source checkpoints. Repeating the same finish is idempotent. Send its compact update when actionable; omit empty-run messages. Keep paper-search's comparison/strategy artifacts intact.

## The routine update

Lead with the number **actually added to the confirmed Zotero collection**. Give linked titles, what the papers found, their specific relevance to the saved topic, and a short recommendation for which paper to read and why. Keep existing items, failed saves, and pending PDFs distinct from new successful saves. Avoid internal counters or a tool scorecard.

When evidence challenges the reviewed context, explain the earlier view, the new evidence, and what may need revising. Save a run-specific context proposal and ask the user to review that change. **Never update reviewed context automatically.** Use paper-reading's draft/review workflow after their response; future routines then load the corrected context. A new paper can raise a question without resolving it.

Use Python 3 or the interpreter returned by `load_workspace_dependencies`; students need no separate Python installation. The helpers perform local bookkeeping only. Read [run contract](references/run-contract.md) for commands and data fields.
