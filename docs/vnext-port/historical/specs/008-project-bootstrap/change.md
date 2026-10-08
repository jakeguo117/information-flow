<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# WI-CHG-0008 — Project bootstrap and durable execution admission

Change ID / title: WI-CHG-0008 Project bootstrap and durable execution admission
Status: Approved
Owner / decision owner: SPEC_OWNER / Jake
Base Current Approved Truth: specs/001-requirements-baseline/spec.md at 3c35008526bbdefa1ba84016f179867ad950feec; project baseline v0.2.0
WHY: Jake has approved a reusable project operating protocol. A fresh supported agent must reconstruct a project's legal next action from its own repository, and an approved material change must reach execution without Jake relaying conversational context.
ADDED: Project-local VNext enrollment and version pin; deterministic initialized/not-initialized detection; bootstrap reconstruction; durable execution admission from approved decision evidence; acceptance of a native Cursor execution adapter against the existing lifecycle and merge policy.
MODIFIED: WI-REQ-005 and WI-REQ-026 bind identity and implementation evidence to the adopting project's repository. The protocol repository remains its own project. Existing lifecycle, approval, one-writer, review, verification, retry, merge and convergence semantics remain binding.
REMOVED: none
Impact: Project state, bootstrap entry point/templates, existing preflight/approval/merge/workflow mechanisms, and acceptance fixtures. No existing project migration, runtime activation, paid commitment, or implementation is authorized by this package.
Alternatives material to the decision: Keeping project content in the protocol repository conflicts with the approved direction. A second state service or custom agent coordinator would duplicate the accepted control plane. Existing project-local state and native Cursor execution are the selected approach.
Open questions / risks: Native concurrency, selected Grok model availability, same-branch repair, and conditional merge capability require execution-environment proof before activation. Cursor cloud usage requires a separately approved spending limit if it creates a new cost commitment.
Jake decision: approved 2026-10-01 by Jake for implementation of the promoted Change/Spec package
Approved content: e2d527fc25f6de67e4dd5410a64ac95087bc6855
Spec path: specs/008-project-bootstrap/spec.md
Next lifecycle state / owner: Implement / IMPLEMENTER

Jake approved the promoted package for implementation on 2026-10-01. That approval does not create a Cursor Automation or any new paid commitment, and it does not promote the project baseline before convergence.

## Evidence and repository grounding

Inspection date: 2026-10-01, Asia/Shanghai. GROUNDING_CORRECTION against the 2026-09-30 review copy.

| Fact | Direct connector observation | Authority status |
| --- | --- | --- |
| Repository | jakeguo117/workspace-infrastructure-vnext; private | VERIFIED by origin URL, `gh repo view`, and `git ls-remote` |
| Configured default / target branch | main | VERIFIED |
| Observed remote main | 64c6acd4ec61896d1c4223e358df89b8019086b6, merge of PR 20 | VERIFIED by `git ls-remote origin refs/heads/main`. The review copy's e1857e12b6593658fa8aeac87260b3790b9e0cb9 is the earlier PR 17 merge. |
| Recorded project baseline | v0.2.0 | Unchanged in PROJECT_STATE.md |
| Recorded approved spec | specs/001-requirements-baseline/spec.md at 3c35008526bbdefa1ba84016f179867ad950feec | Blob 266ca73f9aca430312d006d40b3e9cc0d44d8313 is identical at that commit and at current main |
| Recorded implementation baseline | c20e07bf760a7b86a18492ec17a3a4f9344ccb35, content merge of PR 16 | Unchanged. It is an ancestor of origin/main and is not chased by this draft. |
| Recorded Active Change before capture | none; WI-CHG-0001 through WI-CHG-0007 closed/converged | Observed in PROJECT_STATE.md |
| Next change id | WI-CHG-0008 | No specs/008, branch, or pull request reserved it before this capture |
| Open pull request left untouched | PR 19, “Explain the repository in the README”, draft, head 0dc0232b511c00f2905a8a57bd90342d7ec10f54 | This package does not edit README |
| Local execution checkout | /Users/jake/Developer/workspace-infrastructure-vnext on main, clean, HEAD equal to origin/main 64c6acd4ec61896d1c4223e358df89b8019086b6 | VERIFIED before this branch was created |
| Workflow / lifecycle | docs/authority-graph.json role workflow-lifecycle, folder 1Zf8f97TnX_KCdGd1S6iEVIxgjRCDutjg | identity=VERIFIED revision=VERIFIED against live Drive metadata |
| Architecture baseline | docs/authority-graph.json role architecture, file 16XTL42-4Kkcq42TnLlcD-9USOaN9SP-E | identity=VERIFIED revision=VERIFIED against live Drive metadata. Body not copied into Git. |
| Authority check | `python3 scripts/wi_authority_check.py --check --observation <live metadata> --require-verified architecture,workflow-lifecycle` | exit 0, authority-graph: ok |

Inherited requirement text WI-REQ-001 through WI-REQ-030 matches the current approved spec except the stated WI-REQ-005 and WI-REQ-026 repository-binding sentences.

Repository state: verified for this capture.
Planning Gate for an implementation plan: not used. This pass stops before a plan, tasks, or implementation.
Implementation: not started.

## Minimum authoritative package

| File | Required action and authority |
| --- | --- |
| specs/008-project-bootstrap/change.md | This change record. Status is Approved. |
| specs/008-project-bootstrap/spec.md | Successor requirements candidate. Draft until Jake approves it and convergence accepts it. |
| specs/008-project-bootstrap/handoff.md | Admitted with this capture. Next bounded action is Jake's decision. |
| PROJECT_STATE.md | Active Change set to WI-CHG-0008. v0.2.0, the current approved spec, and the recorded implementation SHA stay unchanged. |
| specs/001-requirements-baseline/spec.md | Not edited. A supersession pointer belongs only to later convergence. |

No separate PRD, architecture document, decision database, execution-request database, or project registry is created.

## Implementation boundary

spec.md names the required behavior and existing mechanisms to reuse. A file-level implementation plan and task list are not produced in this pass.

One approved change is sufficient. Two sequential implementation checkpoints remain materially useful after Jake approves the package:

1. Project-local contract, detection, bootstrap, preflight, decision admission, and deterministic gate fixtures.
2. Native Cursor execution adapter and its live, bounded end-to-end acceptance.

The second checkpoint depends on the first. This is one workstream and one Active Change, with no parallel state system. Both checkpoints are inside the approved contract. Cursor Automations are not created.

Final status: Approved for implementation on 2026-10-01. Cursor Automations and any new paid cloud commitment remain unauthorized.

## Cost authorization for Case 13

Jake authorized on 2026-10-01 the minimum native Cursor Cloud Agent execution for this bounded Case 13 acceptance run, using included usage. This authorization does not upgrade a plan, buy an add-on, create a fixed monthly commitment, or create a standing Cursor Automation. It does not promote the project baseline.
