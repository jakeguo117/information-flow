# Cognition retrieval

Retrieval is additive prior context, not command authority. Do not route every chat through cognition.

## Trigger

Retrieve when Jake is:

- asking what to do on a consequential issue
- making a project direction or architecture decision
- changing business strategy
- planning a meaningful experiment
- revisiting a previously discussed thesis
- evaluating an outcome that may update prior cognition
- proposing something that may conflict with an existing Principle or Belief
- saying 「相关认知」「看看之前相关认知」「我们之前有没有相关判断？」

## Non-trigger

Do not force retrieval for trivial facts, casual conversation, simple wording edits, or low-consequence operational requests. If nothing relevant is found, continue normally and do not invent prior cognition.

## Search order

1. Identify current project / decision / domain / entities.
2. Search `📖 Cognition/{Evidence,Beliefs,Principles}` filenames, frontmatter `domains` / `related_projects`, claim / statement / trigger text, and wikilinks. No embeddings. No graph database.
3. Prefer active over contested; contested over retired only when history is needed; exact project/domain matches; newer superseding objects.
4. Expand top Principles via `based_on` → Beliefs, then Beliefs via `supporting_evidence` / `contradicting_evidence`.
5. Keep the smallest useful set (guidance: up to 3 Principles, 3 Beliefs, 5 Evidence).

## Result contract

Every retrieval ends in exactly one of:

| status | meaning |
|---|---|
| `found` | Store read succeeded and relevant cognition exists |
| `no_match` | Store read succeeded completely enough to claim absence; nothing matched |
| `partial` | Some retrieval succeeded, but failures make absence claims unsafe |
| `unavailable` | Store could not be accessed (including no cognition store yet) |

`partial` and `unavailable` must be disclosed. They must never be summarized as “no relevant cognition.”
Read failures (unreadable files, missing vault / cognition store, permission) are `partial` or `unavailable` — never `no_match`.

Also return matched IDs, warnings/errors, skipped/unreadable files, stale dependency flags, supersession information, and per-hit identity/provenance fields (`id`, `path`, `status`, `source` when present). Payloads stay bounded: claim/statement/trigger summaries only — never raw Journal or note body prose.

## Contradiction, contest, stale, history

- For every selected Belief, resolve readable `contradicting_evidence`. Material contradiction cannot be dropped to meet budget; drop lower-priority supporting Evidence first.
- Contested Belief/Principle may be shown when relevant; must be labeled contested; must not be treated as settled current context.
- Retired or superseded objects are historical only by default. An object actively superseded by a newer active object is history even if its stored `status` is still `active`.
- If a Principle’s material `based_on` Belief is retired or superseded, flag `stale_dependency` and surface it before relying on the Principle.
- Filename rename must not break retrieval: resolve by stable `id`.
- Malformed/unreadable **relevant** files produce `partial`, never a confident `no_match`.
- Broken links: report; do not infer the destination.

## Tool

```bash
python3 .cursor/skills/cognition/tools/retrieve_cognition.py --vault "$VAULT" --query "..." --project "..." --domain "..."
```

Stdout is JSON. Validator success is not semantic completeness.
