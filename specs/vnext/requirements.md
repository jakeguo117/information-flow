# Ported VNext engineering requirements

Source of the inherited wording: `specs/008-project-bootstrap/spec.md` at `c99355daf4889148dc517704bb6423de221d0770` for WI-REQ-001–034, and `specs/009-strategy-execution/spec.md` at the same SHA for WI-REQ-035–039. Spec 008 is the successor of spec 001; spec 001 stays the readable predecessor in the VNext archive and is not copied here because its normative bodies are the pre-successor text.

Business authority stays AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001. This file does not adopt VNext baseline v0.3.0, implementation SHA `b9e339f65a718a00121842e531632c5c2e34e904`, or WI-CHG-0009 status. It grants no standing Git merge, push, or write. It does not define a `continue_project` caller.

Conflicting requirement bodies are not copied. Each one is a stub that points at `docs/vnext-port/CONFLICTS.md`.

## Annotations applied to otherwise faithful sections

- WI-REQ-001: uniqueness here is the engineering spec in Git. Business Current Approved Truth remains AIC-DOC-REQ@0.1.1.
- WI-REQ-005: the exact-SHA rule is kept. The sentence that pins the protocol repository to `workspace-infrastructure-vnext` is not kept. AIC engineering repository is `jakeguo117/information-flow`. No VNext SHA is the AIC baseline.
- WI-REQ-018: remote Git state is implementation truth. Grok readback in WORKFLOW 6.2.7 counts. The Cursor-only read monopoly is not kept.
- WI-REQ-020: Git is authority for an engineering spec after capture. Drive remains the business-document authority (REQ-003).
- WI-REQ-026: mutating actions name `jakeguo117/information-flow` and the expected SHA. The VNext exclusion of information-flow is not kept.
- WI-REQ-027: phase, version, change id, and SHA stay distinct. AIC change ids are `AIC-CHG-*`. `WI-CHG-*` ids are historical VNext identifiers and are not reopened here.
- WI-REQ-034: capability and gate rules are kept. The conditional-merge grant is not kept.
- WI-REQ-037 and WI-REQ-038: durable escalation and resolution records are kept. Webhook wake-up and automatic resume transport are not kept and are not a `continue_project` caller.

## Requirements

### WI-REQ-001 — Current Approved Truth is unique

Engineering note: the paragraphs below keep the VNext engineering-spec uniqueness rule. They do not replace AIC-DOC-REQ@0.1.1 as business Current Approved Truth, and they do not adopt a VNext baseline SHA.

- Problem: Agents otherwise treat a draft, a chat, and a merged branch as equally current.
- Normative requirement: For the engineering spec captured in Git there is exactly one current approved engineering spec. Business Current Approved Truth remains AIC-DOC-REQ@0.1.1 under AIC-APR-0001. For this project there is exactly one current approved engineering spec. It names the approved requirement baseline, its version, and, once the spec is in Git, the Git reference of that baseline. It changes only when an approved change has been verified and converged.
- Rationale: The charter’s first problem is knowing what is approved now.
- Acceptance criteria: A preflight can point to one current baseline. Two unmarked “current” specs fail the check. A draft in Drive or chat is not reported as current.
- Priority: Must
- Dependencies: WI-REQ-008, WI-REQ-020
- Evidence: Foundation 01; charter problem 1.
- Non-goal: A separate database of truth.

### WI-REQ-002 — Active Change is explicit

- Problem: Local edits and branches get mistaken for approved work.
- Normative requirement: An Active Change names its base Current Approved Truth, a stable change id, an owner, a workflow state, and the behavior it proposes to add, modify, or remove. A branch or pull request is the execution vehicle. It is not the approval.
- Rationale: Work must be reviewable against a pinned base.
- Acceptance criteria: Given a branch, a reader can find the change id and the base it started from, or the state is `NOT_VERIFIED`. An untracked local edit is not an Active Change.
- Priority: Must
- Dependencies: WI-REQ-001, WI-REQ-027
- Evidence: Foundation 01 four records.

### WI-REQ-003 — Change Delta is explicit

- Problem: Reviewers cannot see why a change exists or what it removes.
- Normative requirement: Every Active Change carries a Change Delta with WHY, ADDED, MODIFIED, REMOVED, and impact. Empty sections say none. The previous baseline text stays available while the delta is reviewed.
- Rationale: The old baseline must remain stable during review.
- Acceptance criteria: A reviewer can list added, modified, and removed intended behavior without inferring it from a code diff alone. Rejected deltas remain history.
- Priority: Must
- Dependencies: WI-REQ-002
- Evidence: Foundation 01 and template 11.

