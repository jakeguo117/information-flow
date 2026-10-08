# AIC-EVT-VNEXT-PORT-INVENTORY-0001

project_id: AI-AGENTS-COOPERATE
document_id: AIC-EVT-VNEXT-PORT-INVENTORY-0001
event: AIC-VNEXT-PORT
owner_decision: 2026-10-08 — information-flow is the single AIC code repository
status: INVENTORY — not an acceptance result

## SHAs inspected

- `main` is `7168117db85befa4e9f36420d306c667ffc12cbf`. The requested prefix `7168117` matches. Commit subject: `WI-CHG-0008 record the final reconstruction`.
- Requested branch name `wi-chg-0009` does not exist. The branch at the requested SHA is `wi-chg-0009-strategy-execution`.
- `wi-chg-0009-strategy-execution` is `c99355daf4889148dc517704bb6423de221d0770`. The requested prefix `c99355d` matches. Commit subject: `Record DEC-0004 and stop before native acceptance execution.`
- Inspection was read-only through the GitHub API. Nothing in `workspace-infrastructure-vnext` was pushed, merged, or deleted.
- `information-flow` `main` at inventory time was `51f30f2ce5fd62b9f23cfb5752999a2349c8edf4`. This port does not move that branch.

## How to read a row

- **MIGRATE** — rule content is in this PR at the landing path. Names and repo pins are adapted. Conflicting sentences inside an otherwise ported spec are withheld and listed in `CONFLICTS.md`.
- **ALREADY_COVERED_BY_AIC** — no separate import, because the approved AIC document already states the rule. This inventory has no whole file in that class; covered rules are rows in `RULE-MAP.md`.
- **NOT_MIGRATED** — left in the VNext archive. Reason is in the landing column.

Tree difference: commits after `7168117` on `wi-chg-0009-strategy-execution` are the WI-CHG-0009 series. Files present only on that branch, and files whose blobs differ from main, are marked in the tree column. Spec 009 exists only on the 009 branch. Spec bodies 001–008 were byte-compared; see the next section. Every one of those files is identical on the two SHAs.

## Counts

- Files in the union of the two trees: 150
- MIGRATE: 133
- ALREADY_COVERED_BY_AIC (file-level): 0
- NOT_MIGRATED: 17

## Spec bodies 001–008 byte comparison

Method: GitHub contents blob SHA at main `7168117db85befa4e9f36420d306c667ffc12cbf`, compared with `git hash-object` of the same path on the read-only mirror of `c99355daf4889148dc517704bb6423de221d0770`. Those two ids are the same git blob id. The mirror is the 009 tree: its constitution blob is not the main constitution blob.

Result: 39 files, 39 identical, 0 different. No rule text in specs 001–008 exists on only one SHA. RULE-MAP rows for those files apply to both commits. Spec 009 has no counterpart on main.

