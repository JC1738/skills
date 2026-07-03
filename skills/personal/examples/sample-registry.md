# Repo Domain Context (index)

*Per-code-repo domain models — the glossary (ubiquitous language) and decisions/ADRs for individual
git repos, read and written live over `appflowy-mcp` by the `domain-context-mcp` /
`load-domain-context` / `grill-with-context` / `improve-arch-with-context` skills.*

This page **is** the registry. The skills read the two global IDs (this page's `workspace_id` +
`view_id`) from a `## Domain store` block in `~/.claude/CLAUDE.md`, load the table below at session
start, and match the **current repo** to a row — so a repo needs **no local files**.

**Repo key** (how the current repo is matched, in priority order):

1. `git remote get-url origin` (preferred — stable across clones/paths)
2. the repo root absolute path
3. the repo directory basename

**New repo, no row?** The skill bootstraps: searches for a likely glossary/decisions, confirms with
you (or creates a new Glossary + Decisions pair under this index), then appends a row here so next
time it resolves with no prompt.

## Registry

| Repo key | Glossary (view_id) | Decisions (view_id) | Plane project (optional) | Notes |
| --- | --- | --- | --- | --- |
| git@github.com:you/your-repo.git | `<glossary-view-id>` | `<decisions-view-id>` | — | replace with your repo + its page IDs |
| bookstore-demo | `<sample-glossary-view-id>` | — | — | matched by basename; points at the imported *Bookstore — Glossary* sample |

*Plane project is optional (for tying decisions to work items); the skills only require the two
view_ids. Each repo's Glossary + Decisions pages live as children under this index.*
