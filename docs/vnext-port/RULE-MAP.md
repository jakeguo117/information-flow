# VNext rule map

Sources: main `7168117db85befa4e9f36420d306c667ffc12cbf` and `wi-chg-0009-strategy-execution` `c99355daf4889148dc517704bb6423de221d0770`.
Approved documents win: AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, AIC-APR-0001.

## Counts

- Total rule rows: 175
- MIGRATED: 79
- ALREADY_COVERED: 7
- NOT_MIGRATED: 89
- Rows that record a conflict: 65


Conflict rows are also counted in migrated or not-migrated, depending on whether any non-conflicting remainder was ported. The conflict list itself is `docs/vnext-port/CONFLICTS.md`.

| ID | VNext source | Landing in information-flow | Class |
| --- | --- | --- | --- |
| WI-REQ-001 | specs/008-project-bootstrap/spec.md § WI-REQ-001 (successor of specs/001-requirements-baseline/spec.md) | specs/vnext/requirements.md § WI-REQ-001. Business truth remains AIC-DOC-REQ@0.1.1 (REQ-003, APR-0001). | MIGRATED |
| WI-REQ-002 | specs/008-project-bootstrap/spec.md § WI-REQ-002 | specs/vnext/requirements.md § WI-REQ-002. Aligns with WORKFLOW 6.2.3: a branch is not approval. | MIGRATED |
| WI-REQ-003 | specs/008-project-bootstrap/spec.md § WI-REQ-003 | specs/vnext/requirements.md § WI-REQ-003. Aligns with WORKFLOW change-delta language and HANDOFF change history. | MIGRATED |
| WI-REQ-004 | specs/008-project-bootstrap/spec.md § WI-REQ-004 | specs/vnext/requirements.md § WI-REQ-004. Aligns with WORKFLOW 6.2.8 new-version row. | MIGRATED |
| WI-REQ-005 | specs/008-project-bootstrap/spec.md § WI-REQ-005 | specs/vnext/requirements.md § WI-REQ-005 adapted. Exact SHA rule kept. VNext baseline SHA not adopted. See C-BASELINE. | MIGRATED |
| WI-REQ-006 | specs/008-project-bootstrap/spec.md § WI-REQ-006 | specs/vnext/requirements.md § WI-REQ-006. Aligns with WORKFLOW 6.2.7 evidence fields. | MIGRATED |
| WI-REQ-007 | specs/008-project-bootstrap/spec.md § WI-REQ-007 | specs/vnext/requirements.md § WI-REQ-007. | MIGRATED |
| WI-REQ-008 | specs/008-project-bootstrap/spec.md § WI-REQ-008 | specs/vnext/requirements.md § WI-REQ-008. Already required by REQ-011 and WORKFLOW 6.2.8 draft/review rows; engineering capture is still ported. | MIGRATED |
| WI-REQ-009 | specs/008-project-bootstrap/spec.md § WI-REQ-009 | specs/vnext/requirements.md § WI-REQ-009 and docs/vnext-port/workflows/change-lifecycle.yml, merge step withheld. | MIGRATED |
| WI-REQ-010 | specs/008-project-bootstrap/spec.md § WI-REQ-010 | specs/vnext/requirements.md § WI-REQ-010. Aligns with WORKFLOW repair-versus-new-approval split. | MIGRATED |
| WI-REQ-011 | specs/008-project-bootstrap/spec.md § WI-REQ-011 | specs/vnext/requirements.md § WI-REQ-011. Aligns with REQ-008 and WORKFLOW 6.2.8. | MIGRATED |
| WI-REQ-012 | specs/008-project-bootstrap/spec.md § WI-REQ-012 | specs/vnext/requirements.md § WI-REQ-012. Business roles remain WORKFLOW “Roles and modules”. These are engineering executor roles. | MIGRATED |
| WI-REQ-013 | specs/008-project-bootstrap/spec.md § WI-REQ-013 | specs/vnext/requirements.md § WI-REQ-013 and scripts/vnext/wi_ownership_check.sh. Aligns with WORKFLOW one write owner and HANDOFF event writes. | MIGRATED |
| WI-REQ-014 | specs/008-project-bootstrap/spec.md § WI-REQ-014 | specs/vnext/requirements.md § WI-REQ-014 and templates under docs/vnext-port/historical/templates/. Resume entry is the settled GPT name/link plus Grok, not a new caller. See docs/vnext-port/continue-project.md. | MIGRATED |
| WI-REQ-015 | specs/008-project-bootstrap/spec.md § WI-REQ-015; narrowed again in specs/009-strategy-execution/spec.md delta table | NOT_MIGRATED. Standing branch/commit/push/PR/merge. CONFLICTS C-015. In-boundary non-Git engineering detail is ALREADY_COVERED by WORKFLOW 6.2.1 and 6.2.6. | NOT_MIGRATED |
| WI-REQ-015-covered | same section, the non-Git half: routine in-boundary engineering does not re-ask Jake for every keystroke | ALREADY_COVERED by WORKFLOW 6.2.1 (three human decisions) and 6.2.6 (in-scope engineering detail). | ALREADY_COVERED |
| WI-REQ-016 | specs/008-project-bootstrap/spec.md § WI-REQ-016 | specs/vnext/requirements.md § WI-REQ-016. Aligns with WORKFLOW escalation back to Jake and APR stop boundaries. | MIGRATED |
| WI-REQ-017 | specs/008-project-bootstrap/spec.md § WI-REQ-017; .specify/memory/constitution.md principle II on main and on c99355d | NOT_MIGRATED exclusive read/write grant. CONFLICTS C-017. Scoped Cursor engineering ownership is ALREADY_COVERED by WORKFLOW 6.2.6. | NOT_MIGRATED |
| WI-REQ-018 | specs/008-project-bootstrap/spec.md § WI-REQ-018 | specs/vnext/requirements.md § WI-REQ-018 adapted. Remote Git truth kept. Cursor-only read monopoly withheld. CONFLICTS C-018. | MIGRATED |
| WI-REQ-019 | specs/008-project-bootstrap/spec.md § WI-REQ-019; docs/linear-projection.md | NOT_MIGRATED as Linear binding. CONFLICTS C-019. Notion projection is ALREADY_COVERED by REQ-003, WORKFLOW State/evidence/projection, APR-0001. Six fields ported in docs/vnext-port/projection.md. | NOT_MIGRATED |
| WI-REQ-020 | specs/008-project-bootstrap/spec.md § WI-REQ-020; docs/reconciliation.md | specs/vnext/requirements.md § WI-REQ-020 and docs/vnext-port/reconciliation.md adapted. CONFLICTS C-020 for “Drive is only a projection”. | MIGRATED |
| WI-REQ-021 | specs/008-project-bootstrap/spec.md § WI-REQ-021 | specs/vnext/requirements.md § WI-REQ-021 and scripts/vnext/wi_retry_budget.sh, wi_pr_lookup.sh. Aligns with REQ-008 and WORKFLOW retry paragraph. | MIGRATED |
| WI-REQ-022 | specs/008-project-bootstrap/spec.md § WI-REQ-022 | specs/vnext/requirements.md § WI-REQ-022 and docs/vnext-port/projection.md. | MIGRATED |
| WI-REQ-023 | specs/008-project-bootstrap/spec.md § WI-REQ-023 | specs/vnext/requirements.md § WI-REQ-023. Paid and destructive limits also ALREADY_COVERED by APR-0001 excluded actions and REQ-007; the GitHub-plan purchase limit is the ported engineering detail. | MIGRATED |
| WI-REQ-024 | specs/008-project-bootstrap/spec.md § WI-REQ-024 | specs/vnext/requirements.md § WI-REQ-024 and scripts/vnext/wi_secret_check.sh. | MIGRATED |
| WI-REQ-025 | specs/008-project-bootstrap/spec.md § WI-REQ-025 | specs/vnext/requirements.md § WI-REQ-025 and scripts/vnext/wi_merge_gate.sh as a refusal check, not a merge right. Aligns with WORKFLOW 6.2.8 version-mismatch row. | MIGRATED |
| WI-REQ-026 | specs/008-project-bootstrap/spec.md § WI-REQ-026 | specs/vnext/requirements.md § WI-REQ-026 adapted to information-flow. CONFLICTS C-026. | MIGRATED |
| WI-REQ-027 | specs/008-project-bootstrap/spec.md § WI-REQ-027 | specs/vnext/requirements.md § WI-REQ-027 adapted to AIC-CHG ids. | MIGRATED |
| WI-REQ-028 | specs/008-project-bootstrap/spec.md § WI-REQ-028 | specs/vnext/requirements.md § WI-REQ-028 and specs/vnext/constitution.md § III. Same rule as REQ and WORKFLOW NOT_VERIFIED wording. | MIGRATED |
| WI-REQ-029 | specs/008-project-bootstrap/spec.md § WI-REQ-029 | specs/vnext/requirements.md § WI-REQ-029. Aligns with WORKFLOW: implementer self-report is not verification; Jake acceptance is separate. | MIGRATED |
| WI-REQ-030 | specs/008-project-bootstrap/spec.md § WI-REQ-030 | specs/vnext/requirements.md § WI-REQ-030. Single authority per fact is ALREADY_COVERED by REQ-003; the engineering wording is ported so projections are not a second spec. | MIGRATED |
| WI-REQ-031 | specs/008-project-bootstrap/spec.md § WI-REQ-031 | NOT_MIGRATED. VNext protocol enrollment and PROJECT_STATE pin. CONFLICTS C-031. Would import a baseline and a second project identity. | NOT_MIGRATED |
| WI-REQ-032 | specs/008-project-bootstrap/spec.md § WI-REQ-032 | NOT_MIGRATED as a bootstrap writer. CONFLICTS C-032. Reconstruction is ALREADY_COVERED by WORKFLOW 6.2.5–6.2.6 and mapped to scripts/continue_project.py without a new caller. | NOT_MIGRATED |
| WI-REQ-033 | specs/008-project-bootstrap/spec.md § WI-REQ-033; specs/009 delta | specs/vnext/requirements.md § WI-REQ-033. Aligns with WORKFLOW 6.2.3 and 6.2.6: approval and brief before implementation; a trigger is not admission. | MIGRATED |
| WI-REQ-034 | specs/008-project-bootstrap/spec.md § WI-REQ-034; specs/009 delta | specs/vnext/requirements.md § WI-REQ-034 adapted. Merge grant withheld (C-015). Bookkeeping-is-not-authority is ported. | MIGRATED |
| WI-REQ-035 | specs/009-strategy-execution/spec.md § WI-REQ-035 | specs/vnext/requirements.md § WI-REQ-035. Readable brief fields only. No continue_project caller. See docs/vnext-port/continue-project.md. | MIGRATED |
| WI-REQ-036 | specs/009-strategy-execution/spec.md § WI-REQ-036 | specs/vnext/requirements.md § WI-REQ-036. Aligns with WORKFLOW 6.2.6 steps 1–4, including Verified Baseline. PLAN_ACCEPTED_WITHIN_BOUNDARY is not merge proof. | MIGRATED |
| WI-REQ-037 | specs/009-strategy-execution/spec.md § WI-REQ-037 | specs/vnext/requirements.md § WI-REQ-037 adapted. Durable stop record kept. Webhook wake-up NOT a caller. CONFLICTS C-037. | MIGRATED |
| WI-REQ-038 | specs/009-strategy-execution/spec.md § WI-REQ-038 | specs/vnext/requirements.md § WI-REQ-038 adapted. Ancestry and terminal reject/defer/cancel kept. Automatic resume transport not imported. CONFLICTS C-037. | MIGRATED |
| WI-REQ-039 | specs/009-strategy-execution/spec.md § WI-REQ-039; scripts/wi_event_check.py | specs/vnext/requirements.md § WI-REQ-039 and scripts/vnext/wi_event_check.py. Idempotency aligns with WORKFLOW retry. The script does not start an agent. | MIGRATED |
| CONST-I | .specify/memory/constitution.md principle I on main 7168117 | specs/vnext/constitution.md § I. | MIGRATED |
| CONST-I-009 | .specify/memory/constitution.md principle I amendment at c99355d (“WI-CHG-0009 Decision B”) | NOT_MIGRATED. 009 constitution amendment and 009 state. Ancestry without adopting 009 status is WI-REQ-038. | NOT_MIGRATED |
| CONST-II | .specify/memory/constitution.md principle II, both SHAs | NOT_MIGRATED. CONFLICTS C-017. Standing GitHub operator. | NOT_MIGRATED |
| CONST-III | .specify/memory/constitution.md principle III | specs/vnext/constitution.md § III. | MIGRATED |
| CONST-IV | .specify/memory/constitution.md principle IV | specs/vnext/constitution.md § IV. Spec Kit is not a second business workflow. CONFLICTS C-ENGINE records the boundary. | MIGRATED |
| LIFE-STATES | .specify/workflows/change-lifecycle/workflow.yml states draft through converge, except the merge step | docs/vnext-port/workflows/change-lifecycle.yml | MIGRATED |
| LIFE-MERGE | .specify/workflows/change-lifecycle/workflow.yml step id merge; scripts/wi_merge_if_head.sh does not itself merge | NOT_MIGRATED as permission. CONFLICTS C-015. wi_merge_if_head.sh is ported only as a raced-head refusal. | NOT_MIGRATED |
| GATE-EXACT-HEAD | scripts/wi_merge_gate.sh; scripts/wi_review_route.sh; scripts/wi_durable_proof.sh | scripts/vnext/ copies. They refuse or route. They do not merge and their exit is not an AIC acceptance PASS. | MIGRATED |
| SCRIPT-PREFLIGHT | scripts/wi_preflight.sh | scripts/vnext/wi_preflight.sh. Fail-closed when PROJECT_STATE.md is absent. The baseline file is not imported. | MIGRATED |
| SCRIPT-AUTHORITY | scripts/wi_authority_check.py | scripts/vnext/wi_authority_check.py. The VNext authority-graph.json is not imported, so this checker has no current AIC graph to bless. | MIGRATED |
| SCRIPT-ADMIT | scripts/wi_admit.sh | scripts/vnext/wi_admit.sh. Chat is not approval. Aligns with WORKFLOW 6.2.3 and WI-REQ-008. | MIGRATED |
| SCRIPT-APPROVAL | scripts/wi_approval_check.sh | scripts/vnext/wi_approval_check.sh. | MIGRATED |
| SCRIPT-ANCESTRY | scripts/wi_ancestry_check.sh | scripts/vnext/wi_ancestry_check.sh. Implements WI-REQ-004. | MIGRATED |
| SCRIPT-BOOTSTRAP-DETECT | scripts/wi_bootstrap.py --detect; scripts/wi_bootstrap.sh | scripts/vnext/ copies. --apply returns 2 and does not write PROJECT_STATE. See C-032. | MIGRATED |
| SCRIPT-BOOTSTRAP-ACCEPT | scripts/wi_bootstrap_acceptance.sh | NOT_MIGRATED. Second acceptance project, v0.3.0 baseline check, acceptance runner. | NOT_MIGRATED |
| SCRIPT-STRATEGY-ACCEPT | scripts/wi_strategy_acceptance.sh | NOT_MIGRATED. 009 acceptance runner and event-caller surface. Not run. | NOT_MIGRATED |
| SCRIPT-EVENT | scripts/wi_event_check.py; scripts/wi_event_check.sh | scripts/vnext/. Admits or rejects one normalized event record. Does not start a cloud agent or invent a caller. | MIGRATED |
| SCRIPT-ESC-RES | scripts/wi_escalation_record.sh; scripts/wi_resolution_check.sh; scripts/wi_material_stop.sh | scripts/vnext/. Record shape only. Native approval receipt stays NOT_VERIFIED inside the resolution checker. | MIGRATED |
| SCRIPT-PLAN | scripts/wi_plan_boundary.sh | scripts/vnext/wi_plan_boundary.sh. CONTINUE is not architecture, security, cost, or merge proof. | MIGRATED |
| SCRIPT-PROJ | scripts/wi_projection_check.sh | scripts/vnext/wi_projection_check.sh. Headline-is-not-a-SHA and six labels. Linear is not the AIC projection. | MIGRATED |
| SCRIPT-SECRET | scripts/wi_secret_check.sh | scripts/vnext/wi_secret_check.sh. | MIGRATED |
| SCRIPT-OWN | scripts/wi_ownership_check.sh | scripts/vnext/wi_ownership_check.sh. | MIGRATED |
| SCRIPT-RETRY | scripts/wi_retry_budget.sh | scripts/vnext/wi_retry_budget.sh. | MIGRATED |
| SCRIPT-PR-LOOKUP | scripts/wi_pr_lookup.sh | scripts/vnext/wi_pr_lookup.sh. Reuse versus create. Does not open a pull request. Aligns with WI-REQ-021. | MIGRATED |
| SCRIPT-CONVERGE | scripts/wi_converge_check.sh | scripts/vnext/wi_converge_check.sh. speckit.converge does not record a baseline. | MIGRATED |
| SCRIPT-WORKFLOW-VAL | scripts/wi_workflow_validate.sh | scripts/vnext/wi_workflow_validate.sh. Validates a Spec Kit workflow file. Not installed as CI. | MIGRATED |
| SCRIPT-FIXTURE | scripts/wi_acceptance_fixture_check.sh; docs/acceptance/fixture.md; docs/acceptance/bug-fixture.txt | scripts/vnext/wi_acceptance_fixture_check.sh and docs/vnext-port/historical/docs/acceptance/. Historical behavior A/B ancestry. Not an AIC acceptance PASS. | MIGRATED |
| MARKER-E2E | docs/acceptance/native-e2e-marker.txt | NOT_MIGRATED. Would present a native end-to-end marker as if it were evidence in this repo. | NOT_MIGRATED |
| GRAPH-ENG | docs/authority-graph.json role engineering-requirements | NOT_MIGRATED as current pin to specs/008. Business requirements are AIC-DOC-REQ@0.1.1. CONFLICTS C-GRAPH. | NOT_MIGRATED |
| GRAPH-WORKFLOW | docs/authority-graph.json role workflow-lifecycle Drive folder 1Zf8f97TnX_KCdGd1S6iEVIxgjRCDutjg | NOT_MIGRATED. CONFLICTS C-GRAPH. Workflow authority is AIC-DOC-WORKFLOW@0.2.0. | NOT_MIGRATED |
| GRAPH-ARCH | docs/authority-graph.json role architecture Drive file 16XTL42-4Kkcq42TnLlcD-9USOaN9SP-E | NOT_MIGRATED. That VNext architecture pin is not one of the four approved AIC documents. Not adopted as AIC architecture authority. | NOT_MIGRATED |
| GRAPH-IMPL | docs/authority-graph.json role implementation locator workspace-infrastructure-vnext | NOT_MIGRATED. CONFLICTS C-026. Implementation repo is information-flow. | NOT_MIGRATED |
| GRAPH-PROJ | docs/authority-graph.json role projection Linear P-JAK-19 | NOT_MIGRATED. CONFLICTS C-019. | NOT_MIGRATED |
| GRAPH-READING | docs/authority-graph.json role requirements-reading-copy | NOT_MIGRATED as that Drive file pin. The reading-copy rule for an engineering spec is the adapted WI-REQ-020. | NOT_MIGRATED |
| TPL-CHANGE | templates/change.md and .specify/templates/overrides/change.md | docs/vnext-port/historical/templates/change.md and the override copy. Required delta fields. The template does not approve itself. | MIGRATED |
| TPL-HANDOFF | .specify/templates/overrides/handoff-template.md | docs/vnext-port/historical/.specify/templates/overrides/handoff-template.md. Grants no permission. Aligns with WI-REQ-014. | MIGRATED |
| TPL-REVIEW | .specify/templates/overrides/review-template.md; verification-template.md | docs/vnext-port/historical copies. A filled historical PASS in specs/004 and specs/005 is history, not an AIC acceptance result. | MIGRATED |
| TPL-SPEC-PLAN-TASKS | .specify/templates/spec-template.md, plan-template.md, tasks-template.md, checklist-template.md, constitution-template.md | docs/vnext-port/historical/.specify/templates/. | MIGRATED |
| AGENT-IMPL | .cursor/agents/implementer.md | docs/vnext-port/agents/implementer.md. Not a live agent. No merge. | MIGRATED |
| AGENT-REV | .cursor/agents/reviewer.md | docs/vnext-port/agents/reviewer.md. Review is not merge authority. PASS is not claimed for AIC. | MIGRATED |
| AGENT-VER | .cursor/agents/verifier.md | docs/vnext-port/agents/verifier.md. Does not run the withheld acceptance runners. | MIGRATED |
| SKILL-SPECKIT | .cursor/skills/speckit-*/SKILL.md (13 skills) | docs/vnext-port/cursor/skills/. Vendor lifecycle skills. Not installed under .cursor/skills. They do not replace WORKFLOW and do not grant standing Git rights. CONFLICTS C-ENGINE. | MIGRATED |
| SPECIFY-ENGINE | .specify/scripts/bash/*, extensions, integrations, workflow-registry, speckit workflow.yml | docs/vnext-port/historical/.specify/. Tooling for the ported engine. Not activated. | MIGRATED |
| BUG-EXT | .specify/extensions/bug/** and .specify/bugs/** | docs/vnext-port/historical/.specify/. Bug path is WI-REQ-010: repair against approved behavior, do not change the requirement in the fix. | MIGRATED |
| STATE-009 | PROJECT_STATE.md at c99355d; specs/009 status files listed in the inventory | NOT_MIGRATED. Baseline plus WI-CHG-0009 status, including DEC-0004, PR 25, and native-run prohibition as state. | NOT_MIGRATED |
| BASELINE-SHA | PROJECT_STATE.md Implementation Baseline b9e339f65a718a00121842e531632c5c2e34e904; Current Project Baseline v0.3.0; HANDOFF@0.2.0 exclusion | NOT_MIGRATED. CONFLICTS C-BASELINE. | NOT_MIGRATED |
| ENTRY-JOURNAL | information-flow skills/journal; VNext has no Journal writer | ALREADY_COVERED. Journal formal entry is GPT Cloud Work (owner decision 2026-10-08) and the existing journal skill. VNext excluded Information Flow; that exclusion is not imported (C-026). | ALREADY_COVERED |
| ENTRY-RESUME | WI-REQ-014, WI-REQ-032, WI-REQ-035, WI-REQ-037, WI-REQ-038 | Mapped in docs/vnext-port/continue-project.md. Settled entry: new GPT conversation, name or link only, Grok reads the same version. No caller added. scripts/continue_project.py unchanged. | MIGRATED |
| SOT-DRIVE-NOTION-GIT-OBSIDIAN | docs/authority-graph.json and docs/reconciliation.md versus REQ-003 | ALREADY_COVERED by REQ-003, WORKFLOW State/evidence/projection, and APR-0001. Conflicting VNext pins are C-GRAPH, C-019, C-020. | ALREADY_COVERED |
| HANDOFF-EXCLUDE-VNEXT | AIC-DOC-HANDOFF@0.2.0 “实施起点和验证边界” paragraph on c99355d | ALREADY_COVERED. That paragraph already excluded VNext baseline, 009 execution state, and Git standing permission. This port follows it and still migrates non-conflicting rules under the 2026-10-08 decision. | ALREADY_COVERED |
| 008-CASE-01 | specs/008-project-bootstrap/spec.md acceptance case 1, fresh GPT reconstruction. Same blob on main 7168117 and on c99355d. | NOT_MIGRATED as an executable case. Reconstruction from records is WORKFLOW 6.2.5. Settled resume is a new GPT conversation plus Grok, not this fixture. | NOT_MIGRATED |
| 008-CASE-02 | specs/008-project-bootstrap/spec.md acceptance case 2, fresh Cursor reconstruction | NOT_MIGRATED as an executable case. Repository grounding is WORKFLOW 6.2.6. | NOT_MIGRATED |
| 008-CASE-03 | specs/008-project-bootstrap/spec.md acceptance case 3, fresh Grok reconstruction | NOT_MIGRATED as an executable case. Grok reading the same approved version is WORKFLOW 6.2.7 and the 2026-10-08 resume entry. | NOT_MIGRATED |
| 008-CASE-04 | specs/008-project-bootstrap/spec.md acceptance case 4, detection and bootstrap enrollment | NOT_MIGRATED. VNext protocol enrollment and a second project. CONFLICTS C-031 and C-032. | NOT_MIGRATED |
| 008-CASE-05 | specs/008-project-bootstrap/spec.md acceptance case 5, approval before execution | NOT_MIGRATED as case text. The predicate is WI-REQ-008 and WI-REQ-033. | NOT_MIGRATED |
| 008-CASE-06 | specs/008-project-bootstrap/spec.md acceptance case 6, routine repair loop | NOT_MIGRATED as case text. Bounded repair is WI-REQ-010 and WI-REQ-034. The acceptance runner is withheld. | NOT_MIGRATED |
| 008-CASE-07 | specs/008-project-bootstrap/spec.md acceptance case 7, positive gate and conditional merge | NOT_MIGRATED. Standing merge. CONFLICTS C-015. | NOT_MIGRATED |
| 008-CASE-08 | specs/008-project-bootstrap/spec.md acceptance case 8, negative gate | NOT_MIGRATED as case text. Refusal of a bad head is WI-REQ-025. The runner is withheld. | NOT_MIGRATED |
| 008-CASE-09 | specs/008-project-bootstrap/spec.md acceptance case 9, stale evidence or head | NOT_MIGRATED as case text. Exact-head refusal is WI-REQ-025. | NOT_MIGRATED |
| 008-CASE-10 | specs/008-project-bootstrap/spec.md acceptance case 10, material issue | NOT_MIGRATED as case text. Material stop is WI-REQ-016 and WI-REQ-037. | NOT_MIGRATED |
| 008-CASE-11 | specs/008-project-bootstrap/spec.md acceptance case 11, retry exhaustion | NOT_MIGRATED as case text. Finite retry is WI-REQ-021. | NOT_MIGRATED |
| 008-CASE-12 | specs/008-project-bootstrap/spec.md acceptance case 12, reconstruction after accepted merge | NOT_MIGRATED. Treats merge plus convergence as baseline promotion. CONFLICTS C-015 and C-BASELINE. Reconstruction from approved records is WORKFLOW 6.2.5. | NOT_MIGRATED |
| 008-CASE-13 | specs/008-project-bootstrap/spec.md acceptance case 13, end-to-end conditional merge | NOT_MIGRATED. Standing merge and a native acceptance loop. CONFLICTS C-015. Not an AIC acceptance result. | NOT_MIGRATED |
| 008-CASE-EXTRA | specs/008-project-bootstrap/spec.md line 507, additional assertions (one writer, project isolation, secrets, projection) | NOT_MIGRATED as runner assertions. Predicates already in WI-REQ-013, WI-REQ-024, and WI-REQ-030. | NOT_MIGRATED |
| 008-DOD-COMPLETE | specs/008-project-bootstrap/spec.md Definition of Done, line 513 | NOT_MIGRATED. Requires isolated-repository bootstrap and a passing case 13. CONFLICTS C-031 and C-015. Not an AIC acceptance result. | NOT_MIGRATED |
| 008-DOD-MERGE-LINEAR | specs/008-project-bootstrap/spec.md Definition of Done, line 515 | NOT_MIGRATED. Conditional merge read-back and Linear projection. CONFLICTS C-015 and C-019. | NOT_MIGRATED |
| 008-DOD-UNPROVED | specs/008-project-bootstrap/spec.md Definition of Done, line 517 | specs/vnext/requirements.md § WI-REQ-028. Simulation is not proof, and NOT_VERIFIED stays blocking. | MIGRATED |
| 008-DOD-GROUNDING | specs/008-project-bootstrap/spec.md line 519, GROUNDING_CORRECTION naming origin/main 64c6acd4 and WI-CHG-0008 | NOT_MIGRATED. Historical VNext grounding and change status. Not the AIC baseline. | NOT_MIGRATED |
| 009-DEC-B-RULE | specs/009-strategy-execution/spec.md Decision B ancestry; constitution 0.1.1 | The ancestry rule is WI-REQ-038. The statement that WI-CHG-0009 is the active change, that PR 25 stays open, and that v0.3.0 stays current is NOT_MIGRATED 009 state. | MIGRATED |
| 009-TRANSPORT | specs/009-strategy-execution/spec.md line 147, “Keep webhook / API events as the primary production transport” | NOT_MIGRATED as a caller. CONFLICTS C-037. The four route rows below are the table. Product details for continue_project remain pending. | NOT_MIGRATED |
| 009-ARCH-ADAPTERS | specs/009-strategy-execution/spec.md § Necessary architecture, line 109 | NOT_MIGRATED. Keeps Spec Kit as the engine and names two native wake consumers. CONFLICTS C-ENGINE and C-037. “GPT does not control merge” is already APR-0001 Excluded actions. | NOT_MIGRATED |
| 009-ARCH-ENVELOPE | specs/009-strategy-execution/spec.md line 113, smallest durable approval envelope | specs/vnext/requirements.md § WI-REQ-035 and § WI-REQ-033. Origin capture cannot advance a gate. No second copy added. | MIGRATED |
| 009-ARCH-GIT-OWNER | specs/009-strategy-execution/spec.md line 115, “Cursor owns all branch, commit, push and PR operations” | NOT_MIGRATED. Standing Git permission. CONFLICTS C-015. APR-0001 Excluded actions list stage/commit/push/PR/CI/merge. HANDOFF@0.2.0 excludes Git standing permission. | NOT_MIGRATED |
| 009-ARCH-CAPTURE-WAKE | specs/009-strategy-execution/spec.md line 117, capture request may wake Cursor | NOT_MIGRATED webhook caller. CONFLICTS C-037. The predicate that a capture is not Plan/Tasks/Implement admission is already WI-REQ-033. | NOT_MIGRATED |
| 009-ARCH-PROJECTION | specs/009-strategy-execution/spec.md line 119, reading copy cannot overwrite Git; stale state stays NOT_VERIFIED | ALREADY_COVERED by REQ-003 and WORKFLOW State/evidence/projection. Unknown stays unknown is REQ and WORKFLOW NOT_VERIFIED wording, also WI-REQ-028. | ALREADY_COVERED |
| 009-ARCH-WAKE-READ | specs/009-strategy-execution/spec.md line 119, GPT retrieves the readback after wake-up | NOT_MIGRATED webhook caller. CONFLICTS C-037. Settled resume is a new GPT conversation (name or link only) plus Grok reading the same version (owner decision 2026-10-08; WORKFLOW 6.2.5). | NOT_MIGRATED |
| 009-ARCH-B-PERSIST | specs/009-strategy-execution/spec.md line 121, persist and read back decision B before affected work | specs/vnext/requirements.md § WI-REQ-038. A transport receipt is not a second spec (WI-REQ-030). Automatic resume transport is not imported. CONFLICTS C-037. No new paid infrastructure is WI-REQ-023 and APR-0001 Excluded actions. | MIGRATED |
| 009-ARCH-NO-GPT-WRITE | specs/009-strategy-execution/spec.md line 123, GPT has no direct GitHub writer; a future direct-write proposal stops | ALREADY_COVERED by APR-0001 Excluded actions and Approved targets (“no Git publishing authority”), and by WORKFLOW Roles and modules (Git operations need their own authority). | ALREADY_COVERED |
| 009-ARCH-EVENT-NOT-AUTHORITY | specs/009-strategy-execution/spec.md line 125, an event is a reference envelope and not authority, truth, state, or a bus | specs/vnext/requirements.md § WI-REQ-034 and § WI-REQ-039. The permission to wake a consumer is not imported. CONFLICTS C-037. | MIGRATED |
| 009-CONST-II-RETAIN | specs/009-strategy-execution/spec.md line 125, constitution II remains sole GitHub RUNTIME_OPERATOR | NOT_MIGRATED. CONFLICTS C-017. Same exclusion as CONST-II. | NOT_MIGRATED |
| 009-CONST-I-SAME-CHANGE | specs/009-strategy-execution/spec.md line 125, constitution I amended so Decision B stays on the same change id, branch, and pull request | NOT_MIGRATED. 009 constitution amendment. Same exclusion as CONST-I-009. Ancestry without that status is WI-REQ-038. | NOT_MIGRATED |
| 009-BASELINE-STAYS | specs/009-strategy-execution/spec.md line 125, v0.3.0 files are not rewritten and Current Approved Truth stays v0.3.0 | NOT_MIGRATED. CONFLICTS C-BASELINE. 009 state. | NOT_MIGRATED |
| 009-ARCH-THREE-FACTS | specs/009-strategy-execution/spec.md line 127, authored content, durable record, and native approval receipt are three facts; `actor: Jake` is not the receipt | specs/vnext/requirements.md § WI-REQ-008, § WI-REQ-035, and § WI-REQ-028. The spec itself leaves the native receipt NOT_VERIFIED. This row does not claim that receipt. | MIGRATED |
| 009-ARCH-SEQUENCE | specs/009-strategy-execution/spec.md line 129, persist and read back before a strategy_approved or strategy_resolved event may name the authority | NOT_MIGRATED as event-dispatch order. CONFLICTS C-037. Durable-before-authority is already WI-REQ-033 and WORKFLOW 6.2.3. | NOT_MIGRATED |
| 009-ARCH-NO-CONTINUE-WHILE-STOP | specs/009-strategy-execution/spec.md line 131, no CONTINUE or `event: admit` while the next action is STOP; CONTINUE is not merge proof | specs/vnext/requirements.md § WI-REQ-036 and § WI-REQ-037. `event: admit` is not a caller. | MIGRATED |
| 009-ARCH-B-ANCESTRY | specs/009-strategy-execution/spec.md line 133, Decision A then escalation then Decision B; reject, defer, and cancel stay terminal | specs/vnext/requirements.md § WI-REQ-038. Same ancestry rule as 009-DEC-B-RULE. 009 active-change status is not imported. | MIGRATED |
| 009-STATE-INDEX | specs/009-strategy-execution/spec.md line 137, PROJECT_STATE.md is the authoritative index | NOT_MIGRATED. 009 state. Would import the withheld PROJECT_STATE baseline index. Reconstruction is WORKFLOW 6.2.5–6.2.6. | NOT_MIGRATED |
| 009-STATE-ENGINE-SUBORDINATE | specs/009-strategy-execution/spec.md line 139, Spec Kit run state and event receipts do not resolve a conflicting spec or add a lifecycle | specs/vnext/requirements.md § WI-REQ-034. The “as in v0.3.0” pin is not adopted. CONFLICTS C-BASELINE for that pin only. | MIGRATED |
| 009-STATE-BASELINE-UNCHANGED | specs/009-strategy-execution/spec.md line 141, baseline remains v0.3.0; do not point the current binding at an unconverged successor; no backward write into WI-CHG-0008 | NOT_MIGRATED. CONFLICTS C-BASELINE. 009 state. | NOT_MIGRATED |
| 009-STATE-IDLE-REGISTER | specs/009-strategy-execution/spec.md line 143, idle-header registration and “resume requires the already indexed same change” | NOT_MIGRATED. Header writer and event pointer. CONFLICTS C-032 and C-037. An event cannot supply authority: already WI-REQ-033. | NOT_MIGRATED |
| 009-XPORT-CAPTURE | specs/009-strategy-execution/spec.md transport table, Strategy → authorized capture | NOT_MIGRATED webhook/API caller. CONFLICTS C-037. | NOT_MIGRATED |
| 009-XPORT-PLAN | specs/009-strategy-execution/spec.md transport table, `strategy_approved` wakes Cursor Automation | NOT_MIGRATED webhook/API caller. CONFLICTS C-037. | NOT_MIGRATED |
| 009-XPORT-ESCALATE | specs/009-strategy-execution/spec.md transport table, `material_escalation` wakes Strategy/GPT | NOT_MIGRATED webhook/API caller. CONFLICTS C-037. The durable stop record is WI-REQ-037. | NOT_MIGRATED |
| 009-XPORT-RESOLVE | specs/009-strategy-execution/spec.md transport table, `strategy_resolved` resumes the same change | NOT_MIGRATED webhook/API caller. CONFLICTS C-037. Durable decision B is WI-REQ-038. | NOT_MIGRATED |
| 009-XPORT-SHAPE | specs/009-strategy-execution/spec.md line 156, normalized event fields; chats, logs, and PR prose are not authority | NOT_MIGRATED as a production caller contract. CONFLICTS C-037. Historical shape only: docs/vnext-port/historical/specs/009-strategy-execution/contracts/strategy-event.md. “Prose is not authority” is WI-REQ-008 and WI-REQ-034. | NOT_MIGRATED |
| 009-XPORT-ORDER | specs/009-strategy-execution/spec.md line 158, durable capture before dispatch; reject path substitution | NOT_MIGRATED dispatch race for a caller. CONFLICTS C-037. Secrets stay out of records: WI-REQ-024. | NOT_MIGRATED |
| 009-XPORT-ADAPTER | specs/009-strategy-execution/spec.md line 160, thin adapters must not decide, infer approval, or schedule; PR activity does not replace the webhook architecture | NOT_MIGRATED caller design. CONFLICTS C-037. No second orchestrator is WI-REQ-030. | NOT_MIGRATED |
| 009-XPORT-COMPUTER-USE | specs/009-strategy-execution/spec.md line 162, Computer Use is fallback only and is not proof of primary transport | NOT_MIGRATED transport design. CONFLICTS C-037. Not a caller added here. | NOT_MIGRATED |
| 009-XPORT-UNKNOWNS | specs/009-strategy-execution/spec.md § Platform evidence and unknowns, lines 164–170 | NOT_MIGRATED. 009 promotion text and a capability probe for the withheld caller. Missing capability stays unproved (WI-REQ-028). This row is not an acceptance result. | NOT_MIGRATED |
| 009-STRATEGY-WHAT | specs/009-strategy-execution/spec.md § Strategy-layer responsibilities, lines 174–176, GPT clarifies WHAT and does not grant merge or invent the engineering plan | ALREADY_COVERED by WORKFLOW 6.2.1 and 6.2.6. Cursor planning is WI-REQ-036. Merge is APR-0001 Excluded actions. CONFLICTS C-015 only for any reading that keeps standing merge. | ALREADY_COVERED |
| 009-STRATEGY-SIGNAL | specs/009-strategy-execution/spec.md line 174, post-capture adapter emits the execution signal | NOT_MIGRATED caller. CONFLICTS C-037. | NOT_MIGRATED |
| 009-STRATEGY-PROOF | specs/009-strategy-execution/spec.md line 178, an agent-written `approved` field is not proof; Jake does not relay context | specs/vnext/requirements.md § WI-REQ-008 and § WI-REQ-035. Reconstruction from records is WORKFLOW 6.2.5. | MIGRATED |
| 009-COST-CAP | specs/009-strategy-execution/spec.md § Cost boundary and activation, lines 182–186 | specs/vnext/requirements.md § WI-REQ-023 and § WI-REQ-021. Paid commitments are also APR-0001 Excluded actions. A fallback trace is not completion (WI-REQ-028). | MIGRATED |
| 009-NONG-IF | specs/009-strategy-execution/spec.md § Non-goals, line 190, Information Flow/Digital Brain integration excluded | NOT_MIGRATED. CONFLICTS C-026. information-flow is the AIC code repository. | NOT_MIGRATED |
| 009-NONG-ENGINE | specs/009-strategy-execution/spec.md line 190, no second orchestrator, no central workflow database, no extra pull request per decision | specs/vnext/requirements.md § WI-REQ-030, § WI-REQ-039, and § WI-REQ-021. | MIGRATED |
| 009-NONG-MERGE-FREEZE | specs/009-strategy-execution/spec.md line 190, non-goal of changing the accepted exact-head merge policy | NOT_MIGRATED. That freeze would keep standing conditional merge. CONFLICTS C-015. | NOT_MIGRATED |
| 009-AC-PREAMBLE | specs/009-strategy-execution/spec.md § Executable acceptance specification, lines 194–196 | NOT_MIGRATED. Isolated enrolled repository and a native runner would be a second acceptance project. PASS, FAIL, and NOT_VERIFIED as words are already WI-REQ-028. Not an AIC acceptance result. | NOT_MIGRATED |
| 009-AC-01 | specs/009-strategy-execution/spec.md AC-01 | NOT_MIGRATED as an executable case and capture trigger. Approval-before-admission is WI-REQ-033 and WI-REQ-035. Not an AIC acceptance result. | NOT_MIGRATED |
| 009-AC-02 | specs/009-strategy-execution/spec.md AC-02 | NOT_MIGRATED as case text. Signals are not conversation authority: WI-REQ-034. | NOT_MIGRATED |
| 009-AC-03 | specs/009-strategy-execution/spec.md AC-03 | NOT_MIGRATED. Native trigger into a fresh Cursor run. CONFLICTS C-037. Reconstruction without a caller is WORKFLOW 6.2.5–6.2.6. | NOT_MIGRATED |
| 009-AC-04 | specs/009-strategy-execution/spec.md AC-04 | NOT_MIGRATED as case text. Verified Baseline before the plan is WI-REQ-036. | NOT_MIGRATED |
| 009-AC-05 | specs/009-strategy-execution/spec.md AC-05 | NOT_MIGRATED. In-boundary planning is WI-REQ-036. The case also depends on standing execution from WI-REQ-015. CONFLICTS C-015. | NOT_MIGRATED |
| 009-AC-06 | specs/009-strategy-execution/spec.md AC-06 | NOT_MIGRATED as case text. Bounded repair without a new material packet is WI-REQ-010 and WI-REQ-034. Same-branch repair is not a merge grant. | NOT_MIGRATED |
| 009-AC-07 | specs/009-strategy-execution/spec.md AC-07 | NOT_MIGRATED as case text. Material stop is WI-REQ-037. “Writes/merge stop” is not a merge right. | NOT_MIGRATED |
| 009-AC-08 | specs/009-strategy-execution/spec.md AC-08 | NOT_MIGRATED webhook caller that starts GPT. CONFLICTS C-037. Not a continue_project caller. | NOT_MIGRATED |
| 009-AC-09 | specs/009-strategy-execution/spec.md AC-09 | NOT_MIGRATED. Requires event delivery and an automatic GPT reread. CONFLICTS C-037. Stale authority stays NOT_VERIFIED: WI-REQ-028. Settled reread is WORKFLOW 6.2.5. | NOT_MIGRATED |
| 009-AC-10 | specs/009-strategy-execution/spec.md AC-10 | NOT_MIGRATED as a native-receipt case. Durable B ancestry is WI-REQ-038. The spec leaves the native approval receipt NOT_VERIFIED. Not an AIC acceptance result. | NOT_MIGRATED |
| 009-AC-11 | specs/009-strategy-execution/spec.md AC-11 | NOT_MIGRATED automatic same-change resume caller. CONFLICTS C-037. Ancestry without that transport is WI-REQ-038. | NOT_MIGRATED |
| 009-AC-12 | specs/009-strategy-execution/spec.md AC-12 | NOT_MIGRATED as an event-replay case. Idempotency is WI-REQ-039. Not a caller. | NOT_MIGRATED |
| 009-AC-13 | specs/009-strategy-execution/spec.md AC-13 | NOT_MIGRATED. Full native round trip, conditional merge, and WI-CHG-0009 evidence. CONFLICTS C-015, C-037, and 009 state. Not an AIC acceptance result. | NOT_MIGRATED |
| 009-AC-14 | specs/009-strategy-execution/spec.md AC-14 | NOT_MIGRATED as an event crash-recovery case. Idempotent recovery is WI-REQ-039. Not a caller. | NOT_MIGRATED |
| 009-AC-15 | specs/009-strategy-execution/spec.md AC-15 | NOT_MIGRATED as case text. Cost stop is WI-REQ-023 and APR-0001 Excluded actions. “Cursor persistence path may write” is standing Git permission. CONFLICTS C-015. | NOT_MIGRATED |
| 009-AC-16 | specs/009-strategy-execution/spec.md AC-16 | NOT_MIGRATED as case text. Drift stops admission: WI-REQ-028 and WI-REQ-030. The VNext graph pin is not imported. CONFLICTS C-GRAPH. | NOT_MIGRATED |
| 009-AC-EVIDENCE | specs/009-strategy-execution/spec.md line 217, live-result identity list; fixture-only AC-08/11/13 stay NOT_VERIFIED for native operation | NOT_MIGRATED. 009 evidence standard for a native run that is not authorized. Not an AIC acceptance result. | NOT_MIGRATED |
| 009-DOD-HISTORY | specs/009-strategy-execution/spec.md § Definition of Done, line 221 | NOT_MIGRATED. 009 state: v0.3.0 still current, pull request 25 review is not current, live next action is the 009 handoff. CONFLICTS C-BASELINE and C-009-STATE. | NOT_MIGRATED |
| 009-DOD-1 | specs/009-strategy-execution/spec.md Definition of Done item 1 | NOT_MIGRATED. 009 completion criterion for a change this port does not execute. No GPT operator reassignment is already APR-0001 Excluded actions and 009-ARCH-NO-GPT-WRITE. | NOT_MIGRATED |
| 009-DOD-2 | specs/009-strategy-execution/spec.md Definition of Done item 2 | NOT_MIGRATED. Real GPT invocation and same-change automatic resume. CONFLICTS C-037. | NOT_MIGRATED |
| 009-DOD-3 | specs/009-strategy-execution/spec.md Definition of Done item 3 | NOT_MIGRATED. Native AC-03/08/10/11/13 and the primary webhook round trip. CONFLICTS C-037. Missing capability is not waived as an acceptance result. | NOT_MIGRATED |
| 009-DOD-4 | specs/009-strategy-execution/spec.md Definition of Done item 4 | NOT_MIGRATED. Conditional merge, read-back of merge, and promotion of the VNext successor. CONFLICTS C-015 and C-BASELINE. APR-0001 Excluded actions include merge. | NOT_MIGRATED |
| 009-DOD-5 | specs/009-strategy-execution/spec.md Definition of Done item 5 | NOT_MIGRATED. Human status through Linear. CONFLICTS C-019. Notion projection is REQ-003, WORKFLOW State/evidence/projection, and APR-0001. | NOT_MIGRATED |
| 009-DOD-BLOCKED | specs/009-strategy-execution/spec.md line 231, unproved native invocation leaves the implementation blocked and v0.3.0 accepted | NOT_MIGRATED. CONFLICTS C-BASELINE. 009 state. Unproved capability stays unproved: WI-REQ-028. | NOT_MIGRATED |
| 009-PROMO-GRANT | specs/009-strategy-execution/spec.md § Promotion boundary, line 235 | NOT_MIGRATED. That promotion grant is 009 history. Superseded for this project by APR-0001 Approved scope (document promotion of the approved AIC payloads) and Excluded actions. Not an AIC promotion result. | NOT_MIGRATED |
| 009-PROMO-CHECKPOINT | specs/009-strategy-execution/spec.md § Promotion boundary, line 237 | NOT_MIGRATED. 009 checkpoint: pull request 25, handoff.md as the live next action, native activation unauthorized. CONFLICTS C-009-STATE. APR-0001 Excluded actions also exclude autonomous wakeup and Git publishing. | NOT_MIGRATED |
| CI-WORKFLOW | .github/workflows/change-control.yml | NOT_MIGRATED as a live workflow. Would execute withheld acceptance runners and the native marker. | NOT_MIGRATED |
| README-ORIENT | README.md | NOT_MIGRATED. It names VNext as the code repo and sends readers to PROJECT_STATE. | NOT_MIGRATED |

## continue_project

Rows WI-REQ-014, WI-REQ-032, WI-REQ-035, WI-REQ-037, WI-REQ-038, and ENTRY-RESUME are the resume-related rules. The VNext port added no caller. Track C later added an on-request wrapper, documented in `continue-project-trackc.md`. It is not a webhook and it does not close R10-14.

## Coverage check

Method, run against the read-only mirror of `c99355daf4889148dc517704bb6423de221d0770` and GitHub blob ids at main `7168117db85befa4e9f36420d306c667ffc12cbf`. This check does not claim an acceptance result.

1. Byte identity for specs 001–008. Every file under `specs/001-requirements-baseline` through `specs/008-project-bootstrap` was hashed with `git hash-object` on the 009 mirror and compared with the GitHub contents SHA of that path at main. GitHub content SHAs are git blob ids. Result: 39 files, 39 identical, 0 different. Spec 009 is not on main. Because the 001–008 blobs match, no requirement text exists on only one of those two SHAs. Rows for WI-REQ-001–034 and for 008-CASE-01–13 apply to both.

2. Requirement ids. `rg -o "WI-REQ-[0-9]+"` across the 009 mirror (which contains the identical 001–008 bodies plus spec 009) returns WI-REQ-001 through WI-REQ-039 and no other number. Each id is a row id in this table. Unmatched: 0.

3. Spec 009 acceptance ids. `rg -o "AC-[0-9]+"` on `specs/009-strategy-execution/spec.md` returns AC-01 through AC-16. Each is row `009-AC-01` through `009-AC-16`. Unmatched: 0.

4. Spec 009 headings after the `WI-REQ-039` heading. Each heading has at least one row:

| Heading in spec 009 | Rows |
| --- | --- |
| Necessary architecture and authority amendment | 009-ARCH-ADAPTERS and the 009-ARCH-* rows through 009-ARCH-B-ANCESTRY |
| Authorized decision persistence and reading path | 009-ARCH-ENVELOPE, 009-ARCH-GIT-OWNER, 009-ARCH-CAPTURE-WAKE, 009-ARCH-PROJECTION, 009-ARCH-WAKE-READ, 009-ARCH-B-PERSIST, 009-ARCH-NO-GPT-WRITE, 009-ARCH-EVENT-NOT-AUTHORITY, 009-CONST-II-RETAIN, 009-CONST-I-SAME-CHANGE, 009-BASELINE-STAYS, 009-ARCH-THREE-FACTS, 009-ARCH-SEQUENCE, 009-ARCH-NO-CONTINUE-WHILE-STOP, 009-ARCH-B-ANCESTRY |
| State and record placement | 009-STATE-INDEX, 009-STATE-ENGINE-SUBORDINATE, 009-STATE-BASELINE-UNCHANGED, 009-STATE-IDLE-REGISTER |
| Transport responsibilities and selected minimal route | 009-TRANSPORT, 009-XPORT-CAPTURE, 009-XPORT-PLAN, 009-XPORT-ESCALATE, 009-XPORT-RESOLVE, 009-XPORT-SHAPE, 009-XPORT-ORDER, 009-XPORT-ADAPTER, 009-XPORT-COMPUTER-USE |
| Platform evidence and unknowns | 009-XPORT-UNKNOWNS |
| Strategy-layer responsibilities | 009-STRATEGY-WHAT, 009-STRATEGY-SIGNAL, 009-STRATEGY-PROOF |
| Cost boundary and activation | 009-COST-CAP |
| Non-goals | 009-NONG-IF, 009-NONG-ENGINE, 009-NONG-MERGE-FREEZE |
| Executable acceptance specification | 009-AC-PREAMBLE, 009-AC-01 through 009-AC-16, 009-AC-EVIDENCE |
| Definition of Done | 009-DOD-HISTORY, 009-DOD-1, 009-DOD-2, 009-DOD-3, 009-DOD-4, 009-DOD-5, 009-DOD-BLOCKED |
| Promotion boundary | 009-PROMO-GRANT, 009-PROMO-CHECKPOINT |

5. `must` / `shall` after WI-REQ-039. From the heading `## Necessary architecture and authority amendment` through the end of `specs/009-strategy-execution/spec.md`: 9 occurrences of `must` on 8 lines, and 0 occurrences of `shall`. There is no separate SHALL id. Those lines sit under Authorized decision persistence (2), State and record placement (1), Transport responsibilities (3 occurrences on 2 lines), Cost boundary (1), and Executable acceptance specification (2). Each of those headings is in step 4. Unmatched headings: 0. The `must` sentences inside WI-REQ-039 itself stay on the WI-REQ-039 row.

6. Spec 008 executable cases. The acceptance table numbers cases 1 through 13. Both SHAs share that blob. Rows `008-CASE-01` through `008-CASE-13` plus `008-CASE-EXTRA` and `008-DOD-COMPLETE`, `008-DOD-MERGE-LINEAR`, `008-DOD-UNPROVED`, and `008-DOD-GROUNDING` cover that table and the Definition of Done under it. Unmatched case numbers: 0.

7. Other id families already in the table: constitution principles I, II, III, IV and the 009 amendment of I (`CONST-I`, `CONST-I-009`, `CONST-II`, `CONST-III`, `CONST-IV`); each `scripts/wi_*` guard, including the two acceptance runners withheld as `SCRIPT-BOOTSTRAP-ACCEPT` and `SCRIPT-STRATEGY-ACCEPT`; authority-graph roles `GRAPH-ENG`, `GRAPH-WORKFLOW`, `GRAPH-ARCH`, `GRAPH-IMPL`, `GRAPH-PROJ`, and `GRAPH-READING`.

Result: unmatched WI-REQ ids 0, unmatched AC-01–AC-16 ids 0, unmatched spec 009 headings after WI-REQ-039 0, unmatched spec 008 case numbers 0, differing 001–008 files 0. Nothing in that set was left without a class. This is a mapping check, not an acceptance result.
