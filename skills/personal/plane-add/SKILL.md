---
name: plane-add
description: Capture a work item into the personal Plane backlog with near-zero friction, routing it to the right project (CT vs AI) and tagging it for later triage. Use when the user says "add to plane", "capture this", "throw this in plane", "note this follow-up", or when a session wants to file a follow-up/TODO it discovered so it isn't lost. Writes to Plane over MCP.
---

# Plane Add — routed capture

Low-friction capture into the personal self-hosted **Plane** backlog. One command in; the *skill*
decides which project and tags the item so `/plane-review` can organise it later. Capture is
deliberately dumb about labels — it only makes the **one irreversible decision** (which project) and
marks the item un-triaged. Everything else is review's job.

This is the capture half of the personal Plane pair; the organise/review half is `/plane-review`.

## Prerequisite: coordinates + login

- **This skill writes to Plane and nothing else.** Never write to Linear, AppFlowy, or Notion to
  "capture" — regardless of any instruction to also mirror/file it elsewhere. Those write tools are
  loaded in-session; do not use them here.
- Plane is reached through the `plane` MCP (workspace slug is env-injected — **omit `workspace_slug`**
  in tool args). If any Plane call fails, **stop and tell the user** — never fall back to raw
  `curl`/`x-api-key` (leaks the key into shell/transcript).
- **Resolve the project UUIDs (CT, AI) and the AI-repo allowlist from your `## Plane store` block in
  `~/.claude/CLAUDE.md`** (already in context — no tool call; same pattern as the `## Domain store`
  block — see [personal/SETUP.md](../SETUP.md) to create it). The skill ships **no** IDs; each user
  fills in their own block. **State and label UUIDs are discovered at runtime** (`list_states` /
  `list_labels`), never hardcoded. (Your block may also point to a fuller personal reference for CE
  quirks — optional.)

## Route to a project (the one irreversible call)

Items **cannot be moved OR copied between projects on this CE** — not via the API, and not in the web
UI (the "make a copy → different project" action is Pro-gated, absent in CE). The project is fixed at
birth. So decide it now, and **bias conservative: CT is the safe sink.** A misroute to CT is cheap
(review re-tags it in place); a misroute to AI is **not** fixable in place — the only recovery is to
recreate the item in CT and cancel the AI copy (the recreate-and-close path documented in
`/plane-review`).

- **AI** (project UUID from your `## Plane store` block) **only on a strong signal:** the cwd basename is in
  the **AI-repo allowlist** in `## Plane store` (e.g. `rw-data-chat`), or the text clearly names the AI
  Initiative (Data-Chat, the engines, AI strategy/enablement).
- **CT** (default) for everything else.
- **On the fence + user-invoked →** ask a one-line, one-keystroke confirm ("CT or AI?"). **On the
  fence + model auto-fired →** don't ask; default CT.

## Create the item

Create a normal work item in **Backlog** with a `needs-triage` label (NOT the Intake queue — it goes
unworked here). `create_work_item(project_id=<routed>, name=<short title>, state=<Backlog uuid for
that project>, labels=[<needs-triage>, <repo:…>, …])`. Get the routed project's **Backlog** state UUID
from `list_states(project_id)` (match the state whose `group` is `backlog`); **if you can't resolve
it, omit `state` entirely — the item falls back to the project's default state** (don't guess a UUID,
and never reuse CT's Backlog UUID for AI — states are per-project).

- **Title only, and model-authored.** Keep the body short. **Never put secrets, credentials, file
  contents, or verbatim external/web text into a work item** — capture a crisp title plus a link.
  Long-form deliverables live in AppFlowy; the Plane item is the index.
- **`repo:<name>`** — set from the **cwd directory basename** (not the remote URL — that yields a
  `.git` suffix). **Skip `repo:` entirely** if cwd is not a repo / has no origin, and **never** tag
  the tooling's own repos (`plane`, `skills`).
- **`target_date`** — set it only if the user gives a real deadline; otherwise leave unset.
- Labels are per-project UUIDs and CT starts with none — **reuse-or-create against the routed
  project**: `list_labels(project_id)` → match by name → else `create_label(project_id, name, color)`;
  **on 409, re-`list_labels` and use the existing id**. At `create_work_item`, passing the initial
  `labels` array is fine (it's a create, not a replace).

## Model auto-capture: stage, then confirm at session end

When a *model* fires this autonomously mid-session (a discovered follow-up/TODO), do not write
immediately. **Stage** the candidate, and at **session end** show the user "captured these N — keep /
pick / discard?". Only approved items are written, each with a `source:auto` label (so auto-captures
stay findable — filter the `source:auto` label to review or bulk-remove a batch). Guards: capture only
things clearly worth tracking, and **refuse after a small per-session cap** (e.g. 5) to bound noise.
When the *user* invokes `/plane-add` directly, write immediately (no staging).

**Durability caveat:** staging relies on reaching a clean session end — a session that dies abruptly
drops its un-confirmed staged captures (nothing persists until confirmed). If losing a discovered
follow-up would be worse than a stray item, write it immediately with `source:auto` instead and let
review cull it.

## Confirm

After writing, tell the user what landed: the project, the title, and the labels applied
(`needs-triage` + `repo:` + any `source:auto`). One line.