### WI-REQ-004 — Approved behavior keeps ancestry

- Problem: A requirement can change during implementation and erase the baseline it replaced.
- Normative requirement: The system supports this path: approved behavior A, implementation against A, a decision that behavior must become B, a controlled change, then a new baseline B. A and the delta stay recoverable after B is current.
- Rationale: Later agents must explain how the project arrived here.
- Acceptance criteria: After B is current, A is marked superseded by B and remains readable. B’s record links to the change that created it. Silent overwrite of A fails review.
- Priority: Must
- Dependencies: WI-REQ-001, WI-REQ-003, WI-REQ-011
- Evidence: Phase 0 instruction domain A; Foundation supersession rule.

### WI-REQ-005 — Implementation baseline is an exact Git revision

- Problem: “Main” is not precise enough to resume or review.
- Normative requirement: The implementation baseline of a declared repository names that repository, its explicit target branch, and the exact remote commit SHA. A human-readable version does not replace the SHA. For AIC engineering the declared repository is `jakeguo117/information-flow`. A VNext implementation SHA, including `b9e339f65a718a00121842e531632c5c2e34e904`, is not this project's baseline.
- Rationale: Git is the engineering record (REQ-003; WORKFLOW 6.2.6 Verified Baseline).
- Acceptance criteria: A handoff without a fresh remote SHA for any claimed code state is `NOT_VERIFIED`. The SHA matches a readback of the remote.
- Priority: Must
- Dependencies: WI-REQ-018
- Not imported: the VNext protocol-repo pin and any current baseline SHA. See CONFLICTS C-BASELINE and C-026.

### WI-REQ-006 — Execution state is readable

- Problem: Progress is claimed from memory instead of branch, pull request, review, CI, and merge evidence.
- Normative requirement: For the Active Change, the system can show whether a branch exists, whether a pull request exists, review result, CI result, and merge result, each as evidence or as `NOT_VERIFIED`.
- Rationale: The next legal action depends on those facts.
- Acceptance criteria: A status report distinguishes “no pull request was found on the remote” from “the pull request was not looked up.” CI that did not run is not reported as passing.
- Priority: Must
- Dependencies: WI-REQ-017, WI-REQ-018
- Evidence: Foundation 05.

### WI-REQ-007 — Next legal action is singular

- Problem: Agents invent the next step or skip a gate.
- Normative requirement: The current record states one next bounded action, its owner role, the evidence that will show it finished, and the condition that stops it. Missing required evidence blocks the forward transition.
- Rationale: Resume and standing execution both need a legal next step.
- Acceptance criteria: Two conflicting next actions, or a next action whose prior gate has no evidence, fail preflight.
- Priority: Must
- Dependencies: WI-REQ-009, WI-REQ-014
- Evidence: Foundation 02 STOP gate; template 10.

### WI-REQ-008 — Draft work is not authority

- Problem: Research, brainstorm, and chat get copied into the current spec.
- Normative requirement: Chat, agent memory, research, and candidate drafts may inform a decision. They become authority only through decision capture that records the problem, the base version, the alternatives that mattered, the Change Delta, Jake’s decision, the date, and an evidence link.
- Rationale: Otherwise yesterday’s conversation overrides the baseline.
- Acceptance criteria: A spec section with no decision record is not Current Approved Truth. A rejected alternative is stored as history and is not an instruction.
- Priority: Must
- Dependencies: none
- Evidence: Foundation 02; charter non-goals.

### WI-REQ-009 — Work follows a gated lifecycle

- Problem: Implementation starts before approval, or merge is treated as acceptance.
- Normative requirement: Engineering work moves only through these states, in order, unless a failure returns to the earliest affected state: Draft, Approved, Plan, Tasks, Implement, Review, Verify, Merge, Converge, New Baseline. Each exit requires the evidence in Foundation document 02. A failed check does not skip forward. Naming Merge as a lifecycle state is not a standing Git permission to merge, push, or open a pull request. See CONFLICTS C-015.
- Rationale: The charter’s path is approved intent, then reviewed and verified change, then a new baseline.
- Acceptance criteria: An implement action whose state is still Draft is rejected. A merge without review and verification evidence is rejected. Convergence that finds a gap reopens the smallest affected state instead of recording a new baseline.
- Priority: Must
- Dependencies: WI-REQ-007, WI-REQ-029
- Evidence: Foundation 02 lifecycle table.

