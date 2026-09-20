# Cognition schema 1.1

Normative contract: Technical Design §32 (supersedes earlier TD examples). `schema_version` must be `"1.1"`. Skill, validator, retrieval, and writes all support only this version. Newer unsupported versions: do not interpret, validator fails, write stops.

## Identity

Stable IDs, independent of filename:

```
evidence-YYYYMMDD-short-slug
belief-YYYYMMDD-short-slug
principle-YYYYMMDD-short-slug
```

Unique inside `📖 Cognition/`. Rename must not change `id`. Duplicate IDs are validator errors. Machine relations store **IDs**, never filenames or wikilink display names. Body may still use wikilinks.

## Authoritative relations (persist only these)

| Field | Source | Target | Meaning |
|---|---|---|---|
| `Belief.supporting_evidence` | belief | evidence | Evidence supports the Belief |
| `Belief.contradicting_evidence` | belief | evidence | Evidence contradicts or weakens the Belief |
| `Principle.based_on` | principle | belief | Principle is derived from / motivated by the Belief |
| `supersedes` | belief or principle | same type | Source replaces the target |
| `related_to` | any | any | Non-authoritative context only |

Reverse edges are derived at retrieval. Do **not** persist: `Evidence.supports`, `Evidence.contradicts`, `Belief.supports`, `Belief.contradicts`, `superseded_by`, `derived_from`, `motivates`, `applies_to`.

`related_projects` and `source_journals` are metadata, not graph edges. Empty lists are valid. Unresolved IDs and wrong target types are structural errors.

## Common required fields

```yaml
schema_version: "1.1"
id: belief-20260920-short-slug
type: belief          # evidence | belief | principle
status: active
domains: []
related_projects: []
created: 2026-09-20
updated: 2026-09-20
origin_type: journal  # journal | direct_reflection | project_outcome | external_source
origin_ref: "[[journal-wikilink]]"
# origin_summary: "..."   # required when origin_ref is absent
```

## Evidence

Required: `claim`, `source`, `source_type`, `validation` (`unverified|checked|corroborated`), `reliability` (`low|medium|high`), `scope`, `limitations`.

Status: `active|retired`. Unknown scope/limitations must be explicit (`unknown` / `not established`); omitting the field is invalid.

Body must include append-only `## Validation History`.

## Belief

Required: `statement`, `confidence` (`low|medium|high`), `supporting_evidence`, `contradicting_evidence`.

Status: `active|contested|retired`.

Body must include append-only `## Revision History`.

## Principle

Required: `trigger`, `preferred_action`, `rationale`, `based_on`, `scope`, `exceptions`.

Status: `active|contested|retired`.

Body must include append-only `## Revision History`.

## Status transitions

Belief / Principle: `active ↔ contested`, `active → retired`, `contested → retired`. `retired → active` only with explicit Jake reactivation. `retired → contested` is not used.

Evidence: `active → retired`; `retired → active` only with explicit reactivation. Validation moves independently, both directions, only with persisted basis and authorization. Temporary source unavailability is not by itself a downgrade.

## Supersession

Same type only; not self; no cycles. Old file remains. Reverse `superseded_by` is derived. If active A supersedes B, retrieval treats B as history even if `B.status` is still `active`.

## Write authorization

Session-local and content-specific. Create binds to type, id/path, semantic payload, relationships. Update binds to id, before→after diff, and the pre-write fingerprint observed when the diff was shown. A direct Jake instruction that names the mutation is authorization for that mutation.

Create approval does not authorize mutating a duplicate, retiring something else, or git push. If the target fingerprint changed: stop, reload, re-authorize (unless the current direct instruction already covers the new diff).

## Validator

Canonical implementation: `tools/validate_cognition.py` (shared logic in `cognition_lib.py`). Exit 0 if valid, non-zero on schema/structure errors. It does not judge whether a Belief is true and does not rewrite files.
