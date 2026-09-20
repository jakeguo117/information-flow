# Cognition layout

Canonical private storage in DigitalBrain:

```
📖 Cognition/
  Evidence/
  Beliefs/
  Principles/
```

information-flow holds schema, skills, tools, and synthetic fixtures only. Jake’s real Evidence / Beliefs / Principles stay in DigitalBrain. Never copy private cognition into this public repo, GitHub issues, or example files.

## Add-layer-only

The first DigitalBrain mutation for V1.1 is adding this layer. Do not:

- bulk-delete historical folders
- bulk-convert Journal or `📖 Resources/` into Cognition
- rewrite `📖 Resources/SCHEMA.md` (that wiki schema is a sibling, not this layer)
- invent `Candidates/`, `Decisions/`, `Outcomes/`, or a graph directory

Candidate Cognition stays conversational until Accept.

## Directory creation

Create `📖 Cognition/` and a type directory **only during an explicit approved write** of that type. Retrieval against a missing store returns `unavailable` / “no cognition store yet”, and must not create folders.

Files must live in the matching type directory. Markdown outside `📖 Cognition/{Evidence,Beliefs,Principles}` fails when validating that tree.

Default filename: `{id}.md`. Rename is allowed; `id` does not change.

## Git

Write locally. Precise paths. No `git add -A`. Do not automatically push Cognition. Digest’s direct-to-main habit is not inherited.

## Skill sync

`scripts/sync_digitalbrain_skills.py` copies cognition skill / references / tools into DigitalBrain `.cursor/skills/`. It must not rewrite Journal, Digests, Resources, or Cognition **content**.
