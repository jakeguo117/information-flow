# Conflicts between VNext and the approved AIC documents

Approved documents win. The conflicting VNext sentence is not imported as a current rule.

Pins:

- AIC-DOC-REQ@0.1.1
- AIC-DOC-WORKFLOW@0.2.0
- AIC-DOC-HANDOFF@0.2.0 (the approved payload; later envelopes do not replace it)
- AIC-APR-0001
- Owner decision 2026-10-08: `jakeguo117/information-flow` is the single AIC code repository. Journal formal entry is GPT Cloud Work. Project resume is a new GPT conversation with the project name or link only, plus Grok reading the same version.

VNext texts below are paraphrases of the rule that was withheld, with the file that held it. They are not restated as instructions to follow.

## C-BASELINE

- VNext: `PROJECT_STATE.md` at `c99355daf4889148dc517704bb6423de221d0770` sets Current Project Baseline v0.3.0 and Implementation Baseline `b9e339f65a718a00121842e531632c5c2e34e904` for `workspace-infrastructure-vnext`.
- Approved: HANDOFF@0.2.0, section “实施起点和验证边界”, says that SHA's baseline, 009 execution state, and Git standing permission are not imported. REQ-010 says old scan SHAs are historical, not a fresh baseline.
- Resolution: baseline not imported. WI-REQ-005 keeps the exact-SHA rule for whatever repository a task declares, and names information-flow, without adopting the VNext SHA.

## C-015 — standing Git permission

- VNext: WI-REQ-015 in `specs/008-project-bootstrap/spec.md` allows assigned agents, after approval of requirement, change, scope, plan, and gates, to branch, commit, push, open a pull request, review, repair, run CI, verify, merge, and converge without a new approval at each step. The change-lifecycle workflow step `merge` tells RUNTIME_OPERATOR to merge when durable proof succeeds. Spec 008 acceptance case 7 says the operator conditionally merges.
- Approved: APR-0001 excluded actions include stage/commit/push/PR/CI/merge. WORKFLOW “Roles and modules” says Git operations need their own applicable authority. HANDOFF@0.2.0 excludes Git standing permission. The 2026-10-08 decision repeats that exclusion.
- Resolution: the standing grant is not imported. `docs/vnext-port/workflows/change-lifecycle.yml` tells the operator not to merge. `scripts/vnext/wi_merge_gate.sh` and `wi_merge_if_head.sh` only refuse a mismatched head. In-boundary engineering detail that does not publish Git is already in WORKFLOW 6.2.1 and 6.2.6.

## C-017 — sole GitHub operator

- VNext: WI-REQ-017 and constitution principle II. Cursor performs every GitHub read and write. Other executors do not independently read or modify the repository. A non-Cursor SHA claim stays `NOT_VERIFIED` until Cursor reads it.
- Approved: WORKFLOW 6.2.6 makes Cursor the engineering owner of a scoped task. WORKFLOW 6.2.7 requires Grok to open the result and the evidence. Grok coordinates. Git writes still need applicable authority (C-015).
- Resolution: the exclusive read/write grant is not imported. Ported agents tell the reviewer and verifier to read the given head, and they do not forbid Grok readback.

## C-018 — only Cursor's read is implementation truth

- VNext: WI-REQ-018 says code and pull-request state are true only as Cursor reads them from GitHub.
- Approved: WORKFLOW 6.2.7. Grok must actually open the result. A Cursor completion reply is not that readback.
- Resolution: remote Git state remains implementation truth (REQ-003). The Cursor-only monopoly is not imported.

## C-019 — Linear versus Notion

- VNext: WI-REQ-019 and `docs/linear-projection.md` and authority-graph role `projection` bind the human projection to Linear project P-JAK-19.
- Approved: REQ-003. Notion is the operational projection. WORKFLOW “State, evidence and projection”. APR-0001 projection row is Notion page `3ef47497-0e40-816e-a7cb-dc602d9110f7`.
- Resolution: Linear is not imported as the AIC projection. The six human questions are in `docs/vnext-port/projection.md` for that Notion page. A projection badge is still not approval.

## C-020 — Drive as a projection

- VNext: WI-REQ-020 says that after an engineering spec is in Git, the Drive copy becomes a pointer or reading projection. `docs/reconciliation.md` says Linear and Drive copies are projections.
- Approved: REQ-003. The business document body is Drive. WORKFLOW says formal intended behavior and governance live in Drive, then scoped engineering capture moves engineering authority to verified Git. Notion is the projection. Obsidian holds Journal and Cognition.
- Resolution: the port keeps Git as authority for a captured engineering spec, and keeps Drive as authority for business documents and receipts. The sentence that Drive copies are projections is not imported.

## C-026 — repository identity

