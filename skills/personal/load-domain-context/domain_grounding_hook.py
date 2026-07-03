#!/usr/bin/env python3
"""SessionStart hook: inject this repo's AppFlowy domain glossary into context.

Deterministic counterpart to the `load-domain-context` skill. Runs every Claude Code
session start; resolves the current repo against the central registry in AppFlowy,
fetches its glossary, and emits it as additionalContext. Silent no-op when the repo
isn't registered or AppFlowy is unreachable — never blocks a session.

Creds are read from the user-level appflowy-mcp config (~/.claude.json) — single source,
no duplicated secrets here. The two global IDs (workspace + registry index view) come from a
`## Domain store` block in ~/.claude/CLAUDE.md — the same single source the model-invoked skills
read, so hook and skills never disagree. See skills/personal/SETUP.md. Run under the same env as
the MCP server ($APPFLOWY_MCP_DIR points at your appflowy-mcp checkout):

  cd "$APPFLOWY_MCP_DIR" && uv run --with "fastmcp>=3.1.1" --with python-dotenv \
    --with httpx --with pydantic --with appflowysdk --with "pycrdt>=0.10.0" \
    python <this file>
"""
import datetime
import json
import os
import re
import subprocess
import sys

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
LOG_PATH = os.path.expanduser("~/.claude/domain-grounding.log")
PROJECT_MARKERS = ("CLAUDE.md", "AGENTS.md", ".mcp.json", "package.json",
                   "pyproject.toml", "go.mod", "Cargo.toml", ".git")
NUDGE = (
    "INSTRUCTION FOR CLAUDE: At the very start of your first reply this session, show the "
    "user the quoted line below verbatim (it's a call to action only they can take). Show it "
    "once; don't repeat it later in the session.\n\n"
    "> 📍 **This repo isn't registered for domain context.** No AppFlowy glossary was loaded. "
    "Run `/grill-with-context` to set it up — it'll interview you and save this repo's glossary "
    "+ decisions to AppFlowy, after which every session auto-loads them."
)
SETUP_NUDGE = (
    "INSTRUCTION FOR CLAUDE: At the very start of your first reply this session, show the "
    "user the quoted line below verbatim (it's a call to action only they can take). Show it "
    "once; don't repeat it later in the session.\n\n"
    "> ⚙️ **Domain context isn't configured yet.** Add a `## Domain store` block to "
    "`~/.claude/CLAUDE.md` with your AppFlowy `workspace_id` and registry `view_id` — see "
    "`skills/personal/SETUP.md`. Until then no glossary can be loaded."
)


def _log(status, detail=""):
    """Append an audit line so hook runs are provable; failures are ignored."""
    try:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        with open(LOG_PATH, "a") as f:
            f.write(f"{ts}\t{status}\t{detail}\n")
    except Exception:
        pass


def _bail(status="noop", detail=""):
    """Exit cleanly with no context injected; record why in the audit log."""
    _log(status, detail)
    if status != "noop" and detail:
        print(detail, file=sys.stderr)
    sys.exit(0)


def _repo_keys(cwd):
    """Candidate keys for the current repo, in priority order."""
    keys = []
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            keys.append(r.stdout.strip())
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        root = r.stdout.strip() if r.returncode == 0 else cwd
    except Exception:
        root = cwd
    keys.append(os.path.abspath(root))
    keys.append(os.path.basename(os.path.abspath(root)))
    return [k for k in keys if k]


def _is_project(cwd):
    """Heuristic: is this a project dir worth nudging (vs ~ or /tmp)?"""
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip() == "true":
            return True
    except Exception:
        pass
    return any(os.path.exists(os.path.join(cwd, m)) for m in PROJECT_MARKERS)


def _emit(context):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


def _resolve_store_ids():
    """The two global AppFlowy IDs (workspace + registry index view).

    Single canonical source: a `## Domain store` block in ~/.claude/CLAUDE.md — the same place the
    model-invoked skills read, so hook and skills never disagree. Returns (workspace_id,
    registry_view_id), or (None, None) when unconfigured. No creds needed, so it runs first.
    """
    try:
        with open(os.path.expanduser("~/.claude/CLAUDE.md")) as f:
            text = f.read()
    except OSError:
        return None, None
    block = re.search(r"(?ims)^##\s+Domain store\b.*?(?=^##\s|\Z)", text)
    if not block:
        return None, None
    b = block.group(0)
    wm = re.search(r"workspace[ _-]?id\D{0,40}?(" + UUID_RE.pattern + ")", b, re.I)
    rm = re.search(r"registry\D{0,40}?(" + UUID_RE.pattern + ")", b, re.I)
    return (wm.group(1) if wm else None), (rm.group(1) if rm else None)