### WI-REQ-010 — Three ways work may start

- Problem: A bug fix, a technical rewrite, and a behavior change get handled as the same kind of request.
- Normative requirement: The system distinguishes three entries. A bug under already approved behavior records observed versus approved behavior and repairs that behavior. A technical change records that user-visible requirements stay fixed. A requirement change enters decision capture and needs Jake’s approval before affected work continues.
- Rationale: Only the third kind changes Current Approved Truth.
- Acceptance criteria: A repair that changes an acceptance criterion is reclassified as a requirement change. A technical change whose spec text changed fails review.
- Priority: Must
- Dependencies: WI-REQ-003, WI-REQ-011
- Evidence: Foundation 02 three entry paths.

### WI-REQ-011 — Requirement changes stop affected work

- Problem: Coding continues against a spec that Jake has already changed.
- Normative requirement: If intended behavior, acceptance criteria, scope, or an approved constraint changes, affected implementation stops. The proposed delta is captured against the pinned base. Jake approves or rejects it. Approved work is replanned. Unaffected work continues only when its isolation is evidenced. A code change cannot redefine a requirement.
- Rationale: This is the A-to-B path in WI-REQ-004.
- Acceptance criteria: A pull request that changes approved behavior without a linked approved delta fails review. Rejected deltas leave the previous baseline in force.
- Priority: Must
- Dependencies: WI-REQ-008, WI-REQ-016
- Evidence: Foundation 01 requirement-change rule.

### WI-REQ-012 — Coordination is by role

- Problem: The workflow breaks when a vendor is replaced, or a tool login is treated as authority.
- Normative requirement: The system defines these roles, independent of vendor: SPEC_OWNER, PLANNER, IMPLEMENTER, REVIEWER, VERIFIER, RESEARCHER, and RUNTIME_OPERATOR. An assignment records the role, the bounded outcome, the input baseline, the permissions, and the output evidence. Jake remains the decision authority and is not one of these executor roles. No role inherits Jake’s decision authority.
- Rationale: The charter separates role from brand.
- Acceptance criteria: A workflow description that names a vendor as the meaning of a step, rather than as the current executor of a role, fails architecture review. Replacing the reviewer executor does not change the required review evidence.
- Priority: Must
- Dependencies: WI-REQ-017
- Evidence: Charter responsibility table; Phase 0 role list; Foundation 03.

### WI-REQ-013 — One writer for a target

- Problem: Concurrent agents overwrite the same files and leave uncertain state.
- Normative requirement: Each write target has one owner at a time. Parallel work requires independent file and requirement boundaries, one integrator, and one shared pinned baseline. Overlap stops until ownership is explicit.
- Rationale: Retries and handoffs are unsafe if two writers share a target.
- Acceptance criteria: Two Active Changes that both name the same requirement or file are rejected unless an integrator and the independence evidence are recorded.
- Priority: Must
- Dependencies: WI-REQ-002, constraint 5
- Evidence: Foundation 03 ownership rules.

### WI-REQ-014 — Durable handoff can resume the work

- Problem: Stopping an agent loses the only copy of what happened and what is next.
- Normative requirement: A handoff is a persisted record a new executor can preflight. It includes change id, workflow state, owner, completed action, evidence, the next bounded action, and the stop or escalation condition. It also includes the authority pointers, permissions, local and remote state or `NOT_VERIFIED`, and any idempotency keys already issued. The receiver repeats preflight and does not continue across unverified drift. A handoff grants no new permission.
- Rationale: Jake must not be the relay.
- Acceptance criteria: A new session with no prior chat can name the next action from the handoff and the authority records alone. A handoff whose remote SHA does not match a fresh readback stops.
- Priority: Must
- Dependencies: WI-REQ-005, WI-REQ-007
- Evidence: Charter problem 3; Foundation 03 and 11; filter F-02 and F-12.

### WI-REQ-015 — Standing Git execution is not imported

The VNext normative text granted routine branch, commit, push, pull request, merge, and convergence inside an approved change without a new approval at each transition.

That grant is not imported. See CONFLICTS C-015. In-boundary engineering detail that does not change product meaning is already covered by WORKFLOW 6.2.1 and 6.2.6. Git publish, merge, and push still need their own applicable authority (WORKFLOW roles; APR-0001 exclusions; HANDOFF@0.2.0).

