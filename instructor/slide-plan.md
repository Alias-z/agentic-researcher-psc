# Research Assistants slide plan

Research checked: 28 September 2026. Session: 30 September, 10:45–13:00.

## Format

- Deliver a 16:9 PDF and keep an editable slide source in the repo.
- Use a white background, large text, and one accent colour. Footer: page number only.
- Use real screenshots and source images. Crop to the relevant control or result. Mark actions with red rectangles.
- Keep one idea or action per slide. Put longer explanations in speaker notes and source links on a final references page.

## Sections

| Section | Time | Content |
| --- | --- | --- |
| Setup | 20 min | Install apps, configure Codex's browser, install Zotero Connector and the three skills; introduce reading notes and human review. |
| Stories and concepts | 25 min | OpenClaw shows what agents can do; Amazon blocking Muse introduces privacy and safety. Explain the components through our paper-search task. |
| Exercises | 75 min | Search a topic, compare source results, select papers, save to Zotero, and check the PDFs. |

Allow 10 minutes for a break and 5 minutes for closing discussion. Adjust these draft timings after a class rehearsal.

## 1. Setup

Use [the setup guide](../workshop/00-start-here.md) as the source. Ten slides:

1. App downloads.
2. Data privacy and file safety, with a warning symbol and the full incident screenshot on the right.
3. Computer Use, with the existing screenshot.
4. Full CDP access, with the existing screenshot.
5. Zotero Connector in Codex's browser extensions.
6. Enable Zotero local access and explain its write-authorization dialog.
7. Ask `skill-installer` to install `paper-search`, `zotero-save`, and `paper-reading`, with the prompt displayed as a grey code block.
8. Optional Zotero plugin for general library searches and citation exports.
9. Markdown reading notes, their searchable Zotero copies, and human-review status.
10. Example prompts for reading, review, and discussion.

Students finish with all three skills available. Keep the full copyable prompts in the linked setup and exercise guides. Use Zotero 10+ for saving notes through the local API. Explain that every reading saves a draft note; Zotero's authorization dialog grants application access, while explicit approval of the note's content records human review.

Warning example: [Sebastien Guillemot's X thread, 26 August 2026](https://x.com/SebastienGllmt/status/2092634841863123047), read directly in Codex's built-in browser on 28 September. He reports home-directory deletion during a Claude/Fable cleanup-script test and later recovery from Git and other copies. It does not establish a whole-disk wipe or a CDP failure. The slide shows the complete original post, including its attachment and timestamp. Source attribution is in the speaker notes.

## 2. Stories and concepts

### OpenClaw: a voice message in Marrakesh

Peter Steinberger describes sending his assistant a voice message during a trip, although he had not built audio support. The agent identified the file format, converted it with FFmpeg, found an available OpenAI credential, used an audio API, and replied. This is the creator's account of one incident. [Interview transcript, 15:16–17:37](https://lexfridman.com/peter-steinberger-transcript/)

Use two slides: the unexpected reply, then the steps that produced it. Let students predict the missing steps before revealing them.

Teaching point: an agent can combine existing tools to handle an unexpected task. Follow the sequence: inspect → choose a tool → run it → inspect the result → continue. This was tool use, without training a new audio model.

Suggested evidence: a short excerpt from the [original interview](https://lexfridman.com/peter-steinberger/), or a still and the timestamp. Do not fabricate a WhatsApp conversation.

### Amazon blocks Meta Muse: privacy and safety

On 20 September 2026, Amazon said it had blocked Muse from shopping on Amazon. It cited undisclosed agent access, handling of customer credentials, and potential privacy and security risks. Muse could reach account pages and order history when a customer requested it. [GeekWire's report and Amazon statement](https://www.geekwire.com/2026/amazon-blocks-metas-muse-ai-assistant-in-new-standoff-over-agentic-shopping/)

Use two slides:

1. **Amazon blocks Muse.** Show the actual Amazon notice reproduced in the report, with the date and a short account of Amazon's stated concerns.
2. **What access are you giving an agent?** Three questions: What can it read? Where does the data go? What can it do without asking you?

Connect these questions to research: an account may expose unpublished manuscripts, correspondence, or participant data. Give access only to the material needed for the task and check the institution's requirements before connecting sensitive data. For this exercise, use published papers and review selected records and PDFs.

Speaker notes: Amazon's concerns are attributed claims; this report does not establish a data leak. Meta says credentials are stored separately from the main agent and purchases require approval. Its engineering account also says the current architecture does not prevent Meta from accessing VM data when needed to operate the service. Credential protection and data privacy need separate consideration. [Meta's engineering description](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse)

Teaching point: an agent acting through a signed-in account raises questions about data access, permission, and responsibility. Use this incident as the cautionary story; the OpenClaw story illustrates useful capability. Neither incident establishes the overall safety of either product.

### The components in our paper task

Introduce terms beside a concrete action, then keep a single recap slide available during the exercise:

| Component | Meaning | Paper-search example |
| --- | --- | --- |
| Model | Interprets the request and proposes the next action. | Interprets the topic and date filter. |
| Agent loop | Runs an action, reads its result, and decides what to do next. | Reads a results page, checks progress, then loads another page. |
| Tool | Performs a particular operation. | Reads a browser page or checks a Zotero record. |
| Skill | Packages instructions and supporting files for a repeated task. | `paper-search` specifies choices, search steps, and the result format. |
| MCP | A standard interface for connecting an AI application to external tools and data. | A server can expose a database query as a callable tool. |
| Memory or saved state | Retains information for later steps or later tasks. | A candidate ledger retains papers already collected during the search. |

Sources: [Agent Skills specification overview](https://agentskills.io/home), [MCP introduction](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro).

A skill does not grant access by itself. MCP is one connection method; browser control, direct APIs, and command-line tools are other routes. The Muse engineering article describes CLI connectors, so do not label all Muse connectors as MCP. Our Zotero Connector is a browser extension. Our candidate ledger is temporary search state, not permanent personal memory.

Close this section with our own example: opening a paper's PDF did not demonstrate a Zotero save. The finished workflow had to trigger Zotero Connector and verify the record and attachment. Show one real result with those checks. [Local test evidence](setup-audit.md)

## 3. Exercises

Use [the exercise guide](../workshop/01-literature-to-zotero.md) for copyable prompts. About six slides, with one task per slide.

| Activity | Time | Student output |
| --- | --- | --- |
| Instructor demonstration | 10 min | Observe one topic moving through the search form to source results. |
| Search a research question | 20 min | Choose two accessible tools, visible tabs, results by source, and a maximum of three papers per tool. Leave Zotero exclusion off. |
| Compare the papers | 15 min | Identify overlap, one useful paper, and any known paper missing from the lists. Students explain their choices using their subject knowledge. |
| Save selected papers | 20 min | Use `zotero-save` for two selected papers in `test`. Check the DOI and open each PDF. Record any missing attachment. |
| Refine and repeat | 10 min | Add one meaningful filter or clarify a term, then inspect how results change. Zotero exclusion is optional for students with a working library connection. |

Students may use their own topic. Keep a tested example, such as rapid stomatal responses to changing light, ready for anyone who needs one. A comparison should hold the topic and filters constant across tools. Tool availability and search results can change; students assess the returned papers themselves.

The minimum completed exercise is a source-labelled paper list and two checked Zotero records. Record PDF failures honestly. Prepare an accessible paper for students without institutional full-text access.

If time permits, continue with sections 3–5 of the exercise guide: read one saved paper, inspect its Markdown file and Zotero child note, check its evidence, and discuss a research question. Human review is recorded only after students approve the actual note. This extension has no additional database setup.
