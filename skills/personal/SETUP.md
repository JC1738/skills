# Setup — AppFlowy-backed domain-context skills

These four skills keep a repo's **domain model** (glossary + decisions/ADRs) in **AppFlowy**, read and
written live over MCP, instead of in local markdown:

| Skill | What it does |
| --- | --- |
| `load-domain-context` | Read-only: load this repo's glossary from AppFlowy into the session |
| `domain-context-mcp` | Add/sharpen terms, record decisions — write back to AppFlowy |
| `grill-with-context` | Relentless plan/design interview, grounded in the AppFlowy model (calls `/grilling`) |
| `improve-arch-with-context` | Scan for architecture improvements, grounded in the model (calls `/codebase-design`) |

They're the AppFlowy counterparts to mattpocock's markdown skills (`/domain-modeling`,
`/improve-codebase-architecture`, `/grilling`), which live in this same repo — so keep the whole repo's
skills discoverable (below), not just `personal/`.

> **Just want to see what it does?** The lightest path is: do steps 1–5, then run
> `/load-domain-context` manually against the bookstore sample (step 6). You do **not** need the
> SessionStart hook (step 7) for a first look.

## Prerequisites
- An **AppFlowy Cloud** account (self-hosted or hosted).
- A local checkout of the `appflowy-mcp` server (the MCP server these skills call):
  `git clone https://github.com/JC1738/Appflowy-MCP` — note the checkout path; it's your
  `APPFLOWY_MCP_DIR` below.
- Claude Code (for the SessionStart hook and skill discovery). Optional: a **Plane** workspace if you
  want decisions tied to work items.

## 1. Get the skills registered
`personal/` skills are intentionally excluded from this plugin's manifest, so a plain plugin install
won't register them. Two ways to make them (and the skills they call) discoverable:

**Recommended — link every skill at once:**

```bash
scripts/link-skills.sh
```

This symlinks every skill in the repo (all buckets) into `~/.claude/skills/` and `~/.agents/skills/`,
so `/load-domain-context`, `/domain-context-mcp`, `/grill-with-context`, `/improve-arch-with-context`
and their dependencies (`/grilling`, `/codebase-design`) are all registered in one shot. Because they're
symlinks into your clone, a `git pull` keeps them current — just leave the clone where it is. Re-run the
script after adding or renaming a skill.

