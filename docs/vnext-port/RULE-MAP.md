# VNext rule map

Sources: main `7168117db85befa4e9f36420d306c667ffc12cbf` and `wi-chg-0009-strategy-execution` `c99355daf4889148dc517704bb6423de221d0770`.
Approved documents win: AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, AIC-APR-0001.

## Counts

- Total rule rows: 97
- MIGRATED: 68
- ALREADY_COVERED: 4
- NOT_MIGRATED: 25
- Rows that record a conflict: 23

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
| ACCEPT-CASES-008 | specs/008-project-bootstrap/spec.md acceptance cases 1–6 and 8–12 | NOT_MIGRATED as case text. The executable acceptance runner is withheld. Non-merge predicates already live in WI-REQ-014, WI-REQ-025, WI-REQ-029, and WI-REQ-033. Case 7 and the conditional-merge sentence are CONFLICTS C-015. | NOT_MIGRATED |
| ACCEPT-CASE-7 | specs/008-project-bootstrap/spec.md acceptance case 7 and Definition of Done conditional merge | NOT_MIGRATED. CONFLICTS C-015. | NOT_MIGRATED |
| 009-DEC-B-RULE | specs/009-strategy-execution/spec.md Decision B ancestry; constitution 0.1.1 | The ancestry rule is WI-REQ-038. The statement that WI-CHG-0009 is the active change, that PR 25 stays open, and that v0.3.0 stays current is NOT_MIGRATED 009 state. | MIGRATED |
| 009-TRANSPORT | specs/009-strategy-execution/spec.md webhook/API primary transport; Computer Use fallback | NOT_MIGRATED as a caller. CONFLICTS C-037. Product details for continue_project remain pending. | NOT_MIGRATED |
| 009-AC-DOD | specs/009-strategy-execution/spec.md sections after WI-REQ-039: architecture amendment, AC-01–AC-16, Definition of Done, Promotion boundary | NOT_MIGRATED. Those sections require webhook wake-up, standing Git writes, Linear projection, or v0.3.0 as current. CONFLICTS C-015, C-017, C-019, C-037, C-BASELINE, and 009 state. Not an AIC acceptance result. | NOT_MIGRATED |
| CI-WORKFLOW | .github/workflows/change-control.yml | NOT_MIGRATED as a live workflow. Would execute withheld acceptance runners and the native marker. | NOT_MIGRATED |
| README-ORIENT | README.md | NOT_MIGRATED. It names VNext as the code repo and sends readers to PROJECT_STATE. | NOT_MIGRATED |

## continue_project

Rows WI-REQ-014, WI-REQ-032, WI-REQ-035, WI-REQ-037, WI-REQ-038, and ENTRY-RESUME are the resume-related rules. No caller was added. `scripts/continue_project.py` is unchanged.

## Omissions

Every WI-REQ-001 through WI-REQ-039 has a row. Constitution principles, lifecycle merge, authority-graph roles, each ported guard script, templates, agents, the withheld baseline/009-status bundle, and the withheld spec 009 acceptance/definition-of-done tail (`009-AC-DOD`) have rows. No rule id in that set was left without a class. Spec 008 acceptance case text is `ACCEPT-CASES-008` and is not copied as executable cases.
