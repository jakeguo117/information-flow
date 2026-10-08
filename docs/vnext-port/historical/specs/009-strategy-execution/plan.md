<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Implementation Plan: Bidirectional Strategy ↔ Execution

**Branch**: `wi-chg-0009-strategy-execution` | **Date**: 2026-10-01 | **Spec**: `specs/009-strategy-execution/spec.md`

**Input**: Feature specification from `/specs/009-strategy-execution/spec.md`

## Summary

WI-CHG-0009 keeps Cursor as the only repository operator. Durable Git records stay authoritative. A normalized webhook/API event may only name those records and wake a consumer. This plan reuses the existing `scripts/wi_*.sh` lifecycle and adds a thin event admit, an escalation record, and a resolution check. It does not add a service, a bus, or a second spec.

Cursor Automations document a private webhook that starts a cloud agent, and those runs are billed as cloud-agent usage. This account's remaining included allowance is not proved, and the fetched automation docs do not provide a GPT Work event consumer. Native dispatch stays blocked. Computer Use is not the production path.

## Technical Context

**Language/Version**: Bash and Python 3, matching `scripts/wi_*.sh` and `scripts/wi_bootstrap.py`

**Primary Dependencies**: existing Spec Kit 1.0.13 lifecycle, `scripts/wi_admit.sh`, `scripts/wi_preflight.sh`, `scripts/wi_material_stop.sh`, `scripts/wi_ownership_check.sh`, `scripts/wi_merge_gate.sh`

**Storage**: project Git records. Effects and escalations live in the change directory. No new database.

**Testing**: `scripts/wi_strategy_acceptance.sh` plus the existing `scripts/wi_bootstrap_acceptance.sh`

**Target Platform**: local repository checks and GitHub Actions `change-control.yml`. Cursor Automation webhook is the approved later consumer, not a host built here.

**Project Type**: repository lifecycle scripts

**Performance Goals**: event admit is a local file check. No throughput target.

**Constraints**: no plan upgrade, add-on, new recurring service, GPT GitHub writes, Computer Use primary path, or second orchestrator. Unknown included-usage allowance blocks native dispatch.

**Scale/Scope**: one active change, `WI-CHG-0009`, on the existing branch

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Result |
| --- | --- |
| I. Flow-forward | Pass under the WI-CHG-0009-DEC-0002 amendment. Same-change resolution stays in `specs/009-strategy-execution`. A new product outcome still opens a new change. `specs/008-project-bootstrap` is not rewritten. |
| II. Sole GitHub operator | Pass. GPT is not given commit, branch, PR, or merge authority. |
| III. NOT_VERIFIED | Pass. Webhook account binding, included allowance, and a GPT event consumer stay `NOT_VERIFIED`. |
| IV. No second orchestrator | Pass. No hosted coordinator, webhook bus, or second current spec. The native Cursor webhook remains a later consumer of Git state. |

Post-design re-check: the same four gates pass. Contracts describe the event; they do not deploy a listener.

## Verified Baseline

Observed 2026-10-01 from `git fetch` and `git ls-remote`, not from the prompting message.

| Fact | Observed value |
| --- | --- |
| Repository | `jakeguo117/workspace-infrastructure-vnext`, private, default branch `main` |
| `origin/main` | `7168117db85befa4e9f36420d306c667ffc12cbf` |
| Change branch | `wi-chg-0009-strategy-execution` at audited head `a746078e0c18379c19c81803f6e73a32937a6f6b` before this consolidated repair |
| Ahead / behind | That audited head was 9 commits ahead of `origin/main`, 0 behind |
| Approved content | `7ca26b5d6481872dc122f91f2fe45acb39131a01` |
| Spec SHA-256 | `f9452dc0dfc4c093cb151acfe42a3709718b7b6bc50fb56c50fba8de68204512` |
| Current Approved Truth | v0.3.0, `specs/008-project-bootstrap/spec.md` at `b9e339f65a718a00121842e531632c5c2e34e904` |
| Protocol | v0.3.0, `e75af65951711202a6f973d5f7e89239a4b3b2ff` |
| Ownership | `ownership: ok active=0` |
| Other writers | Open PR 19 is the unrelated README draft. No second `WI-CHG-0009` branch. |
| Reuse | `scripts/wi_admit.sh`, `scripts/wi_preflight.sh`, `scripts/wi_material_stop.sh`, `scripts/wi_ownership_check.sh`, `scripts/wi_approval_check.sh`, and `scripts/wi_merge_gate.sh` already implement admission, dirty-tree preflight, material stop, ownership, approval, and exact-head merge. The new guard is `scripts/wi_event_check.sh`. |

## Project Structure

### Documentation (this feature)

```text
specs/009-strategy-execution/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/strategy-event.md
├── tasks.md
├── spec.md
├── approval.md
├── change.md
└── handoff.md
```

### Source Code (repository root)

```text
scripts/
├── wi_event_check.sh
├── wi_plan_boundary.sh
├── wi_escalation_record.sh
├── wi_resolution_check.sh
└── wi_strategy_acceptance.sh
.github/workflows/change-control.yml
```

**Structure Decision**: Extend the existing `scripts/` lifecycle. Do not add `src/`, a service, or a database.

## Boundary validation

`scripts/wi_plan_boundary.sh` is a deterministic fail-fast string check. It does not prove architecture, security, or cost compliance.

| Requirement | Class |
| --- | --- |
| WI-REQ-035 execution brief | Designed. The handoff carries the brief fields. Native dispatch is not verified. |
| WI-REQ-036 planning boundary | Implemented deterministic fail-fast guard. Not full semantic validation. |
| WI-REQ-037 escalation | Implemented deterministic guard for question identity and immutable history. Native GPT wake-up is not verified. |
| WI-REQ-038 resolution | Implemented deterministic guard for ancestry, multiple blockers, and terminal reject/defer/cancel. Native resume is not verified. |
| WI-REQ-039 correlation | Implemented deterministic canonical effect identity, pending, and ack. Native idempotency is not verified. |

Acceptance cases that need a live Cursor webhook or a live GPT Work run stay `NOT_VERIFIED`. Included cloud allowance is unknown and blocks native dispatch. It does not authorize a different architecture. Decision A and Decision B are recorded, so this fail-fast check may return CONTINUE. That is not merge authority.

PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE

## Complexity Tracking

No constitution violation requires justification.
