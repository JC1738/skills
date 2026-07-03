---
name: improve-arch-with-context
description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick — for repos whose glossary and decisions live in AppFlowy/Plane instead of markdown.
disable-model-invocation: true
---

# Improve Codebase Architecture (AppFlowy/Plane-backed)

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow
modules into deep ones. The aim is testability and AI-navigability. Same discipline as
`/improve-codebase-architecture`, but the domain model is sourced and updated **live in AppFlowy**
(via `/domain-context-mcp`) — no local `CONTEXT.md` / `docs/adr/`.

This command is _informed_ by the project's domain model and built on a shared design vocabulary:

- Run the `/codebase-design` skill for the architecture vocabulary (**module**, **interface**,
  **depth**, **seam**, **adapter**, **leverage**, **locality**) and its principles (the deletion
  test, "the interface is the test surface", "one adapter = hypothetical seam, two = real"). Use these
  terms exactly in every suggestion — don't drift into "component," "service," "API," or "boundary."
- The domain language gives names to good seams; recorded decisions are ones this command should not
  re-litigate. Both live in AppFlowy, not in the repo.

## Process

### 1. Explore

**Read the domain model from AppFlowy first.** Log in once (`appflowy_login`), resolve the two global
IDs (`workspace_id` + registry index `view_id`) from the `## Domain store` block in `~/.claude/CLAUDE.md`
(first-run setup → `skills/personal/SETUP.md`), then resolve this repo's pages from the **central
registry** by matching the current repo key (`git remote get-url origin`; else repo root path; else
basename) to a row — same logic as `/domain-context-mcp`, no repo files needed. Then
`appflowy_get_page_markdown` on the glossary page and on the Decisions parent + its ADR child pages for
the area you're touching. No matching row → bootstrap/confirm as in `/domain-context-mcp`. If AppFlowy
is unreachable, say so and proceed without the glossary rather than inventing one.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid
heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how
  they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate
complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the
temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to
`<tmpdir>/architecture-review-<timestamp>.html`. Open it for the user (`xdg-open` on Linux, `open` on
macOS, `start` on Windows) and tell them the absolute path.

For each candidate render a card with files, problem, solution, benefits (in terms of locality and
leverage), a before/after diagram, and a recommendation-strength badge. End with a **Top
recommendation** section. See [HTML-REPORT.md](HTML-REPORT.md) for the full scaffold, diagram
patterns, and styling.

**Use the AppFlowy glossary vocabulary for the domain, and the `/codebase-design` vocabulary for the
architecture.** If the glossary defines "Order," talk about "the Order intake module" — not "the
FooBarHandler," and not "the Order service."

**ADR conflicts**: if a candidate contradicts a recorded decision (an ADR child page under the
Decisions parent), only surface it when the friction is real enough to warrant revisiting that
decision. Mark it clearly in the card (e.g. _"contradicts the 'event-sourced orders' decision — but
worth reopening because…"_). Don't list every theoretical refactor a decision forbids.

Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like
to explore?"

### 3. Grilling loop

Once the user picks a candidate, run the `/grilling` skill to walk the design tree with them —
constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests
survive.

Side effects happen inline as decisions crystallize — run the **`/domain-context-mcp`** skill (not
`/domain-modeling`) to keep the domain model current in AppFlowy as you go:

- **Naming a deepened module after a concept not in the glossary?** Add the term to the AppFlowy
  glossary page.
- **Sharpening a fuzzy term during the conversation?** Update the glossary page right there
  (read-then-write to preserve marks).
- **User rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me to
  record this as a decision so future architecture reviews don't re-suggest it?"_ — written as a new
  child page under the Decisions parent. Only offer when the reason would actually be needed by a
  future explorer; skip ephemeral and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** Run the `/codebase-design` skill
  and use its design-it-twice parallel sub-agent pattern.
