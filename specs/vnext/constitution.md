# Ported engineering constitution

Source: `.specify/memory/constitution.md` on main `7168117db85befa4e9f36420d306c667ffc12cbf` (version 0.1, ratified 2026-09-30). The WI-CHG-0009 amendment in `c99355daf4889148dc517704bb6423de221d0770` is not imported (009 amendment / 009 state).

Business authority remains AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001.

## I. Flow-forward

A change to approved behavior creates a new feature directory. The previous directory stays readable and is marked superseded. Silent in-place replacement of an approved requirement is not the default.

The 009 amendment that keeps an in-flight Decision B on the same change id, branch, and pull request is not imported as AIC active-change status. Ancestry of an explicit new decision is WI-REQ-004 and WI-REQ-038.

## II. GitHub operator — not imported as a standing grant

Main constitution principle II said Cursor performs every GitHub read and write for `jakeguo117/workspace-infrastructure-vnext`.

That principle is not imported. See CONFLICTS C-017. Cursor is the engineering owner when a scoped task authorizes the work (WORKFLOW 6.2.6). Grok reads the result (WORKFLOW 6.2.7). This port grants no standing push or merge.

## III. NOT_VERIFIED

Unknown, stale, or conflicting state stays `NOT_VERIFIED`. Elapsed time, chat, agent memory, and a projection status do not upgrade it. A Linear status is not evidence. A Notion badge is not evidence (WORKFLOW “State, evidence and projection”).

## IV. No second orchestrator

Do not add a hosted coordinator, a webhook bus that holds authority, a second current engineering spec, or a second orchestrator.

Spec Kit files under `docs/vnext-port/specify/` are the ported VNext lifecycle engine. They do not replace AIC-DOC-WORKFLOW@0.2.0 and they are not installed as a live second skill router beside `skills/journal` and `skills/cognition`. See CONFLICTS C-ENGINE.

## Governance

Jake remains the decision authority and is not an executor role. A vendor is the current executor of a role, not the meaning of the step.

**Port version**: records main constitution 0.1, with principle II withheld. **Not adopted**: constitution 0.1.1 from WI-CHG-0009.
