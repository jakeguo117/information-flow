<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Bug Verification: external authority binding

- **Slug**: external-authority-binding
- **Tested**: 2026-09-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified locally

## Summary

A process that starts from `PROJECT_STATE.md` can name the requirements, workflow, architecture, implementation, and projection authorities. Removing a required binding fails. A wrong external identifier fails. An unavailable source stays `NOT_VERIFIED`. A stale pinned revision asks for reconciliation.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reconstruction | `python3 scripts/wi_authority_check.py --self-test` | pass | `self-test reconstruction: PASS` |
| Missing binding | same self-test | pass | Exit path 10, `authority-graph: FAIL` |
| Wrong identity | same self-test | pass | Exit path 11, `identity=FAIL` |
| Unavailable source | same self-test | pass | Exit 0, architecture `identity=NOT_VERIFIED` |
| Stale revision | same self-test | pass | Exit path 12, `revision=RECONCILE` |
| Offline check | `python3 scripts/wi_authority_check.py --check` | pass | External roles stay `NOT_VERIFIED` |
| Workflow regression | `bash scripts/wi_workflow_validate.sh` | pass | `workflow validate: ok` |
| Ownership and secrets | ownership and secret checks | pass | Both exit 0 |
| Acceptance fixture | `bash scripts/wi_acceptance_fixture_check.sh --expect B` | pass | `fixture: ok behavior=B` |
| Preflight | `bash scripts/wi_preflight.sh --check` | pending clean tree | Run after this record is committed |

## Output Excerpts

`authority self-test: ok`

`authority-graph: ok`

## Residual Risks

- Offline preflight cannot prove the Drive bytes. It reports `NOT_VERIFIED` for those roles until an observation is supplied.
- The revision pin is size and modified time. A Drive write updates the modified time and then fails closed against this pin.

## Recommendation

Independent review and verification still have to name the commit that contains this fix. This file records the local checks only.