### WI-REQ-016 — Jake approves only material decisions

- Problem: Either every keystroke waits for Jake, or agents change product meaning alone.
- Normative requirement: The system escalates only for a new product direction, a material requirement or scope change, a material architecture trade-off with no dominant option, a privacy or security semantics change, a new paid commitment, a destructive or irreversible action outside the approved workflow, a bypass of review or CI or verification, conflicting authoritative requirements, or unresolved material ambiguity. The escalation states the decision, the options, and the consequence. The stop text is `STOP — JAKE DECISION REQUIRED`.
- Rationale: Filter F-04. Ordinary file names, layout, and Spec Kit configuration are not escalations.
- Acceptance criteria: A routine test failure returns to repair. A request to buy a plan, delete history, or change an acceptance criterion returns to Jake. The escalation fits in one decision request.
- Priority: Must
- Dependencies: WI-REQ-015
- Evidence: Foundation 02; Phase 0 decision boundary.

### WI-REQ-017 — Exclusive GitHub operator grant is not imported

The VNext normative text said Cursor performs every GitHub read and write, and other executors must not read or modify the repository.

That grant is not imported. See CONFLICTS C-017. Cursor is the engineering owner of a scoped task when that task authorizes the work (WORKFLOW 6.2.6). Grok must open the result (WORKFLOW 6.2.7). Git writes are not a standing permission.

### WI-REQ-018 — GitHub remote state is implementation truth

- Problem: Local commits and chat summaries get reported as merged.
- Normative requirement: Code, history, branch, pull request, review, CI, and merge state are true only as read from the GitHub remote of the declared repository. A local commit is not remote truth. After a mutation, readback includes the repository, branch, exact SHA, pull request state, and applicable check results. Grok's readback of an engineering result (WORKFLOW 6.2.7) is required evidence. This rule does not make Cursor the only party allowed to read GitHub.
- Acceptance criteria: A completion claim without that readback is not accepted. The readback SHA is the one stored in the handoff.
- Priority: Must
- Not imported: “true only as Cursor reads them” and the exclusive operator grant. See CONFLICTS C-017 and C-018.

### WI-REQ-019 — Linear projection is not imported

The VNext normative text made Linear the human projection.

That binding is not imported. See CONFLICTS C-019. AIC projection is Notion only (REQ-003; WORKFLOW “State, evidence and projection”; APR-0001). The six human questions are ported in `docs/vnext-port/projection.md`.

### WI-REQ-020 — One engineering spec; Drive keeps the business body

- Problem: Two editable copies both claim to be the current engineering spec.
- Normative requirement: Drive holds business documents, research, candidates, receipts, and history (REQ-003; APR-0001). Once an engineering spec is approved and captured in Git, that Git copy is the engineering authority (WORKFLOW 6.2.6). A Drive reading copy of that engineering spec is not a second editable engineering spec. If that Git spec and its Drive reading copy disagree, the affected action stops until the approved engineering source is identified. Business masters in Drive are not corrected “from Git” and are not projections.
- Acceptance criteria: Editing only a Drive reading copy of an engineering spec does not change the Git engineering spec. Editing Notion or a projection does not change Drive business authority.
- Priority: Must
- Not imported: “Drive becomes a pointer” for business documents, and the VNext foundation folder as workflow authority. See CONFLICTS C-020 and C-GRAPH.

### WI-REQ-021 — Recovery, retry, idempotency, stop, and reconciliation

- Problem: A crashed run repeats a pull request, loops on the same failure, or continues from a guessed state.
- Normative requirement: An interrupted run resumes from the last durable handoff and any persisted workflow progress. Retry applies only to transient failures, with a finite budget, and only after checking whether the intended effect already exists. The same change id and expected base must not create a second pull request, milestone, or version. Identical repeated failures, permission ambiguity, source conflict, or an exhausted budget stop and escalate. Reconciliation compares the surfaces that claim the same fact and corrects the non-authoritative one.
- Rationale: Filter F-05 and F-06; Foundation 03.
- Acceptance criteria: Replaying a completed pull-request creation finds the existing pull request and does not open another. A third identical failure stops. An unknown remote state stays `NOT_VERIFIED` rather than being repaired by assumption.
- Priority: Must
- Dependencies: WI-REQ-014, WI-REQ-018
- Evidence: Foundation 03; AEL acceptance tests for duplicate events, retained only as the need.

