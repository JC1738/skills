---
name: plane-digest
description: Produce a short daily digest of the personal Plane backlog (CT + AI) — counts of unorganized, stale, decision-needed, ready-for-agent, needs-triage, and defers now due — so review actually happens instead of items rotting silently. Read-only. Use on demand, or schedule it to run daily.
---

# Plane Digest — the daily anti-rot nudge

A tiny read-only summary of the personal **Plane** backlog. Its whole job is to make `/plane-review`
*happen*: a once-a-day line of counts turns silent rot into a visible nudge. Read-only — it never
writes to Plane.

## Prerequisite: coordinates + login

Reached through the `plane` MCP (omit `workspace_slug`). Resolve the **CT** and **AI** project UUIDs
from your `## Plane store` block in `~/.claude/CLAUDE.md` (already in context — no tool call; see
[personal/SETUP.md](../SETUP.md) to create it — ships no IDs). State/label UUIDs are discovered at
runtime via `list_states` / `list_labels`. If a Plane call fails, say so briefly and stop.

## Compute (client-side — PQL is dead on this CE)

For **each** project configured in your `## Plane store` block (typically CT and AI — run only the
projects you've configured): pull the full project (`list_work_items`, sparse
`fields=id,name,state,labels,parent,created_at,target_date,priority`, **loop `next_cursor`**), build a
`list_labels` UUID→name map, then count client-side:

- **needs-triage** — items carrying `needs-triage` (raw captures awaiting organise).
- **unorganized** — actionable items **in an open state (not `Done`/`Cancelled`)**, not `reference`,
  carrying **no organizing label**, whether or not they have `needs-triage`. **A project's organizing
  labels are per-project** — they're the ones that say *what kind of work this is*:
  - **CT** → any `repo:*` **or** `area:*` label.
  - **AI** → any `repo:*` label (currently just `repo:rw-data-chat` for the Data-Chat repo) **or** an
    AI category label (`integration`, `enablement`, `ui`, `engine`, `foundation`). AI has **no**
    `area:` and doesn't use `repo:` broadly, so scoring AI against CT's `repo:`/`area:` rule wrongly
    flags *every* AI item as unorganized (the misleading "92"). Score each project against **its own**
    organizing set. (`blocked`/`decision-needed`/`reference`/`meeting-prep` are workflow, not
    organizing — they don't count.)

  Excluding closed states is load-bearing: a finished item is not "unorganized backlog," and counting
  the Done/Cancelled pile inflates the number (e.g. CT's raw 30 was really 19 open + 11 closed). This
  catches the **legacy unlabeled backlog** that predates capture — items that would otherwise read as
  "clean" because they lack a `needs-triage` label yet have never been through a review pass. This is
  the number that should drive the first `/plane-review` retrofit runs; don't let it hide.
- **stale** — in `Backlog`/`Todo`, `created_at` older than the threshold (default 30d), **not**
  carrying a future `defer:` date, and **not** carrying `needs-triage` (those are counted as
  needs-triage, not stale — same exclusion `/plane-review` uses, so the two surfaces reconcile).
- **decision-needed** — carrying `decision-needed`.
- **ready-for-agent** — carrying `ready-for-agent`.
- **defers now due** — items whose `defer:YYYY-MM-DD` date is today or past (time to resurface).
- **overdue** (optional) — `target_date` in the past and not Done/Cancelled.

## Emit

One compact block per project, plus the pointer to act:

```
Plane · CT — 30 unorganized · 0 needs-triage · 0 stale · 0 decision-needed · 0 ready-for-agent
Plane · AI — 51 unorganized · 3 decision-needed
→ run /plane-review CT   (30 unorganized — start the retrofit)
```

Keep it to a few lines. Lead with **unorganized** when it's non-zero (it's the backlog needing a
review pass). Only say "backlog clean" when unorganized, needs-triage, stale, decision-needed, and
defers-due are all zero.

## Scheduling & delivery

This skill only *produces* the digest. To run it daily, wrap it in a routine with `/schedule` (or
claude-cron), e.g. a prompt like *"Run /plane-digest and post the result to <channel>."* Pick one
delivery sink: a Slack DM/channel, an email, or a comment on a pinned Plane "daily digest" item.
Default suggestion: Slack DM to yourself — lowest friction, shows up where you already look.
