<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

Change ID / title: WI-CHG-0007 Operational acceptance fixture
Status: Superseded by specs/007-acceptance-b/change.md
Owner / decision owner: SPEC_OWNER drafted; Jake approved this acceptance run
Base Current Approved Truth: specs/001-requirements-baseline/spec.md at main 3c35008526bbdefa1ba84016f179867ad950feec; project baseline v0.2.0; pinned implementation baseline f9e720953521b5ba93046242932080112b73f7d7
WHY: Phase 1 has to be exercised as an operational lifecycle, including a later synthetic A to B transition, without changing production requirements.
ADDED: An acceptance fixture whose current sentence is behavior A, plus the records this lifecycle needs.
MODIFIED: none
REMOVED: none
Impact: docs/acceptance/fixture.md and this change directory. No WI-REQ text change. No architecture change. No paid plan. No Batch 7.
Alternatives material to the decision: Opening Batch 7 was rejected. This run is an acceptance fixture only.
Open questions / risks: none
Jake decision: Operational acceptance instruction approved WI-CHG-0007 on 2026-09-30, including the later synthetic fixture transition from behavior A to behavior B. Evidence is that instruction. It does not approve a production semantic change or Batch 7.
Next lifecycle state / owner: Implement / IMPLEMENTER

Lifecycle history:
- Draft: SPEC_OWNER recorded the problem and the candidate fixture sentence. No implementation was in the draft.
- Jake gate before Approved: approve. Reject was not chosen. The decision and the delta above are the gate evidence.
