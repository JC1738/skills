---
name: domain-context-mcp
description: Build and sharpen a project's domain model when the glossary and decisions live in AppFlowy (and work is tracked in Plane) rather than in markdown files. Use when the user wants to pin down domain terminology or record a decision in a repo whose context lives in AppFlowy/Plane, or when another skill needs to maintain that model.
---

# Domain Modeling (AppFlowy/Plane-backed)

The active domain-modeling discipline — challenging terms, inventing edge-case scenarios, and
writing the glossary and decisions down the moment they crystallise — but with the **store living
in AppFlowy and Plane**, read and written **live** over MCP. There is no local `CONTEXT.md` or
`docs/adr/`: AppFlowy is canonical. (Merely *reading* context for vocabulary is a one-line habit any
skill can do. This skill is for when you're *changing* the model.)

This is the personal AppFlowy/Plane counterpart to `/domain-modeling`. Same quality rules; different
storage layer.

## Prerequisite: log in once per session

Before any AppFlowy tool, call `appflowy_login` once (in-memory token, resets each reload). Creds
come from the repo's `appflowy-mcp` config. If login or any later AppFlowy/Plane call fails, **stop
and tell the user** — never fall back to writing a local file, and never write to a guessed page.

## Locate the store

Domain pages are resolved from the **central registry in AppFlowy** — repos need **no local files**.

- **Two global IDs (`workspace_id` + registry index `view_id`):** read them from a `## Domain store`
  block in `~/.claude/CLAUDE.md` (already in context — no tool call). This is the single source the
  SessionStart hook reads too. If that block is **absent, it's first-run setup** (see
  `skills/personal/SETUP.md`): get the two IDs from the AppFlowy share-link URL of your *Repo Domain
  Context (index)* page (**primary**), or discover once via `appflowy_list_workspaces` +
  `appflowy_search_documents({query: "Repo Domain Context"})` (**secondary** — confirm the match, it
  can return zero/many). Then **write them into `## Domain store`** so every later run is free. Never
  re-discover when the block is present.
- **Read the registry:** after `appflowy_login`, `appflowy_get_page_markdown(workspace_id,
  registry_view_id)`; its **Registry** table maps each repo to its pages.
- **Match the current repo key** to a table row, in priority order: `git remote get-url origin`; else
  the repo root absolute path; else the repo directory basename. The matched row gives the glossary
  `view_id` and the Decisions parent `view_id` (Plane project is optional).
- **Repo-local override:** if `docs/agents/domain-store.md` (or a per-repo `## Domain store` block in
  the project's `CLAUDE.md`) exists, its IDs win for that repo.

**No matching row?** Bootstrap once: `appflowy_search_documents(workspace_id, {query: "<repo>
glossary"})` / `…{query: "<repo> decisions"}`. On a confident match, confirm with the user; otherwise
create a `<repo> — Glossary` + `<repo> — Decisions (ADRs)` pair as children of the registry page
(`appflowy_create_page_from_markdown`, `parent_view_id=<registry index view_id>`). Then **append a row
to the registry** (read-then-write `appflowy_update_page_from_markdown` on the registry page) so it
resolves with no prompt next time. On zero/ambiguous matches, ask — don't guess.

## Read the current model

- **Glossary / ADR pages:** `appflowy_get_page_markdown(workspace_id, view_id)`.
- **Related work:** pull Plane items for context with `list_work_items(project_id, pql=…)`,
  `search_work_items(query=…)`, or `retrieve_work_item(…)`.

## During the session

Identical discipline to `/domain-modeling`:

### Challenge against the glossary
When the user uses a term that conflicts with the existing language, call it out immediately. "Your
glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language
When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying
'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios
Stress-test domain relationships with specific scenarios that probe edge cases and force the user to
be precise about the boundaries between concepts.

### Cross-reference with code
When the user states how something works, check whether the code agrees. Surface contradictions:
"Your code cancels entire Orders, but you just said partial cancellation is possible — which is
right?"

## Write-back — always to AppFlowy, never to a cache

Capture resolutions the moment they happen; don't batch them.

- **Glossary term resolved →** update the glossary page. To preserve inline marks and links,
  **read-then-write**: `appflowy_get_page_markdown` → edit → `appflowy_update_page_from_markdown`.
  For a simple addition at the end, `appflowy_append_markdown` is fine. Keep the glossary a glossary —
  totally devoid of implementation details (format: [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)).
- **ADR worth recording →** create a child page under the Decisions parent:
  `appflowy_create_page_from_markdown(workspace_id, parent_view_id=<Decisions>, name="<title>",
  markdown=…)`. Offer an ADR only when all three hold: hard to reverse, surprising without context,
  the result of a real trade-off (format + criteria: [ADR-FORMAT.md](./ADR-FORMAT.md)).
- **Decision ties to a tracked item →** optionally log it with
  `create_work_item_comment(project_id, work_item_id, …)` so the Plane item stays the index.

## Scope

Single-context per repo for now (one glossary page, one Decisions parent). Multi-context
(`CONTEXT-MAP`-equivalent across several AppFlowy pages) is deferred.