### WI-REQ-022 — Jake can see status in one scan

- Problem: Status is scattered across chats and internal state names.
- Normative requirement: One human-readable header shows the approved baseline, the active change, how far implementation has gone, the blocker, the next action, and whether a Jake decision is needed. Unknowns stay `NOT_VERIFIED`.
- Rationale: Charter observable success and Foundation template 10.
- Acceptance criteria: The header answers those six questions without opening a log. Elapsed time does not upgrade `NOT_VERIFIED`.
- Priority: Must
- Dependencies: WI-REQ-001, WI-REQ-002, WI-REQ-019
- Evidence: Foundation 10.

### WI-REQ-023 — No unapproved paid or destructive action

- Problem: Automation upgrades a plan, spends money, or destroys history to finish a task.
- Normative requirement: The system does not upgrade a paid plan, create a recurring paid commitment, or perform an unapproved destructive or irreversible external action. Those are Jake decisions. Branch protection being unavailable on the current private plan is a recorded limit, not a reason to buy GitHub Pro or to make the repository public.
- Rationale: Foundation 05 cost boundary; verified GitHub 403 on protection and rulesets during this run.
- Acceptance criteria: A blocked protection API returns a recorded limit and a procedural merge gate. It does not trigger a plan purchase. Force-push, history rewrite, and deletion of an approved baseline are refused without a specific Jake approval.
- Priority: Must
- Dependencies: WI-REQ-016
- Evidence: Foundation 01; GitHub API 403 this run.

### WI-REQ-024 — Records do not contain secrets

- Problem: Credentials leak into specs, issues, and handoffs that many agents read.
- Normative requirement: Secrets, credentials, and private tokens are not written into specifications, handoffs, pull request text, Linear text, or Drive project records.
- Rationale: Filter F-09.
- Acceptance criteria: A review that finds a credential in those surfaces fails. The fix removes the secret from the record and does not quote it back into the handoff.
- Priority: Must
- Dependencies: WI-REQ-016
- Evidence: AEL 06 §16, retained as the need; Foundation evidence rules.

### WI-REQ-025 — Review and verification name the revision

- Problem: A pass on an old commit is applied to a newer commit.
- Normative requirement: A review result and a verification result each name the exact revision they judged. A later commit invalidates that result for merge purposes until the affected review or verification is repeated. The implementer does not mark an uncertain result verified.
- Rationale: Filter F-03 and F-08.
- Acceptance criteria: Merge is refused when the pull request head SHA differs from the SHA on the passing review and the passing verification. A self-declared pass without command output or readback fails.
- Priority: Must
- Dependencies: WI-REQ-005, WI-REQ-009
- Evidence: Foundation 11 templates C and D; PR #7 lesson retained as provenance integrity.

### WI-REQ-026 — Actions name the declared repository

- Problem: Tooling falls back to another repository that happens to be checked out.
- Normative requirement: Every mutating action names the declared repository and the expected remote SHA. For AIC engineering that repository is `jakeguo117/information-flow`. No action may silently substitute another repository, including `workspace-infrastructure-vnext`. If the authenticated repository, visibility, branch, SHA, or working tree differs, the action stops. There is no default repository. Private visibility stays private unless Jake decides otherwise.
- Acceptance criteria: A preflight pointed at a different repository or a different SHA performs no write.
- Priority: Must
- Not imported: the sentence that VNext is not a continuation of information-flow. See CONFLICTS C-026.

### WI-REQ-027 — Four identifiers stay distinct

- Problem: A phase name, a release number, a change, and a commit get used as if they were the same fact.
- Normative requirement: Phase names the work stage. A project version does not replace a Git SHA. A change id names one controlled delta and is not a SHA. A document version is separate again. AIC change identifiers use the `AIC-CHG-` scheme already used by AIC-CHG-0001. Historical `WI-CHG-` identifiers are VNext history and are not reopened as AIC changes. A version number does not claim deployment.
- Acceptance criteria: A record can show a phase, a document version, no active AIC change, and a SHA at the same time without treating them as one identifier.
- Priority: Must

### WI-REQ-028 — Unknown stays unknown

