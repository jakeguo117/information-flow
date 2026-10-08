<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Bug Assessment: external authority binding

- **Slug**: external-authority-binding
- **Created**: 2026-09-30
- **Source**: pasted text
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

A fresh agent given only this repository cannot locate the Foundation workflow authority or the Architecture Baseline. Those sources are outside Git. The repository names them in prose and tells the reviewer to compare against the Architecture Baseline, but it has no complete machine-readable binding. The agent fails closed instead of inventing the sources.

## Symptom

Approved behavior says a new session can resume from durable records and authority pointers, and that Jake does not carry routine context. The current repository does not let a fresh agent reconstruct the external authority graph. Expected behavior is one canonical binding that identifies local and external authorities and fails closed when a pinned external revision cannot be confirmed.

## Reproduction

1. Clone `jakeguo117/workspace-infrastructure-vnext` at `main` `e1857e12b6593658fa8aeac87260b3790b9e0cb9` with a clean tree.
2. Read `PROJECT_STATE.md`, `docs/reconciliation.md`, `.cursor/agents/reviewer.md`, and `scripts/wi_preflight.sh`.
3. Try to name the current Foundation pack and the current Architecture Baseline, including a revision that can be checked, using only those files.

The Foundation pack and the Architecture Baseline cannot be resolved from the repository. `scripts/wi_preflight.sh --check` does not look for them.

## Suspected Code Paths

- `docs/reconciliation.md` — names requirements, GitHub, the handoff, and Linear, and does not identify the Foundation pack or the Architecture Baseline.
- `.cursor/agents/reviewer.md` — tells the reviewer to compare against the Architecture Baseline and does not say where it is.
- `scripts/wi_preflight.sh` — checks the Git requirements file and the repository identity, and does not load an authority graph.
- `.specify/workflows/change-lifecycle/workflow.yml` — sequences Architecture section F and does not point at an external authority record.
- `specs/001-requirements-baseline/spec.md` — cites Foundation Baseline v0.1.0 as governance input. After capture, this Git file is the engineering requirements authority.

## Root Cause Hypothesis

External authorities were left as prose citations after the requirements capture. No repository file records their stable identifiers, revision pins, normative status, or the result when a read cannot be completed. Confidence: high. This is a missing control for already approved resume and single-authority behavior, not a new product requirement.

## Proposed Remediation

**Preferred**: Extend the existing reconciliation record with one machine-readable graph at `docs/authority-graph.json`. Preflight loads that graph. Reviewer, verifier, and the workflow resolve authorities through it. Pin external revisions with the Drive identifier, document version, size, and modified time. Do not copy the Foundation pack or the Architecture Baseline into Git. Do not pin this graph's own Git blob, and do not pin the moving `main` SHA.

**Files likely to change**:

- `docs/authority-graph.json`
- `docs/reconciliation.md`
- `PROJECT_STATE.md`
- `scripts/wi_authority_check.py`
- `scripts/wi_authority_check.sh`
- `scripts/wi_preflight.sh`
- `.cursor/agents/reviewer.md`
- `.cursor/agents/verifier.md`
- `.specify/workflows/change-lifecycle/workflow.yml`
- `.github/workflows/change-control.yml`

**Tests to add or update**:

- `scripts/wi_authority_check.py --self-test` covers reconstruction, a missing binding, a wrong external identifier, an unavailable source, and a stale revision.

## Risks & Considerations

- Offline preflight must stay able to pass when Drive cannot be read. That case is `NOT_VERIFIED`, not a fabricated match.
- A pinned external metadata change must stop for reconciliation instead of being accepted quietly.
- `WI-CHG-0008` stays unused.
- Pull request 19 stays untouched.

## Open Questions

- None. The Foundation pack folder and the Architecture Baseline file were read from Drive during this assessment. Their identifiers belong in the graph, not in this open-question list as unresolved blockers.