| Path | Blob (both SHAs) | Result |
| --- | --- | --- |
| `specs/001-requirements-baseline/change.md` | `21148da10184148c6d006d21c839e85391088dd9` | identical |
| `specs/001-requirements-baseline/spec.md` | `9e9c1ed98cc320407058f02df6baa177abb37928` | identical |
| `specs/002-durable-handoff/handoff.md` | `1d70e6cf283abcedfc960ca3aa37fde04a4a714d` | identical |
| `specs/003-workflow/handoff.md` | `30fd3fe4a744d303dd30ef1b34a3dc6b4f375edc` | identical |
| `specs/004-verify-converge/convergence.md` | `756b755d045c852ae3c7b8ec34af806b52f4a6c2` | identical |
| `specs/004-verify-converge/handoff.md` | `e5a11ba8017ba9e3a73ca35321f193bb15224ce1` | identical |
| `specs/004-verify-converge/review.md` | `0887ec08dc0639e9088abc1d27f1cbca3081107a` | identical |
| `specs/004-verify-converge/verification.md` | `2ea3335be5094ac19c819a24ec37610887129126` | identical |
| `specs/005-projection/convergence.md` | `14529a091fb25bb02d71a8e4d26f989c3c45a02a` | identical |
| `specs/005-projection/handoff.md` | `a2233af3945efe8f201d0cba0766bfd82f4530cb` | identical |
| `specs/005-projection/review.md` | `a845548a421297f271d8dcaa1dae2553bcb0757f` | identical |
| `specs/005-projection/verification.md` | `30cb83e397aeb0afaf00c9ee9c1f6676fe678a52` | identical |
| `specs/006-acceptance-a/change.md` | `c84da32f0510c8c8bf53f33a11cd8d34a2d8d30f` | identical |
| `specs/006-acceptance-a/handoff.md` | `394e2d4c595aaf0af3df83c7add5dbefb76b4c9d` | identical |
| `specs/006-acceptance-a/ownership.md` | `3562c691e30f44d3a0965698ab519783dcd9c712` | identical |
| `specs/006-acceptance-a/plan.md` | `ab8a745ad7c2f0d319b6b20d2130069ca487647f` | identical |
| `specs/006-acceptance-a/spec.md` | `622e3a042152c525601b7717e30c07bd0fec8933` | identical |
| `specs/006-acceptance-a/tasks.md` | `d52600078b4947d43e8238ba27091a2c8dedf203` | identical |
| `specs/007-acceptance-b/change.md` | `52a6d812930eaf56193254050d3e5929ded33149` | identical |
| `specs/007-acceptance-b/convergence.md` | `d3818a7776b1207a4807f9de49b1d33a8a92b4af` | identical |
| `specs/007-acceptance-b/evidence.md` | `fbd91250689efd982ea68c48022e3c2b65782124` | identical |
| `specs/007-acceptance-b/plan.md` | `6511b0a0847bd17089f63b89e0ef45e52cf63106` | identical |
| `specs/007-acceptance-b/review.md` | `2360feb61c2cd34ae37db78cbe14feb6eecf62bc` | identical |
| `specs/007-acceptance-b/spec.md` | `f8c21ff1efd8f76fdb8dc35bd2961fea9361046f` | identical |
| `specs/007-acceptance-b/tasks.md` | `70e3ad0c66d0b645f1512222402964c5871baff6` | identical |
| `specs/007-acceptance-b/verification.md` | `6d6a5e6e93a183b99e5ccc11abb46deeeffba1ee` | identical |
| `specs/008-project-bootstrap/change.md` | `e1aee481c221d4c8f1e8e59da6761fc74da1d9d7` | identical |
| `specs/008-project-bootstrap/ci.md` | `4bebab71a6d535b1cd47dfea90fbc152d0f3d032` | identical |
| `specs/008-project-bootstrap/convergence.md` | `8d8334a92583e5a93c3a56f136f5d2ef722cf8de` | identical |
| `specs/008-project-bootstrap/evidence.md` | `6b1617c3c6e0122b927f2345235865dd339ea543` | identical |
| `specs/008-project-bootstrap/handoff.md` | `815ff3a80b842d0c76d4642ac47ee00cfd6ec0eb` | identical |
| `specs/008-project-bootstrap/identity.md` | `bed10f84b767ada53c652541111161e8df602227` | identical |
| `specs/008-project-bootstrap/ownership.md` | `d3f3a229e621d053ddfca8043ae4b84e3d909f8e` | identical |
| `specs/008-project-bootstrap/plan.md` | `aa79f2a882f2d84917cb3795a013b698458feff3` | identical |
| `specs/008-project-bootstrap/readback.md` | `ffdcf506d878b7af360cdfe6131a2ccebfa0c824` | identical |
| `specs/008-project-bootstrap/review.md` | `e967a2436cbf0c93cb9f35403bb38539c4dc5575` | identical |
| `specs/008-project-bootstrap/spec.md` | `4c472aac38246bac5c53002cecfd7acd6b2c1302` | identical |
| `specs/008-project-bootstrap/tasks.md` | `240338d374258108aa202e97e5995f02474f058b` | identical |
| `specs/008-project-bootstrap/verification.md` | `c854344f70fd4616462ab9eb49f22ac854450eca` | identical |