- Problem: Missing evidence is filled in from memory, habit, or elapsed time.
- Normative requirement: Unknown, stale, or conflicting state is `NOT_VERIFIED`. It is not upgraded by time, by a Linear status, by chat, or by assuming a directory is empty. The record names the missing proof.
- Rationale: Foundation 03 and 10.
- Acceptance criteria: A field upgraded without a cited source fails preflight. A conflict records both observations and does not pick one silently.
- Priority: Must
- Dependencies: WI-REQ-018
- Evidence: Foundation 10.

### WI-REQ-029 — Verification is independent of the claim

- Problem: The same actor writes the code, announces success, and records the new baseline.
- Normative requirement: Review findings return to the implementer for repair. The verifier reruns the affected proof. Review, repair, and verify repeat until the result passes or a stop condition is reached. No agent marks its own uncertain result verified by assertion. Merge evidence and the new-baseline decision are separate.
- Rationale: Filter F-03; Foundation 02 and 03.
- Acceptance criteria: A change whose only proof is the implementer’s summary stays unverified. After merge, Current Approved Truth changes only when convergence matches the approved intent to the remote result.
- Priority: Must
- Dependencies: WI-REQ-009, WI-REQ-025
- Evidence: Foundation 02 Converge and New Baseline rows.

### WI-REQ-030 — Projection and history are not second truths

- Problem: Linear, Drive copies, and old baselines compete with the approved spec and the remote commit.
- Normative requirement: Each fact has one authority, defined by the source-of-truth policy. History is retained and is not current. Projections are corrected from the authority. Agents do not introduce another canonical copy of requirements, code, or run state.
- Rationale: Foundation 01; the legacy coordinator duplicated work state and is dropped.
- Acceptance criteria: Architecture review can point to one authority for requirements, one for implementation, one for an in-flight workflow run, and one human projection. A second orchestrator or a second current spec fails that review.
- Priority: Must
- Dependencies: WI-REQ-001, WI-REQ-018, WI-REQ-019, WI-REQ-020
- Evidence: Foundation 01; filter F-15.


## Added requirements

### WI-REQ-031 — VNext protocol enrollment is not imported

The VNext normative text required an adopting repository to pin an immutable VNext protocol release in its own PROJECT_STATE.md.

That enrollment is not imported. See CONFLICTS C-031. information-flow is the AIC code repository. It is not enrolled as a second VNext project and it does not receive a VNext baseline.

### WI-REQ-032 — Bootstrap that writes enrollment is not imported

The VNext normative text defined VNEXT_INITIALIZED detection and a bootstrap that writes protocol records before implementation.

The writer is not imported. See CONFLICTS C-032. Reconstruction of approved version, state, and next action is covered by WORKFLOW 6.2.5–6.2.6. Rules that relate to `continue_project` are mapped in `docs/vnext-port/RULE-MAP.md` and do not add a caller. `scripts/continue_project.py` is unchanged.

### WI-REQ-033 — Approved decision precedes execution admission

A material decision becomes executable only after its exact delta, pinned base, Jake approval evidence and bounded execution authority are persisted in the project's Change/Spec/handoff records. Chat content and a launch event alone are insufficient.

The approved Active Change may direct implementation while the old Current Approved Truth remains current pending convergence. Approval of the change does not prematurely promote the project's new baseline.

Admission verifies the current approved decision, intended requirements, scope, plan/tasks, permissions, ownership, finite budgets and applicable preflight. Execution receives durable references and identifiers, without requiring Jake to relay conversational history.

### WI-REQ-034 — Native execution bookkeeping is not authority

- Normative requirement: An execution adapter's event or run state is bookkeeping. It does not replace Git engineering authority, Drive business authority, or the accepted lifecycle. Routine defects return to bounded repair or retry. Review and verification are independent of implementation and assess the current exact head. A passing prompt, a vendor approval tool, a previous CI success, or a previous head result cannot authorize merge. A material issue stops affected work and uses `STOP — JAKE DECISION REQUIRED`. A capability that is unavailable or unproved stays `NOT_VERIFIED` and does not justify another orchestrator or a weaker gate.
- Not imported: “Cursor invokes the authoritative deterministic merge gate” as a standing merge right, and any webhook caller. See CONFLICTS C-015 and C-037.
- Priority: Must

### WI-REQ-035 — Minimum durable Execution Brief

Every admitted Strategy decision has one current Execution Brief in the existing per-change handoff, referencing approved Change/Spec/decision records rather than duplicating requirement prose. The handoff may contain an `execution_brief` section; a new standalone brief database/manifest is unnecessary. The minimum contract is:

