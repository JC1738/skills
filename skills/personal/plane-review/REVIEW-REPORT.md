# Review report format

The `/plane-review` review pass outputs a single terminal-friendly report (markdown). Keep it
scannable — the point is to decide, not to read prose. One project per report; header names the
project and the counts.

## Shape

```markdown
## Plane review — <PROJECT> (<N> items · <M> still needs-triage)

### 🏠 Homeless (<n>)  — open, no organizing label (CT: repo:/area: · AI: repo:/category) — excludes `reference` + `needs-triage`
- <title>  ·  _suggest: repo:<x> / area:<y>_
- …

### 🕸 Stale (<n>)  — in Backlog/Todo, created >Nd ago, not deferred
- <title>  ·  created <YYYY-MM-DD> (<Nd>)  ·  priority <p>
- …

### ⏭ Next up (<n>)
- <title>  ·  priority <p>  ·  _reason: due <date> / decision-needed / blocked / resurfaced (defer reached)_
- …

### 🤖 Ready-for-Claude (<n>)  — brief written ✎ / candidate ○
- ✎ <title>  ·  brief posted
- ○ <title>  ·  _looks ready — write brief? (opt-in)_
- …
```

## Rules

- **Order the lists by urgency of attention:** Homeless and Stale first (they're the rot), then Next
  up, then Ready-for-Claude.
- **Homeless** — always offer a concrete `repo:`/`area:` suggestion so the fix is one confirmation.
- **Stale** — show `created_at` and the age in days; never `updated_at`. Omit anything with a future
  `defer:`.
- **Next up** — every line carries its *reason*, not a manufactured global rank. Items whose `defer:`
  date has arrived are tagged `resurfaced`.
- **Ready-for-Claude** — mark whether a brief was actually written (✎) or the item is just a candidate
  (○). Briefing is opt-in per item; don't auto-brief the whole list.
- Keep each line to one row; if a title is long, truncate — the item id/link is the source of truth.
- End with a one-line footer: `<k> organised this run · <M> still needs-triage · run again to continue`.
