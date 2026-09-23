# Agentic Researcher PSC

Teaching materials for the **Research Assistants** workshop in *Explore the Responsible Use of Generative AI in Academic Work*, Zurich–Basel Plant Science Center (PSC), 30 September 2026.

The workshop follows a research task from finding papers to checking sources, collecting full text, analysing a small dataset, and presenting a result. Students start with ordinary language in Codex. The instructor can expose the underlying code when it helps explain or audit an action.

## Start here

1. [Prepare Codex, browser access, and Zotero with illustrated steps](workshop/00-start-here.md).
2. [Find, collect, and verify a paper](workshop/01-literature-to-zotero.md).

The first reusable skill is [zotero-connector-collect](skills/zotero-connector-collect/SKILL.md). It tells Codex how to activate the installed official Zotero Connector from the publisher page and how to verify the saved record and PDF. The repository copy is the version to distribute; students should receive it through a course installation package rather than editing it.

## Repository layout

```text
agentic-researcher-psc/
├── README.md
├── workshop/                  Student-facing steps and exercises
│   ├── 00-start-here.md
│   ├── 01-literature-to-zotero.md
│   └── assets/                 Illustrated setup screens (PNG with SVG sources)
├── skills/                    Reusable Codex skills; one folder per skill
│   └── zotero-connector-collect/
│       └── SKILL.md
└── instructor/                Rationale, timing, and facilitator notes
    ├── course-alignment.md
    └── setup-audit.md
```

As the exercises are developed, add `workshop/02-paper-synthesis.md`, `workshop/03-data-analysis.md`, and `workshop/04-present-results.md`. Put small public or synthetic inputs in `examples/` only when those exercises need them. Add a skill when its workflow has been tested, rather than creating empty skill folders.

## Scope and status

The literature-to-Zotero action has been tested in Codex's built-in browser with the official Zotero Connector. Two publisher articles saved with metadata and PDF attachments; a third saved metadata without a PDF. The lesson requires checking each outcome. Data analysis and result-presentation exercises are planned but not yet built.

This is a local Git repository. It has no remote or public release yet. The lecturer kickoff PDF is an input to the plan and is not included in the student materials.

The [instructor setup audit](instructor/setup-audit.md) records what was verified on the teaching machine and what still needs a Settings check.
