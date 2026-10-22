# Cognition schema 1.2

Normative contract: Technical Design §32 (supersedes earlier TD examples), plus schema 1.2. Current `schema_version` is `"1.2"`. `"1.1"` stays valid: existing 1.1 files load and validate unchanged. Validator, retrieval, and writes support only `"1.1"` and `"1.2"`. Newer unsupported versions: do not interpret, validator fails, write stops.

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
schema_version: "1.2"   # "1.1" remains valid
id: belief-20260920-short-slug
type: belief          # evidence | belief | principle
status: active
domains: []
related_projects: []
created: 2026-09-20
updated: 2026-09-20
origin_type: journal  # journal | direct_reflection | project_outcome | external_source | value_choice
origin_ref: "[[journal-wikilink]]"
# origin_summary: "..."   # required when origin_ref is absent
```

`value_choice` is schema 1.2 and only valid on a Principle. It records a value preference that need not be derived from a Belief.

## Evidence

Required: `claim`, `source`, `source_type`, `validation` (`unverified|checked|corroborated`), `reliability` (`low|medium|high`), `scope`, `limitations`.

Optional on schema 1.2: `fact_ref`, a stable Fact node id (`fact-` plus 12 lowercase hex digits, the facts-0.1 `fact_id`). Reference the Fact. Do not copy its `statement` into `fact_ref`. Schema 1.1 Evidence omits `fact_ref`. A copied statement, any other shape, `fact_ref` on schema 1.1, or `fact_ref` on a non-Evidence object is a validator error. `fact_ref` is not a cognition-graph edge; the Fact node is not required to live under `📖 Cognition/`.

Status: `active|retired`. Unknown scope/limitations must be explicit (`unknown` / `not established`); omitting the field is invalid.

Body must include append-only `## Validation History`.

## Belief

Required: `statement`, `confidence` (`low|medium|high`), `supporting_evidence`, `contradicting_evidence`.

Status: `active|contested|retired`.

Body must include append-only `## Revision History`.

## Principle

Required: `trigger`, `preferred_action`, `rationale`, `based_on`, `scope`, `exceptions`.

`origin_type: value_choice` may persist `based_on: []`. Other origin types keep the 1.1 rule: `based_on` is a required list of Belief ids. An empty list stays valid so existing 1.1 Principles do not fail.

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

A retrieval conflict hint is not authorization to change a Belief. Changing a Belief needs update authorization bound to that id and diff. `## Revision History` is append-only.

## Retrieval conflict (AC11)

`retrieve` accepts optional in-memory Fact records (`fact_id`, `validation_state`, and any other facts-0.1 fields the caller already has). It does not read a facts file and does not copy a Fact `statement` into the result. For one `fact_id`, the last record in the supplied list is current.

When a returned Belief lists supporting Evidence whose `fact_ref` is F, and the current record for F has `validation_state` `disputed` or `corrected`, the result includes a `conflicts` entry: belief id, evidence id, `fact_ref`, and that validation state. The Belief file is not modified.

## Validator

Canonical implementation: `tools/validate_cognition.py` (shared logic in `cognition_lib.py`). Exit 0 if valid, non-zero on schema/structure errors. It does not judge whether a Belief is true and does not rewrite files. Supported `schema_version` values are `"1.1"` and `"1.2"`.
