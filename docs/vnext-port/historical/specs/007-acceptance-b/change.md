<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

Change ID / title: WI-CHG-0007 Operational acceptance fixture behavior B
Status: Approved
Owner / decision owner: SPEC_OWNER recorded the delta; Jake pre-approved this synthetic transition
Base Current Approved Truth: behavior A in specs/006-acceptance-a/spec.md, pinned implementation baseline f9e720953521b5ba93046242932080112b73f7d7, project baseline v0.2.0
WHY: The acceptance run requires a controlled A to B transition after implementation against A exists. Affected implementation against A stops here.
ADDED: none
MODIFIED: the current fixture sentence changes from behavior A to behavior B, and the fixture must also contain ACCEPTANCE_EVIDENCE: present. docs/acceptance/bug-fixture.txt must contain bug-fixture: approved behavior.
REMOVED: none
Impact: docs/acceptance/fixture.md and docs/acceptance/bug-fixture.txt. specs/006-acceptance-a remains as history. No WI-REQ text change. No architecture change. No Batch 7.
Alternatives material to the decision: Continuing to implement A after the transition was rejected.
Open questions / risks: none
Jake decision: The operational acceptance instruction pre-authorized this synthetic A to B fixture transition on 2026-09-30. Evidence is that instruction, section 6. It does not approve a production requirement change.
Approved content: f6b41350c070713f9c4edb93f39bb44a0c113f3c
Next lifecycle state / owner: Implement / IMPLEMENTER