| Fact | Required value / validation |
| --- | --- |
| Project identity | `project_id`, repository, explicit target branch, and the identity of the approved authority the reader must recover. The VNext authority-graph file and a VNext protocol enrollment are not that identity. See CONFLICTS C-GRAPH and C-031. |
| Change and base | `change_id`, immutable approved-base spec/commit, change ref and expected record revision. |
| Approved intent | Objective, exact requirement/decision identity, approved spec revision/content hash and acceptance-criteria references. |
| Limits | Constraints, non-goals, approved architecture identity, permitted actions/targets, material escalation boundaries and cost authority. Explicit none is distinct from unknown. |
| Approval | `decision_id`, explicit Jake approval evidence/actor/time, approved content identity, scope and authority grant. A fabricated agent claim is not approval evidence. |
| Correlation | Logical execution identity if allocated, parent escalation/resolution identity if resuming, and stable idempotency/effect key. |
| Legal entry | Plan, replan or a validated retained plan; the one next action and stop conditions. |

GPT must not supply file lists, implementation steps, technical decomposition or test implementation as a prerequisite. Cursor supplies those after grounding. The initial brief's allowed targets may therefore be a semantic boundary; precise file ownership must exist before implementation.

### WI-REQ-036 — Cursor owns engineering planning and in-boundary acceptance

After a planning signal is received, Cursor must, in order:

1. Authenticate the delivery's source/declared repository and read current durable state independently. Check the hinted decision against the currently approved decision; allocate/reuse correlation and acquire the existing single-writer ownership.
2. Verify repository root/origin, target branch/baseline, exact local/remote revisions, detached/dirty/staged/untracked state, unpushed/ahead/behind status and authority identities. Run applicable preflight; preserve user work and stop on unverified drift.
3. Inspect actual project files, functions, tests, configuration and structure. Before proposing ADD, search exact names, likely paths and equivalent behavior. Record a Verified Baseline in the plan.
4. Produce `plan.md` and `tasks.md` using the existing Cursor/Spec Kit planning path. Map approved criteria to observed code and planned proof; state owners, write scope, dependencies, permissions, finite budgets and stop conditions.
5. Validate the plan against current approved requirements, acceptance criteria, architecture, action permissions, security/privacy semantics, non-goals and cost bounds. Persist the validation result against the exact decision/spec/plan identities.

If every predicate is satisfied, persist `PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE` and admit implementation without another Jake approval. This is an admission result, not a new workflow state, not a waiver of any later gate, and not a Git merge, push, or pull-request grant. Unknown predicates cannot yield that result. See CONFLICTS C-015.

Cursor chooses files/modules, sequence, internal technical structure, tests, reuse, bounded decomposition and routine technical trade-offs. A material departure uses WI-REQ-037. A failing technical check returns to the existing repair path; it does not amend approved intent.

### WI-REQ-037 — Durable material escalation stops affected work

- Normative requirement: On a material issue, affected work stops. A bounded immutable escalation record is persisted in the change's evidence. No affected implementation proceeds while it is unresolved. Unaffected work continues only when its isolation is evidenced (REQ-008; WI-REQ-013).
- Escalate at least for requirement or acceptance changes, product direction, architecture outside approval, conflicting authorities, new paid commitments, security or privacy or permission semantics, destructive or irreversible actions outside approval, inability to meet intent without changing it, and exhausted finite retry bounds.
- General stop text: `STOP — JAKE DECISION REQUIRED`. Cost stop text: `STOP — JAKE COST APPROVAL REQUIRED`.
- Minimum record fields: project id; repository; change id; escalation id; triggering decision id; record revision; observed problem; approved intent; evidence pointers; options and consequences; recommendation or explicit none; exact next legal action; stopped scope; consumed budgets; resolution status.
- The problem, evidence, options, and next action stay bounded. Do not copy full logs or chats. A duplicate observation reuses the same unresolved escalation. A distinct material question gets a distinct id.
- Not imported: automatic webhook or GPT wake-up, and any `continue_project` caller. Settled resume entry is a new GPT conversation with the project name or link only, plus Grok reading the same approved version (owner decision 2026-10-08; WORKFLOW 6.2.5). See CONFLICTS C-037.
- Priority: Must

### WI-REQ-038 — Durable resolution keeps ancestry