- VNext: WI-REQ-026 and spec 008 non-goals. The protocol repository is `jakeguo117/workspace-infrastructure-vnext`. VNext is not a continuation of `information-flow`. Information Flow is excluded.
- Approved: owner decision 2026-10-08. information-flow is the single AIC code repository, including later public status board and `continue_project` work. HANDOFF@0.2.0 repository locator is `https://github.com/jakeguo117/information-flow`.
- Resolution: ported rules name information-flow. The exclusion of Information Flow is not imported. VNext remains a read-only historical archive and was not modified.

## C-031 — protocol enrollment

- VNext: WI-REQ-031. A supported repository pins a VNext protocol release in PROJECT_STATE.md. The protocol repo is not that project's repo, but the contract is how a project is enrolled.
- Approved: information-flow is already the AIC engineering repo under the approved Drive documents. HANDOFF@0.2.0 says not to import the VNext baseline. Enrolling this repo would write that baseline and create a second project identity.
- Resolution: enrollment is not imported. `scripts/vnext/wi_bootstrap.py --apply` refuses to write.

## C-032 — bootstrap writer

- VNext: WI-REQ-032. Detect `VNEXT_INITIALIZED` and bootstrap protocol records before implementation.
- Approved: WORKFLOW 6.2.5–6.2.6 already require reading pinned versions and a Verified Baseline. The owner decision says not to invent a `continue_project` caller. Creating a second acceptance or enrollment project is out of scope.
- Resolution: the writer is not imported. Detection code is ported only as a guard that does not enroll this repository. Resume rules are mapped in `docs/vnext-port/continue-project.md`.

## C-GRAPH — authority pins

- VNext: `docs/authority-graph.json` current normative pins are spec 008 in the VNext repo, Drive folder `1Zf8f97TnX_KCdGd1S6iEVIxgjRCDutjg` as workflow-lifecycle, Drive file `16XTL42-4Kkcq42TnLlcD-9USOaN9SP-E` as architecture, and the VNext GitHub repo as implementation.
- Approved: workflow authority is AIC-DOC-WORKFLOW@0.2.0 (Drive file `1QvfW1FzzeaalkGXhcRGHTpVVGU0Jue5A`). Requirements authority is AIC-DOC-REQ@0.1.1. Implementation repo is information-flow. The VNext architecture file is not one of the four approved documents.
- Resolution: the JSON graph is not imported and is not a current AIC authority file.

## C-037 — resume transport

- VNext: spec 009 controlling clarification and WI-REQ-037/038. The primary production transport is a webhook or API event that wakes Cursor or GPT. Material escalation emits `material_escalation`. Resolution emits `strategy_resolved` and the same change resumes automatically.
- Approved: owner decision 2026-10-08. Project resume is a new GPT conversation with the name or link only, and Grok reads the same version. Journal entry is GPT Cloud Work. WORKFLOW 6.2.5 step 5: a notification locates the handoff; it does not copy a second requirements set. Product details for `continue_project` are still pending. This task says not to invent that caller.
- Resolution: durable escalation and resolution records are ported. The wake-up and automatic resume transport are not imported and are not implemented.

## C-ENGINE — Spec Kit as the business workflow

- VNext: constitution principle IV. Spec Kit is the workflow engine.
- Approved: AIC-DOC-WORKFLOW@0.2.0 is the business workflow. WORKFLOW 6.2.6 puts the technical spec and tasks in Git. It does not require Spec Kit, and it does not allow a second orchestrator.
- Resolution: Spec Kit files are ported under `docs/vnext-port/` as the engineering lifecycle engine VNext used. They are not installed as live `.cursor` skills and they do not replace 04.

## C-009-STATE

- VNext: at `c99355daf4889148dc517704bb6423de221d0770`, WI-CHG-0009 is APPROVED / PROMOTED, not on main, not closed. DEC-0004 withdraws DEC-0003. Pull request 25 may not merge. A native run may not start. Review PASS and VERIFIED are recorded for content SHA `755a0b3e72c2cae4682041760b551b182de5a364` and do not apply to that publication head.
- Approved: HANDOFF@0.2.0 and the 2026-10-08 decision. Do not import 009 execution state. Do not claim an acceptance PASS.
- Resolution: PROJECT_STATE.md, the 009 status files, the native acceptance package, and the PASS/VERIFIED records are not imported. No acceptance suite was run as an AIC acceptance check.

## Not a conflict

These VNext rules were ported because they match the approved documents or add an engineering guard the approved documents do not contradict: one active change, explicit delta, ancestry, exact SHA, draft is not authority, gated lifecycle except the merge grant, three entry kinds, stop on requirement change, one writer, durable handoff fields, material escalation to Jake, secrets, exact-head evidence, NOT_VERIFIED, independent verification, retry and idempotency, and the execution-brief fields minus the caller.
