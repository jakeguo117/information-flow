<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Contract: normalized Strategy event

A normal event is a reference and wake-up envelope. It identifies durable authority. It does not prove Jake approval, current project state, lifecycle admission, implementation authority, or merge authority.

## Persistence before dispatch

1. Jake authors the decision content. That content is not an authenticated native approval receipt.
2. Cursor persists the durable decision record and reads it back.
3. Only then does `strategy_approved` or `strategy_resolved` name that durable authority reference.
4. `capture_request` may name the approved base that already exists (`expected_remote_sha`) or the current approved content. It must not be required to name a Git commit the capture has not created.

## Request

JSON object. Allowed keys:

| Key | Rule |
| --- | --- |
| `schema_version` | integer `1` |
| `event_kind` | `capture_request`, `strategy_approved`, `material_escalation`, or `strategy_resolved` |
| `repository` | must equal the handoff repository |
| `project_id` | must equal the handoff project |
| `change_id` | must equal the handoff change |
| `decision_id` | current handoff decision, or a named predecessor for a no-op |
| `escalation_id` | string or empty. Included in the effect identity when non-empty |
| `authority_ref` | 40 hexadecimal characters. For the current decision, `strategy_approved`, `material_escalation`, and `strategy_resolved` must equal `approved_content`. `capture_request` may equal `approved_content` or `expected_remote_sha` |
| `record_path` | must equal the handoff record path. A URL or another path rejects |
| `idempotency_key` | caller delivery token. It is not the effect identity |

## Effect identity

The system derives the canonical effect identity as the SHA-256 of:

`repository`, `project_id`, `change_id`, `authority_ref`, `decision_id`, `event_kind`, and `escalation_id` when that field is non-empty.

A second delivery of that tuple with a different caller `idempotency_key` acknowledges the existing effect and does not append another. A different operation or decision is a different effect.

## Reject

| Condition | Result |
| --- | --- |
| Extra key, prose, or forged approval field | `event: reject reason=payload-authority` |
| Repository, project, or change mismatch | `event: reject reason=repository` |
| `record_path` or, for a current non-capture event, `authority_ref` does not match the handoff | `event: reject reason=authority` |
| Workflow state is Closed, Converged, or New Baseline | `event: reject reason=closed` |
| Decision not current and not a named predecessor | `event: reject reason=unknown-decision` |
| Handoff names a conflicting successor | `event: reject reason=conflict` |
| Durable next action is `STOP — JAKE DECISION REQUIRED` or `STOP — JAKE COST APPROVAL REQUIRED` | `event: reject reason=stop` |

Predecessor evaluation happens before the current-content comparison. A named predecessor is `event: noop reason=superseded` even when Decision B has changed `approved_content`. It does not append an effect.

## Effects

The effects file is durable change state, separate from workflow state. The production path is `specs/009-strategy-execution/effects.log`. Tests may pass another file path. The record is not only a temporary fixture.

| State | Meaning |
| --- | --- |
| `pending` | The effect was recorded before acknowledgement |
| `acknowledged` | A redelivery found the pending or completed effect and did not apply it again |

The first delivery appends `pending` and prints `event: admit`. A redelivery of that canonical identity prints `event: ack` and does not append. A redelivery that finds `pending` updates that line to `acknowledged`.

The event does not create a branch, edit a file other than the effects log, or satisfy `scripts/wi_admit.sh` by itself.
