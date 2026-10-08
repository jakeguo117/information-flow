<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Bug Fix: external authority binding

- **Slug**: external-authority-binding
- **Fixed**: 2026-09-30
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

The repository now has one authority graph. Preflight reads it. A fresh agent can identify local and external authorities from that graph, and a pinned external revision that does not match an observation stops for reconciliation.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `docs/authority-graph.json` | added | Canonical binding for requirements, Foundation, architecture, GitHub, and Linear |
| `docs/reconciliation.md` | modified | Procedure stays here. Identifiers stay in the graph |
| `PROJECT_STATE.md` | modified | Names the graph as the discovery path |
| `scripts/wi_authority_check.py` | added | Schema check, local verification, observation results |
| `scripts/wi_authority_check.sh` | added | Shell entry point |
| `scripts/wi_preflight.sh` | modified | Runs the authority check |
| `.cursor/agents/reviewer.md` | modified | Resolves authorities through the graph |
| `.cursor/agents/verifier.md` | modified | Resolves authorities through the graph |
| `.specify/workflows/change-lifecycle/workflow.yml` | modified | Plan step points at the graph |
| `.github/workflows/change-control.yml` | modified | Runs the authority self-test |

## Tests Added or Updated

- `scripts/wi_authority_check.sh --self-test` — reconstruction, missing binding, wrong identity, unavailable source, stale revision, and a matching observation

## Local Verification

- Commands run: `python3 scripts/wi_authority_check.py --self-test` → exit 0, `authority self-test: ok`
- Commands run: `python3 scripts/wi_authority_check.py --check` → exit 0, external roles `NOT_VERIFIED`, requirements `VERIFIED`
- Commands run: `bash scripts/wi_workflow_validate.sh` → exit 0
- Commands run: `bash scripts/wi_ownership_check.sh --check` → exit 0
- Commands run: `bash scripts/wi_secret_check.sh --check` → exit 0
- Commands run: `bash scripts/wi_acceptance_fixture_check.sh --expect B` → exit 0
- Manual checks: Drive metadata for the Architecture Baseline and the Foundation pack members was read again and matches the pins in the graph

## Deviations from Assessment

The external revision pin is Drive file size and modified time, plus the document version the source states. A content digest is optional in the checker and is not pinned, because the normative documents were not copied into Git.

## Follow-ups

- None inside this bug. `WI-CHG-0008` is not started.