- Normative requirement: Jake's response is a new immutable decision record B linking the specific unresolved escalation, preceding decision A, the approved base, the new approved content or delta, the evidence, and `resolution = approve | reject | defer | cancel`. A, the escalation, the options, and consumed budgets stay recoverable.
- Only an explicit valid approval permits affected work to continue. Reject, defer, and cancel stay stopped or terminate as recorded. Timeout or silence is not approval. A later approve does not reactivate a terminally closed escalation.
- A new independent product outcome is a new change. It does not silently replace the previous approved behavior (WI-REQ-004; constitution principle I as ratified on main).
- B invalidates affected review, verification, and CI evidence. The exact-head rule remains. A resolution does not bypass a gate and does not reset repair budgets unless the decision explicitly says so.
- Not imported: automatic resume transport, webhook dispatch, and the WI-CHG-0009 status that pull request 25 stays open. See CONFLICTS C-037. The in-flight “same change id” amendment from 009 is discussion history and is not an AIC active-change status.
- Priority: Must

### WI-REQ-039 — Durable correlation and at-least-once event safety

Use project/repository identity plus project-scoped `change_id`, immutable `decision_id`, `escalation_id`, logical `execution_id`, Spec Kit `workflow_run_id`, vendor invocation `run_id`, and stable operation idempotency keys. Thread/chat IDs and vendor event IDs are provenance/delivery metadata only.

A decision record includes a predecessor identity and exact content hash, not only a timestamp. `decision_id` is immutable and never reused for new intent. Resolution links must name the escalation and preceding decision explicitly. The current handoff selects exactly one approved decision; competing approved successors stop for reconciliation rather than picking the latest timestamp.

The canonical effect identity is the SHA-256 of `repository`, `project_id`, `change_id`, `authority_ref`, `decision_id`, `event_kind`, and `escalation_id` when that field is non-empty. `authority_ref` is the one durable reference in that tuple. For `strategy_approved`, `material_escalation`, and `strategy_resolved` it equals current approved content. For `capture_request` it may equal the approved base that already exists. There is no second base component beside `authority_ref`. The caller idempotency key is delivery metadata and is not part of the identity. Delivery retries reuse that identity; recording a new native run ID does not create a new logical execution. A material B can receive a new admission effect key without creating another change/PR/workflow lineage. Existing effect lookup and ownership enforce at most one mutating Cursor owner. GPT packet generation/capture likewise reuses decision/escalation keys and a single bounded Strategy owner.

Assume duplicate, delayed, lost and out-of-order deliveries. Consumers compare hints with current durable state; a duplicate returns the existing result/ack, a superseded decision is a no-op, an unseen/future or conflicting reference stops for bounded reconciliation, and closed/cancelled changes never restart. If an old event wakes a consumer after B exists, it may reconcile to B only by rereading current state and admitting B under B's own key; it may not execute A. That sentence constrains a delivery that already happened. It does not authorize a webhook or a `continue_project` caller.

Persist pending/acknowledged transport effects in existing per-change handoff/evidence, separate from legal lifecycle state. A send success is not proof of consumer execution. Record consumer admission/checkpoint acknowledgments; bounded redelivery checks effects first. Crash after durable capture/before send, after send/before ack, and after an effect/before ack must recover without duplicate work. No new central queue/workflow database is created.

The remainder of `specs/009-strategy-execution/spec.md` after this requirement is not imported as a current rule. That remainder is the architecture amendment, the webhook/API transport table, the strategy-layer wake path, AC-01 through AC-16, the Definition of Done, and the Promotion boundary. Those sections grant standing Git writes, keep baseline v0.3.0, bind a Linear projection, exclude Information Flow, or define a webhook caller. See CONFLICTS C-015, C-017, C-019, C-026, C-037, C-BASELINE, and the 009-state exclusion. Durable record fields that do not grant those rights stay in WI-REQ-035 through WI-REQ-039. The normalized event shape used by `scripts/vnext/wi_event_check.py` remains historical reference material at `docs/vnext-port/historical/specs/009-strategy-execution/contracts/strategy-event.md`. It is not a `continue_project` caller.

## Inherited non-goals that are not imported

Spec 008 says to exclude Information Flow, Journal, and Digital Brain, and says VNext is not a continuation of information-flow. Those exclusions conflict with the 2026-10-08 owner decision and are not imported. See CONFLICTS C-026.

Spec 008 acceptance case 7 and the definition-of-done sentence that an operator conditionally merges are standing merge rights. They are not imported. See CONFLICTS C-015.