## File inventory

| Path | Tree | Class | Landing or reason |
| --- | --- | --- | --- |
| `.cursor/agents/implementer.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/agents/implementer.md (not installed as a live .cursor agent). |
| `.cursor/agents/reviewer.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/agents/reviewer.md (not installed as a live .cursor agent). |
| `.cursor/agents/verifier.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/agents/verifier.md (not installed as a live .cursor agent). |
| `.cursor/skills/speckit-analyze/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-analyze/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-bug-assess/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-bug-assess/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-bug-fix/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-bug-fix/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-bug-test/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-bug-test/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-checklist/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-checklist/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-clarify/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-clarify/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-constitution/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-constitution/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-converge/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-converge/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-implement/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-implement/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-plan/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-plan/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-specify/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-specify/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-tasks/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-tasks/SKILL.md (not installed as a live skill). |
| `.cursor/skills/speckit-taskstoissues/SKILL.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/cursor/skills/speckit-taskstoissues/SKILL.md (not installed as a live skill). |
| `.github/workflows/change-control.yml` | both; bytes differ on 009 | NOT_MIGRATED | Live workflow runs VNext acceptance suites and the native-e2e marker. Not installed on information-flow. Check scripts that are guards are ported separately. No standing merge workflow is added. |
| `.specify/.gitignore` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/.gitignore |
| `.specify/bugs/acceptance-bug-fixture/assessment.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/acceptance-bug-fixture/assessment.md |
| `.specify/bugs/acceptance-bug-fixture/fix.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/acceptance-bug-fixture/fix.md |
| `.specify/bugs/acceptance-bug-fixture/test.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/acceptance-bug-fixture/test.md |
| `.specify/bugs/external-authority-binding/assessment.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/external-authority-binding/assessment.md |
| `.specify/bugs/external-authority-binding/fix.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/external-authority-binding/fix.md |
| `.specify/bugs/external-authority-binding/test.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/bugs/external-authority-binding/test.md |
| `.specify/extensions.yml` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions.yml |
| `.specify/extensions/.registry` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/.registry |
| `.specify/extensions/bug/README.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/bug/README.md |
| `.specify/extensions/bug/commands/speckit.bug.assess.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/bug/commands/speckit.bug.assess.md |
| `.specify/extensions/bug/commands/speckit.bug.fix.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/bug/commands/speckit.bug.fix.md |
| `.specify/extensions/bug/commands/speckit.bug.test.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/bug/commands/speckit.bug.test.md |
| `.specify/extensions/bug/extension.yml` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/extensions/bug/extension.yml |
| `.specify/init-options.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/init-options.json |
| `.specify/integration.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/integration.json |
| `.specify/integrations/cursor-agent.manifest.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/integrations/cursor-agent.manifest.json |
| `.specify/integrations/speckit.manifest.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/integrations/speckit.manifest.json |
| `.specify/memory/.constitution-template.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/memory/.constitution-template.json |
| `.specify/memory/constitution.md` | both; bytes differ on 009 | MIGRATE | specs/vnext/constitution.md (principle II and the 009 amendment withheld). |
| `.specify/scripts/bash/check-prerequisites.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/check-prerequisites.sh |
| `.specify/scripts/bash/common.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/common.sh |
| `.specify/scripts/bash/create-new-feature.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/create-new-feature.sh |
| `.specify/scripts/bash/resolve-template.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/resolve-template.sh |
| `.specify/scripts/bash/setup-plan.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/setup-plan.sh |
| `.specify/scripts/bash/setup-tasks.sh` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/scripts/bash/setup-tasks.sh |
| `.specify/templates/checklist-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/checklist-template.md |
| `.specify/templates/constitution-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/constitution-template.md |
| `.specify/templates/overrides/change.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/overrides/change.md |
| `.specify/templates/overrides/handoff-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/overrides/handoff-template.md |
| `.specify/templates/overrides/review-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/overrides/review-template.md |
| `.specify/templates/overrides/spec-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/overrides/spec-template.md |
| `.specify/templates/overrides/verification-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/overrides/verification-template.md |
| `.specify/templates/plan-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/plan-template.md |
| `.specify/templates/spec-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/spec-template.md |
| `.specify/templates/tasks-template.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/templates/tasks-template.md |
| `.specify/workflows/change-lifecycle/workflow.yml` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/workflows/change-lifecycle.yml (merge grant removed; not a live workflow). |
| `.specify/workflows/speckit/workflow.yml` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/workflows/speckit/workflow.yml |
| `.specify/workflows/workflow-registry.json` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/.specify/workflows/workflow-registry.json |
| `PROJECT_STATE.md` | both; bytes differ on 009 | NOT_MIGRATED | VNext baseline identity and WI-CHG-0009 execution state. Owner decision and HANDOFF@0.2.0 exclude both. |
| `README.md` | both; treated as main content unless noted | NOT_MIGRATED | Points agents at PROJECT_STATE as the baseline and names VNext as the forward code repo. Conflicts with information-flow as the single AIC code repo. |
| `docs/acceptance/bug-fixture.txt` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/docs/acceptance/bug-fixture.txt |
| `docs/acceptance/fixture.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/docs/acceptance/fixture.md |
| `docs/acceptance/native-e2e-marker.txt` | both; treated as main content unless noted | NOT_MIGRATED | WI-CHG-0008 native end-to-end marker. Importing it would look like an acceptance result. No AIC acceptance PASS is claimed. |
| `docs/authority-graph.json` | both; bytes differ on 009 | NOT_MIGRATED | Current-authority pins name the VNext repo, a VNext Drive foundation folder, a VNext architecture file, and Linear. Those pins conflict with REQ-003, WORKFLOW@0.2.0, and APR-0001. The graph file is not imported. See CONFLICTS C-GRAPH. |
| `docs/linear-projection.md` | both; treated as main content unless noted | NOT_MIGRATED | Binds the human projection to Linear project P-JAK-19. AIC projection is Notion only. The six-field scan is ported in docs/vnext-port/projection.md. See CONFLICTS C-019. |
| `docs/reconciliation.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/reconciliation.md (Drive-as-projection sentence withheld). |
| `scripts/wi_acceptance_fixture_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_acceptance_fixture_check.sh |
| `scripts/wi_admit.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_admit.sh |
| `scripts/wi_ancestry_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_ancestry_check.sh |
| `scripts/wi_approval_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_approval_check.sh |
| `scripts/wi_authority_check.py` | both; bytes differ on 009 | MIGRATE | scripts/vnext/wi_authority_check.py |
| `scripts/wi_authority_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_authority_check.sh |
| `scripts/wi_bootstrap.py` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_bootstrap.py |
| `scripts/wi_bootstrap.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_bootstrap.sh |
| `scripts/wi_bootstrap_acceptance.sh` | both; bytes differ on 009 | NOT_MIGRATED | WI-CHG-0008 acceptance runner. It builds synthetic projects and checks the v0.3.0 baseline. Not imported: second acceptance project, baseline, and acceptance PASS. |
| `scripts/wi_converge_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_converge_check.sh |
| `scripts/wi_durable_proof.sh` | both; bytes differ on 009 | MIGRATE | scripts/vnext/wi_durable_proof.sh |
| `scripts/wi_escalation_record.sh` | 009 only | MIGRATE | scripts/vnext/wi_escalation_record.sh |
| `scripts/wi_event_check.py` | 009 only | MIGRATE | scripts/vnext/wi_event_check.py |
| `scripts/wi_event_check.sh` | 009 only | MIGRATE | scripts/vnext/wi_event_check.sh |
| `scripts/wi_material_stop.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_material_stop.sh |
| `scripts/wi_merge_gate.sh` | both; bytes differ on 009 | MIGRATE | scripts/vnext/wi_merge_gate.sh |
| `scripts/wi_merge_if_head.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_merge_if_head.sh |
| `scripts/wi_ownership_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_ownership_check.sh |
| `scripts/wi_plan_boundary.sh` | 009 only | MIGRATE | scripts/vnext/wi_plan_boundary.sh |
| `scripts/wi_pr_lookup.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_pr_lookup.sh |
| `scripts/wi_preflight.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_preflight.sh |
| `scripts/wi_projection_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_projection_check.sh |
| `scripts/wi_resolution_check.sh` | 009 only | MIGRATE | scripts/vnext/wi_resolution_check.sh |
| `scripts/wi_retry_budget.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_retry_budget.sh |
| `scripts/wi_review_route.sh` | both; bytes differ on 009 | MIGRATE | scripts/vnext/wi_review_route.sh |
| `scripts/wi_secret_check.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_secret_check.sh |
| `scripts/wi_strategy_acceptance.sh` | 009 only | NOT_MIGRATED | WI-CHG-0009 acceptance runner. It is 009 execution machinery and a strategy-event caller surface. Not imported and not run. |
| `scripts/wi_workflow_validate.sh` | both; treated as main content unless noted | MIGRATE | scripts/vnext/wi_workflow_validate.sh |
| `specs/001-requirements-baseline/change.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/001-requirements-baseline/change.md |
| `specs/001-requirements-baseline/spec.md` | both; blob identical | MIGRATE | specs/vnext/requirements.md (non-conflicting sections). Conflicting sections are not imported; see CONFLICTS.md. |
| `specs/002-durable-handoff/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/002-durable-handoff/handoff.md |
| `specs/003-workflow/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/003-workflow/handoff.md |
| `specs/004-verify-converge/convergence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/004-verify-converge/convergence.md |
| `specs/004-verify-converge/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/004-verify-converge/handoff.md |
| `specs/004-verify-converge/review.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/004-verify-converge/review.md |
| `specs/004-verify-converge/verification.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/004-verify-converge/verification.md |
| `specs/005-projection/convergence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/005-projection/convergence.md |
| `specs/005-projection/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/005-projection/handoff.md |
| `specs/005-projection/review.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/005-projection/review.md |
| `specs/005-projection/verification.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/005-projection/verification.md |
| `specs/006-acceptance-a/change.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/change.md |
| `specs/006-acceptance-a/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/handoff.md |
| `specs/006-acceptance-a/ownership.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/ownership.md |
| `specs/006-acceptance-a/plan.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/plan.md |
| `specs/006-acceptance-a/spec.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/spec.md |
| `specs/006-acceptance-a/tasks.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/006-acceptance-a/tasks.md |
| `specs/007-acceptance-b/change.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/change.md |
| `specs/007-acceptance-b/convergence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/convergence.md |
| `specs/007-acceptance-b/evidence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/evidence.md |
| `specs/007-acceptance-b/plan.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/plan.md |
| `specs/007-acceptance-b/review.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/review.md |
| `specs/007-acceptance-b/spec.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/spec.md |
| `specs/007-acceptance-b/tasks.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/tasks.md |
| `specs/007-acceptance-b/verification.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/007-acceptance-b/verification.md |
| `specs/008-project-bootstrap/change.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/change.md |
| `specs/008-project-bootstrap/ci.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/ci.md |
| `specs/008-project-bootstrap/convergence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/convergence.md |
| `specs/008-project-bootstrap/evidence.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/evidence.md |
| `specs/008-project-bootstrap/handoff.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/handoff.md |
| `specs/008-project-bootstrap/identity.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/identity.md |
| `specs/008-project-bootstrap/ownership.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/ownership.md |
| `specs/008-project-bootstrap/plan.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/plan.md |
| `specs/008-project-bootstrap/readback.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/readback.md |
| `specs/008-project-bootstrap/review.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/review.md |
| `specs/008-project-bootstrap/spec.md` | both; blob identical | MIGRATE | specs/vnext/requirements.md (non-conflicting sections). Conflicting sections are not imported; see CONFLICTS.md. |
| `specs/008-project-bootstrap/tasks.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/tasks.md |
| `specs/008-project-bootstrap/verification.md` | both; blob identical | MIGRATE | docs/vnext-port/historical/specs/008-project-bootstrap/verification.md |
| `specs/009-strategy-execution/approval.md` | 009 only | NOT_MIGRATED | WI-CHG-0009 approval/status record, including implementation-in-progress state. 009 status is not imported. Non-conflicting requirement deltas are in specs/vnext/requirements.md. |
| `specs/009-strategy-execution/capability-probe.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/capability-probe.md |
| `specs/009-strategy-execution/change.md` | 009 only | NOT_MIGRATED | WI-CHG-0009 change status, checkpoint, and baseline pins. 009 status and the VNext baseline are not imported. |
| `specs/009-strategy-execution/closure-report.md` | 009 only | NOT_MIGRATED | WI-CHG-0009 closure/review/CI status. 009 state. Not imported. No AIC acceptance PASS. |
| `specs/009-strategy-execution/contracts/strategy-event.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/contracts/strategy-event.md |
| `specs/009-strategy-execution/controlling-update.md` | 009 only | NOT_MIGRATED | WI-CHG-0009 controlling-update status. 009 state. Not imported. |
| `specs/009-strategy-execution/data-model.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/data-model.md |
| `specs/009-strategy-execution/escalation.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/escalation.md |
| `specs/009-strategy-execution/handoff.md` | 009 only | NOT_MIGRATED | WI-CHG-0009 execution handoff and reconstruction boundary for that change. 009 state. Resume rules that remain are mapped, not a continue_project caller. |
| `specs/009-strategy-execution/native-acceptance.md` | 009 only | NOT_MIGRATED | Bounded native acceptance package for WI-CHG-0009, including PASS/BLOCKED/FAIL and an activation condition. Not imported: 009 execution package, second acceptance project, acceptance PASS. |
| `specs/009-strategy-execution/plan.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/plan.md |
| `specs/009-strategy-execution/quickstart.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/quickstart.md |
| `specs/009-strategy-execution/research.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/research.md |
| `specs/009-strategy-execution/resolution.md` | 009 only | NOT_MIGRATED | WI-CHG-0009-DEC-0004 / DEC-0003 status (PR 25, native run, spend, abandoned scope). 009 state. Not imported. |
| `specs/009-strategy-execution/review.md` | 009 only | NOT_MIGRATED | Records RESULT PASS for VNext SHA 755a0b3. 009 review state. Not an AIC acceptance result. |
| `specs/009-strategy-execution/spec.md` | 009 only | MIGRATE | specs/vnext/requirements.md keeps WI-REQ-035–039 record rules only. Each later rule, acceptance case, and definition-of-done item is a RULE-MAP row (`009-ARCH-*`, `009-XPORT-*`, `009-AC-01`–`009-AC-16`, `009-DOD-*`, `009-PROMO-*`). Those items are mapped, not imported as 009 state or as a caller. |
| `specs/009-strategy-execution/tasks.md` | 009 only | MIGRATE | docs/vnext-port/historical/specs/009-strategy-execution/tasks.md |
| `specs/009-strategy-execution/verification.md` | 009 only | NOT_MIGRATED | Records VERIFIED for a VNext content SHA. 009 verification state. Not an AIC acceptance result. |
| `templates/change.md` | both; treated as main content unless noted | MIGRATE | docs/vnext-port/historical/templates/change.md |

## Could not classify

No remaining file in the 150-file tree was left unclassified. Granola had no account on this run, so meeting notes were not a second source. The approved uploads and the two Git SHAs were the sources.
