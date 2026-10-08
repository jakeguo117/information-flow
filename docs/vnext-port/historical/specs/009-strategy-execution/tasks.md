<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Tasks: Bidirectional Strategy ↔ Execution

**Input**: Design documents from `/specs/009-strategy-execution/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the authoritative acceptance specification. Native webhook and GPT cases stay `NOT_VERIFIED` until a proved included-cost dispatch exists.

**Organization**: The spec uses WI-REQ and AC identifiers rather than ranked user stories. Tasks are grouped by those requirements.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Requirement group

## Phase 1: Event guard

- [x] T001 [US1] Add `scripts/wi_event_check.py` and `scripts/wi_event_check.sh` for the contract in `specs/009-strategy-execution/contracts/strategy-event.md`
- [x] T002 [US1] Cover forged payload, replay, superseded decision, unknown decision, closed change, conflict, cross-project, and one-effect concurrency in `scripts/wi_strategy_acceptance.sh`

## Phase 2: Planning boundary

- [x] T003 [US2] Record the verified baseline and `PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE` in `specs/009-strategy-execution/plan.md`
- [x] T004 [US2] Add `scripts/wi_plan_boundary.sh` and the missing-baseline negative in `scripts/wi_strategy_acceptance.sh`

## Phase 3: Escalation and resolution

- [x] T005 [US3] Add `scripts/wi_escalation_record.sh` for the nine material categories, with the cost stop kept distinct, without editing `spec.md`
- [x] T006 [US3] Add `scripts/wi_resolution_check.sh` and forged, defer, and valid-approve cases in `scripts/wi_strategy_acceptance.sh`

## Phase 4: Execution entry

- [x] T007 [US4] Put the execution brief and planning result on `specs/009-strategy-execution/handoff.md` and point `PROJECT_STATE.md` at implementation without moving v0.3.0
- [x] T008 [US4] Run `scripts/wi_strategy_acceptance.sh` from `.github/workflows/change-control.yml`

## Consolidated repair

- [x] T010 [US6] Align the event contract, data model, and `scripts/wi_event_check.py` on canonical effect identity, predecessor no-op after a content change, durable pending/ack, and stop admission
- [x] T011 [US6] Align escalation question identity, multiple unresolved blockers, and terminal reject/defer/cancel in the escalation and resolution guards
- [ ] T009 [US5] Bind a Cursor Automation webhook and a GPT Strategy consumer only after the included cloud allowance and the consumer endpoint are proved. Do not substitute Computer Use. Native AC-03, AC-08, AC-10, AC-11, AC-13, AC-14, and AC-15 stay `NOT_VERIFIED`

## Dependencies

T001 → T002. T003 → T004. T005 → T006. T007 and T008 follow the guards. T010 and T011 follow the approved Decision A and Decision B records. T009 is blocked on cost and consumer proof.