**Or — copy just what you need** (if you'd rather not symlink, or want to move the clone later):

```bash
cp -r skills/personal/load-domain-context skills/personal/domain-context-mcp ~/.claude/skills/
cp -r skills/personal/grill-with-context skills/personal/improve-arch-with-context ~/.claude/skills/
cp -r skills/productivity/grilling skills/engineering/codebase-design ~/.claude/skills/
```

(`grill-with-context` calls `/grilling`; `improve-arch-with-context` calls `/codebase-design` — copy
those too or you'll hit a missing-skill error.)

Verify either way with `/help` or by typing `/load-domain-context`.

## 2. Configure MCP servers
Copy the template and fill in your own values:

```bash
cp .mcp.json.example .mcp.json    # .mcp.json is gitignored — your secrets stay local
```

- **`appflowy-mcp`** — put this block in your **user-level** `~/.claude.json` (not just project
  `.mcp.json`): the SessionStart hook reads your AppFlowy creds from `~/.claude.json`. Set
  `APPFLOWY_EMAIL`, `APPFLOWY_PASSWORD`, `BASE_URL`, and `APPFLOWY_MCP_DIR` (path to your `appflowy-mcp`
  checkout).
- **`plane`** (optional) — project-level `.mcp.json` is fine.

## 3. Create your registry index page in AppFlowy
Import `skills/personal/examples/sample-registry.md` into your workspace as a new page (call it
**Repo Domain Context (index)**). *In AppFlowy: hover a Space in the sidebar → `+` / right-click →
**Import** → **Text & Markdown** → pick the file.* This one page maps each repo → its glossary/decisions
pages.

## 4. Get your two global IDs
You need your **`workspace_id`** and the registry page's **`view_id`**. Either:
- open the registry page in AppFlowy and read them from the page URL / share link, **or**
- ask Claude (with `appflowy-mcp` running) to call `appflowy_list_workspaces` and
  `appflowy_get_workspace_folder` and report the workspace id + the page's view id.

## 5. Point the skills at your workspace (single source of truth)
Add a `## Domain store` block to your **`~/.claude/CLAUDE.md`** (global). Both the skills and the
SessionStart hook read the two IDs from here — one place, no drift:

```markdown
## Domain store

- workspace_id: <your-workspace-id>
- registry view_id: <your-registry-view-id>
```

This global block (in `~/.claude/CLAUDE.md`) holds the two **workspace + registry** IDs and is the only
thing the SessionStart hook reads. *(Separately, the model-invoked skills also honor a per-repo override
— a `## Domain store` block or `docs/agents/domain-store.md` in a **project's** own repo that points
straight at that repo's glossary/decisions pages, bypassing the registry lookup. The SessionStart hook
does not read per-repo overrides; it always resolves via the registry.)*

## 6. Five-minute first look
1. Import `skills/personal/examples/sample-glossary.md` as a child of your registry index (name it
   **Bookstore — Glossary**) — same Import → Text & Markdown flow as step 3, but right-click the
   registry index page so it nests underneath.
2. Copy its `view_id` (obtain it the same way as step 4) into the `bookstore-demo` row of your
   registry page (replace `<sample-glossary-view-id>`).
3. In a **plain directory named `bookstore-demo`** (`mkdir bookstore-demo` — not inside another git
   repo, or its `origin` URL would be matched instead of the basename), run `/load-domain-context`.
   You should see: *"✓ Domain context loaded for `bookstore-demo` from AppFlowy (7 terms)"* and the
   Bookstore glossary adopted for the session. That's the payoff.

## 7. (Optional) Enable auto-load via the SessionStart hook
Add a **SessionStart** hook to your Claude Code `settings.json` that runs
`domain_grounding_hook.py` under the `appflowy-mcp` env. Substitute both `/ABSOLUTE/PATH/TO/...`
placeholders with **literal absolute paths** — your `appflowy-mcp` checkout and this repo's hook
script. (Use real paths, not `$APPFLOWY_MCP_DIR`: a SessionStart hook's shell does not inherit the MCP
server's env block, so that variable would be empty here. The hook still reads `APPFLOWY_MCP_DIR` from
`~/.claude.json` internally for its own imports — that part is fine.)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd /ABSOLUTE/PATH/TO/appflowy-mcp && uv run --with \"fastmcp>=3.1.1\" --with python-dotenv --with httpx --with pydantic --with appflowysdk --with \"pycrdt>=0.10.0\" python /ABSOLUTE/PATH/TO/skills/personal/load-domain-context/domain_grounding_hook.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Then every session in a registered repo auto-injects its glossary — no manual invocation.
Unregistered repos get a one-line nudge; unconfigured setups get a "add a `## Domain store` block"
nudge instead of an error.

## 8. Author your own
In a real repo with no row yet, run `/grill-with-context` — it interviews you and writes a fresh
glossary + decisions into AppFlowy, then appends a registry row so future sessions auto-load it.

---

**Troubleshooting**
- *"Domain context isn't configured yet" nudge* → your `## Domain store` block (step 5) is missing or
  malformed in `~/.claude/CLAUDE.md`.
- *Hook error `APPFLOWY_MCP_DIR not set`* → add `APPFLOWY_MCP_DIR` to the `appflowy-mcp` env in
  `~/.claude.json` (step 2).
- *"This repo isn't registered" nudge* → expected for a repo with no registry row; run
  `/grill-with-context` (step 8) or add a row manually.