def _load_creds_into_env():
    """Pull appflowy-mcp env (BASE_URL, APPFLOWY_EMAIL/PASSWORD) from ~/.claude.json."""
    cfg = os.path.expanduser("~/.claude.json")
    with open(cfg) as f:
        data = json.load(f)
    env = ((data.get("mcpServers") or {}).get("appflowy-mcp") or {}).get("env") or {}
    for k, v in env.items():
        os.environ.setdefault(k, str(v))
    if not os.environ.get("APPFLOWY_EMAIL"):
        _bail("error", "appflowy-mcp creds not found in ~/.claude.json")


def _match_glossary(registry_md, keys):
    """Find the glossary view_id for this repo from the registry table."""
    best = None
    for line in registry_md.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        repo_key = cells[0]
        if repo_key.lower() in ("repo key", "") or set(repo_key) <= set("-: "):
            continue  # header / separator
        ids = UUID_RE.findall(cells[1])
        if not ids:
            continue
        glossary_id = ids[0]
        # exact match on remote URL / absolute path
        if repo_key in keys:
            return glossary_id
        # basename fallback
        if os.path.basename(repo_key) == os.path.basename(keys[-1]):
            best = glossary_id
    return best


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()

    keys = _repo_keys(cwd)
    if not keys:
        _bail("noop", f"no repo keys cwd={cwd}")

    # Resolve the two global IDs first (no creds needed) so an unconfigured user gets the friendly
    # setup nudge rather than a terse creds error.
    workspace_id, registry_view_id = _resolve_store_ids()
    if not (workspace_id and registry_view_id):
        # Unconfigured (no `## Domain store` in ~/.claude/CLAUDE.md): nudge to set up, don't crash.
        if _is_project(cwd):
            _log("unconfigured", f"cwd={cwd}")
            _emit(SETUP_NUDGE)
        else:
            _log("noop", f"unconfigured non-project cwd={cwd}")
        sys.exit(0)

    _load_creds_into_env()
    mcp_dir = os.environ.get("APPFLOWY_MCP_DIR")
    if not mcp_dir:
        _bail("error", "APPFLOWY_MCP_DIR not set in appflowy-mcp env")

    sys.path.insert(0, mcp_dir)
    try:
        import main as af  # noqa: E402  (env must be set first)
        af.client.login()
        registry = af.appflowy_get_page_markdown(workspace_id, registry_view_id)["markdown"]
    except Exception as e:
        _bail("error", f"AppFlowy unreachable: {e}")

    glossary_id = _match_glossary(registry, keys)
    if not glossary_id:
        # Not registered: nudge in real project dirs, stay silent elsewhere.
        if _is_project(cwd):
            _log("nudge", f"cwd={cwd}")
            _emit(NUDGE)
        else:
            _log("noop", f"unregistered non-project cwd={cwd}")
        sys.exit(0)

    try:
        glossary = af.appflowy_get_page_markdown(workspace_id, glossary_id)["markdown"]
    except Exception as e:
        _bail("error", f"glossary fetch failed: {e}")

    _log("loaded", f"cwd={cwd} glossary={glossary_id}")

    repo_name = os.path.basename(keys[-1].rstrip("/")) or keys[-1]
    n_terms = len(re.findall(r"(?m)^\*\*.+?\*\*\s*:", glossary))
    terms_str = f" ({n_terms} glossary term{'s' if n_terms != 1 else ''})" if n_terms else ""
    context = (
        "INSTRUCTION FOR CLAUDE: At the very start of your first reply this session, show the user "
        "this confirmation line verbatim (once; don't repeat later):\n\n"
        f"> ✓ **Domain context loaded** for `{repo_name}` from AppFlowy{terms_str}. "
        "Edit via `/grill-with-context` or `/domain-context-mcp`.\n\n"
        "Then use the glossary below as this repo's ubiquitous language for the session. The glossary "
        "and decisions live in AppFlowy, not the repo — don't create local CONTEXT.md / docs/adr "
        "files; write changes back via `/domain-context-mcp`.\n\n"
        f"---\n\n{glossary.strip()}"
    )
    _emit(context)


if __name__ == "__main__":
    main()
