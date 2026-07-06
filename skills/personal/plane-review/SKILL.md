---
name: plane-review
description: Organise and review a personal Plane project — label the un-triaged captures, then surface what's homeless, stale, up-next, and ready to hand to an agent.
disable-model-invocation: true
---

# Plane Review — organise + review a project

A deliberate sit-down over one personal **Plane** project (`CT` default, or `AI`). It does two
things: an **organise pass** that turns raw captures into properly-labelled items, and a **review
pass** that surfaces four lists so nothing rots. Same discipline whichever project you point it at —
"make AI clean just like CT."

This is the review half of the personal Plane pair; capture is `/plane-add`.

## Prerequisite: coordinates + login

- Reached through the `plane` MCP (omit `workspace_slug` — env-injected). If a call fails, **stop and
  tell the user**; never fall back to raw `curl`/`x-api-key`.
- Resolve the **project UUIDs** from your `## Plane store` block in `~/.claude/CLAUDE.md` (already in
  context — no tool call; see [personal/SETUP.md](../SETUP.md) to create it — ships no IDs). Default
  project = **CT**; accept **AI** as an argument (only if your block defines a second project); GEM is
  out of scope. **Per-project state and label UUIDs are discovered at runtime** (`list_states` /
  `list_labels`), never hardcoded.

## Reading the project (CE quirks — these bite)

- **Server-side `pql` filtering is silently ignored on this CE** — it returns the whole project. So
  **pull the full project and filter client-side.** `list_work_items(project_id, per_page=100,
  fields=id,name,state,labels,parent,created_at,target_date,priority)` and **loop `next_cursor` until
  exhausted** (per_page maxes at 100; a project can exceed it). `total_count` is reliable for counts.
- **Labels come back as UUIDs.** Build a UUID→name map once with `list_labels(project_id)` and reason
  in names.
- Never use `search_work_items` (returns empty on this CE).

## Organise pass — process the un-triaged queue

Walk items carrying `needs-triage`. For each, apply labels + priority in place, then drop
`needs-triage`. **Batched + resumable:** process up to ~10 per run, then stop and show progress —
because dropping `needs-triage` per item makes the pass idempotent, a partial run is safe and the next
run resumes. (The first CT run is the one-time retrofit of the ~30 unlabelled items; don't try to do
all of them in one sitting.)

Per item:

- **`repo:<name>`** for repo-bound work (primary axis) · **`area:<infra|product|strategy|tooling>`**
  for repo-less/cross-cutting work (growable set — reuse an existing value before inventing one).
  Repo-bound items don't need an `area:`.
  - **Per-project organizing vocabulary.** The above is **CT's** set. **AI** already has its own
    category taxonomy — `integration` / `enablement` / `ui` / `engine` (E4/E6/E7 verticals) /
    `foundation` (E1/E2/E3) — plus `repo:rw-data-chat` for the Data-Chat repo. When organising AI, an
    item is "organized" once it carries a `repo:*` **or** one of AI's categories; reuse those, don't
    graft CT's `area:` set onto AI. (Data-Chat work → `repo:rw-data-chat`.) The homeless/unorganized
    test below is always computed against **the project's own** organizing set.
- **Workflow** where it applies: `blocked` (external dep), `decision-needed` (needs leadership /
  discussion), `reference` (context doc, **not** an action).
- **`priority`** — set the Plane field (`urgent|high|medium|low|none`).
- **`defer:YYYY-MM-DD`** if it's a deliberate wait-and-see / revisit-later; **`target_date`** for a
  real deadline.
- Drop `needs-triage` last.

**Label writes: `update_work_item(labels=[full desired array])` with read-merge-write.** (The atomic
`manage_work_item_label` tool is **broken on this CE** — it errors on the response and does not mutate;
verified. `update_work_item(labels=)` is the only working path.) Because `labels=` **replaces** the
whole array, you MUST merge, never clobber: `retrieve_work_item(expand="labels")` → take the existing
label ids → add/remove the ones you want → `update_work_item(labels=[…merged…])`. Read back and confirm
the count to catch an accidental wipe. Setting only `priority`/`state`/`target_date` via
`update_work_item` (without `labels=`) is safe — labels are left untouched. Reuse-or-create labels
against **this** project (`list_labels` → match by name → else `create_label`; on 409 re-list and use
the existing id).

## Review pass — the four lists

Produce the report ([REVIEW-REPORT.md](./REVIEW-REPORT.md) for the exact shape). Compute over
organised items (exclude anything still carrying `needs-triage` — it's new, not forgotten):

1. **Homeless / misfiled** — an **open** item (state `group` not `completed`/`cancelled`), **not**
   `reference`, carrying **none of this project's organizing labels** (CT: `repo:*`/`area:*`; AI:
   `repo:*` or a category — `integration`/`enablement`/`ui`/`engine`/`foundation`; the AI set is the
   author's example — each project defines its own). Closed and `reference` items are excluded —
   neither needs a home. Walk these and give each a home.
2. **Stale / forgotten** — age from **`created_at`** (immutable) for items still in `Backlog`/`Todo`,
   **excluding** anything with a future `defer:` date. **Never use `updated_at`** — your own organise
   edits bump it, which would reset every item to "fresh" and permanently hide the truly-forgotten
   ones. (Richer signal if wanted: `list_work_item_activities` → last *human* touch.)
3. **Next up** — candidates ranked by `priority` + readiness + age, each shown **with the reason it's
   waiting** rather than force-ranked: `target_date` (due/overdue), `decision-needed`, `blocked`,
   `defer:<date>` (hidden until due). Surface `defer:` dates that have now arrived as *resurfaced*.
4. **Ready-for-Claude** — items specified enough for an AFK agent. For each, **write a durable agent
   brief as a Plane comment** and add `ready-for-agent`. Brief format: current behavior / desired
   behavior / key interfaces / acceptance criteria / out-of-scope — behavior-based and path-free so it
   survives code drift. This is opt-in per item (don't brief everything); it's the expensive step, so
   keep it separate from the cheap organise pass. If a brief grows large, write it to AppFlowy and drop
   the link in a short comment.

## Promotion CT→AI (rare — recreate-and-close is the ONLY path on CE)

If review decides a CT item truly belongs to the AI Initiative, note it — but **Plane CE v1.3.1 has no
cross-project move OR copy**. The API can't move items (no settable `project`), and the web-UI "Make a
copy → different project" is **Pro-gated** (shipped in Commercial v1.13.0, Jul 2025) so it's absent in
CE — verified against the docs. There is no "drag between projects" in CE; earlier guidance to do that
was wrong.

So the only path is **recreate-and-close**, done deliberately and human-approved:
1. `create_work_item` in AI (Backlog + AI's own label taxonomy — labels are per-project UUIDs, so map,
   don't copy CT's; e.g. CT's `area:product` diagnostics work → AI's `engine` label). Carry over the
   description and **any agent-brief comment** (comments do NOT come along — copy their text into the
   new description or re-post as a comment).
2. Comment on the CT item pointing at the new `AI-#`, then set it to **Cancelled**.

This loses nothing when the source has no comment thread; when it does, copy that across first. Never
auto-promote. (A future Commercial/Pro upgrade would add the copy path — revisit then.)

## Confirm

Show the report, say how many items were organised this run, and what remains un-triaged (so the user
knows whether to run again).
