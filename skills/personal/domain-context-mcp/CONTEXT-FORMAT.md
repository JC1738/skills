# Glossary Format

The glossary lives as an **AppFlowy page** (the glossary `view_id` in the store config), not a local
`CONTEXT.md`. The content format below is identical to the markdown `CONTEXT.md` convention — only
the storage location differs.

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.

## Editing the AppFlowy page

To preserve inline marks and links, **read-then-write**: `appflowy_get_page_markdown` → edit the
returned markdown → `appflowy_update_page_from_markdown`. A plain end-of-page addition can use
`appflowy_append_markdown`. Reading raw `/json` and writing it back flattens inline formatting —
don't.

## Single vs multi-context

Single context (the current scope): one glossary page per repo. Multi-context — several AppFlowy
glossary pages mapped per bounded context — is deferred; if it comes up, ask the user which context
the current topic belongs to.
