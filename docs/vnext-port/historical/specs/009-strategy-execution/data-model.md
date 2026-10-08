<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Data model: WI-CHG-0009

Records stay in the change directory. No new store. No central workflow database.

## Execution brief

Lives in `handoff.md` under `execution_brief`. Fields: `project_id`, repository, target branch, protocol pin, `change_id`, approved base, approved content, `decision_id`, predecessor decision, actor, constraints, non-goals, permitted actions, cost authority, and the one next action. It points at the spec; it does not copy requirement prose.

The one next action is the legal entry. It cannot be `PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE` while that next action is `STOP — JAKE DECISION REQUIRED`.

## Normalized event

Allowlisted fields only: `schema_version`, `event_kind`, `repository`, `project_id`, `change_id`, `decision_id`, `escalation_id`, `authority_ref`, `record_path`, `idempotency_key`.

`event_kind` is `capture_request`, `strategy_approved`, `material_escalation`, or `strategy_resolved`. Any other field is payload authority and is rejected.

`authority_ref` is a 40-character reference to durable state that already exists. It is not approval content and it is not a commit the caller hopes will be created by this event.

The caller `idempotency_key` is delivery metadata. The canonical effect identity is the hash of repository, project, change, authority reference, decision, operation, and escalation when present.

## Effect

Durable lines in `specs/009-strategy-execution/effects.log`, or in the path passed to the guard:

`pending <canonical-key> <kind> <decision-id> <caller-key>`

`acknowledged <canonical-key> <kind> <decision-id> <caller-key>`

`pending` is written before the admit result returns. A crash after that write and before ack is recovered by redelivery: the same canonical identity becomes `acknowledged` and is not applied twice. The effects file is not a substitute for workflow state.

## Escalation

Immutable appended records. Required fields match WI-REQ-037. `question` is the material question. `problem` is only the category. The same unresolved category plus the same question reuses the existing escalation id. A different question appends a new id. Two open questions of one category stay distinct.

Cost uses `STOP — JAKE COST APPROVAL REQUIRED`. Every other material category uses `STOP — JAKE DECISION REQUIRED`. The approved spec file is not modified.

More than one escalation may be unresolved. An approved escalation is no longer unresolved. Only a different escalation that is still unresolved may block resume. Reject, defer, and cancel are terminal for that escalation and are not unresolved.

## Resolution

Immutable Decision B. Fields: new `decision_id`, predecessor decision, escalation id, `resolution` (`approve`, `reject`, `defer`, or `cancel`), actor, content SHA-256, and evidence.

`actor: Jake` plus a non-empty evidence string is a syntactic shape check. It is not an authenticated native approval receipt. That receipt stays `NOT_VERIFIED`.

Only `approve` can admit resume, and only when no other escalation is still unresolved. Reject, defer, and cancel append a terminal resolution event. A later approve of that same escalation rejects. Decision A, the escalation, and Decision B remain recoverable.

## State

Current Approved Truth stays v0.3.0 until convergence. The handoff names one current decision and one next action. A competing successor stops. Closed, Converged, and New Baseline changes do not restart.

## Evidence envelope

A review or verification record names the implementation/content commit it assessed. A Git commit cannot contain its own SHA, so the current record is stored in a descendant evidence envelope. The named commit stays the assessed head.

The envelope is current only when every changed path is `PROJECT_STATE.md` or `specs/<one-segment>/review.md`, `verification.md`, `handoff.md`, or `closure-report.md`. A nested path is not an envelope. Rename detection must not hide a source path: a renamed spec or script makes the record historical. The route then prints `content_pass` or `content_verified` only for a real envelope. Those tokens mean the named content remains reviewed or verified. They do not authorize merge.

`scripts/wi_merge_gate.sh` still refuses a merge unless the evaluated head is the named content commit. `scripts/wi_durable_proof.sh` rejects an envelope with `reason=not-merge-head`. That rejection does not mean the content review is missing and does not start another review of the same content. Recording the envelope does not create a new implementation head.
