---
name: load-domain-context
description: Load the current repo's domain glossary (and decisions) live from AppFlowy so work uses the project's ubiquitous language. Use at the start of substantive work in a repo whose domain model lives in AppFlowy/Plane rather than markdown, or whenever you need its domain vocabulary. Read-only.
---

# Load Domain Context

Ground work in this repo's domain model, sourced **live from AppFlowy** (the repo keeps no
`CONTEXT.md` / `docs/adr/`). **Read-only** — this skill only loads context; to *change* the model
(add/sharpen terms, record a decision) use `/domain-context-mcp`.

> On Claude Code a SessionStart hook does this automatically every session. Invoke this skill directly
> in surfaces where hooks don't run (Cowork / web) or to reload after the glossary changed.

## Steps

1. `appflowy_login` (once per session).
2. **Resolve the two global IDs** (`workspace_id` + registry index `view_id`) from a `## Domain store`
   block in `~/.claude/CLAUDE.md` (already in context — no tool call; same source the SessionStart hook
   uses). If that block is **absent, it's first-run setup** (see `skills/personal/SETUP.md`): get the
   IDs from the AppFlowy share-link URL of your *Repo Domain Context (index)* page (**primary**), or
   discover once via `appflowy_list_workspaces` + `appflowy_search_documents({query: "Repo Domain
   Context"})` (**secondary** — confirm, it can return zero/many), then write them into `## Domain
   store`. Then read the registry: `appflowy_get_page_markdown(workspace_id, registry_view_id)`
   (*Repo Domain Context (index)*).
3. Match the **current repo** to a Registry row, in priority order: `git remote get-url origin`; else
   the repo root absolute path; else the directory basename.
4. **Matched** → `appflowy_get_page_markdown` on that row's glossary `view_id`. Tell the user once,
   visibly: *"✓ Domain context loaded for `<repo>` from AppFlowy (N terms)."* Then adopt its
   ubiquitous language for the rest of the session. Optionally read the Decisions parent to see
   recorded ADRs for the area you're touching.
5. **No match** → if this is a real project dir (a git repo, or it has `CLAUDE.md` / `.mcp.json` /
   `package.json` / etc.), surface a one-line nudge: *"No domain context registered for this repo —
   run `/grill-with-context` to set it up."* In a non-project dir, stay silent. (The SessionStart hook
   applies the same rule automatically on Claude Code.)
6. **AppFlowy unreachable** → say so briefly and proceed without the glossary; never invent one, never
   write a local file.

Keep it lightweight: glossary first (the high-value vocabulary); pull individual ADR child pages only
when a task touches that area.
