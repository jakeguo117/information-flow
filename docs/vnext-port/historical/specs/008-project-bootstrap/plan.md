<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Plan WI-CHG-0008

The protocol scripts read the declared repository, branch, and protocol commit. They do not special-case this repository. This repository enrolls itself as the test project. Disposable repositories prove that another declared repository can enroll.

Allowed files:
- PROJECT_STATE.md
- scripts/wi_bootstrap.sh
- scripts/wi_bootstrap.py
- scripts/wi_bootstrap_acceptance.sh
- scripts/wi_preflight.sh
- scripts/wi_approval_check.sh
- scripts/wi_admit.sh
- scripts/wi_pr_lookup.sh
- scripts/wi_merge_gate.sh
- scripts/wi_merge_if_head.sh
- scripts/wi_durable_proof.sh
- scripts/wi_retry_budget.sh
- scripts/wi_material_stop.sh
- scripts/wi_converge_check.sh
- templates/change.md
- .specify/templates/overrides/change.md
- .specify/workflows/change-lifecycle/workflow.yml
- .github/workflows/change-control.yml
- .cursor/agents/implementer.md
- .cursor/agents/reviewer.md
- .cursor/agents/verifier.md
- specs/008-project-bootstrap/change.md
- specs/008-project-bootstrap/handoff.md
- specs/008-project-bootstrap/plan.md
- specs/008-project-bootstrap/tasks.md
- specs/008-project-bootstrap/evidence.md
- docs/acceptance/native-e2e-marker.txt

Checks:
- bash scripts/wi_bootstrap_acceptance.sh
- bash scripts/wi_preflight.sh --check
- bash scripts/wi_approval_check.sh --check specs/008-project-bootstrap/change.md
- bash scripts/wi_approval_check.sh --check specs/007-acceptance-b/change.md
- bash scripts/wi_workflow_validate.sh
- bash scripts/wi_authority_check.sh --self-test
- bash scripts/wi_acceptance_fixture_check.sh --expect B

Cursor Automations are not created. A new cloud spending commitment is outside this approval.

## Case 13 native execution

Derived 2026-10-01 from origin/main dd5509ba398faed7cd0fff478e20249108e576b1. The protocol implementation is already on main. Cases 12 and 13 are NOT_VERIFIED. Cases 1 and 3 stay NOT_VERIFIED as recorded. Cases 4-11 and case 2 stay PASS.

The smallest fixture is docs/acceptance/native-e2e-marker.txt, one assertion in scripts/wi_bootstrap_acceptance.sh, and the same assertion in change-control. A one-shot Cursor Cloud Agent reads the handoff and implements that fixture. A later one-shot Cloud Agent repairs one injected routine defect from the failing check. No standing Cursor Automation is created. No plan upgrade, add-on, or new fixed monthly commitment is created.

PLAN_ACCEPTED_WITHIN_BOUNDARY
