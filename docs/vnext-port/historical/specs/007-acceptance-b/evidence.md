<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# WI-CHG-0007 acceptance evidence

This file is evidence. It is not the Current Approved Truth.

| Test | Result | Evidence |
| --- | --- | --- |
| Preflight pass on v0.2.0 | PASS | `scripts/wi_preflight.sh --check` exit 0 at c30eff1, phase Phase 1, baseline v0.2.0, change none, sha f9e720953521b5ba93046242932080112b73f7d7 |
| Preflight negatives | PASS | Isolated clone. Wrong repo exit 1. Dirty exit 2. Malformed phase, SemVer, and change id exit 3. Missing SHA exit 3. Non-ancestor exit 4. Missing WI-REQ-030 exit 5. Missing handoff exit 6. Handoff SHA mismatch exit 6. |
| specify version | PASS | CLI Version 1.0.13 |
| specify init | PASS | `/tmp/wi-oat/init`, integration cursor-agent, not imported |
| Workflow validate | PASS | `scripts/wi_workflow_validate.sh` exit 0 |
| Jake gate resume | PASS | Run 9edb15f4 paused at jake-before-approved, resume stayed paused, approve completed `after` once |
| Jake gate reject | PASS | Run 28fb7699 aborted. Choice reject. |
| A to B | PASS | A commit 00e3386813ddf6c0f6bfd9251f75924ab63c82e7. B spec supersedes A. A sentence remains in specs/006-acceptance-a/spec.md |
| Review failure | PASS | CHANGES_REQUESTED for 07c6823ac41e7cc75beff82d64c34334472260a0. CI run 36726022911 failed: ACCEPTANCE_EVIDENCE missing |
| Repair same PR | PASS | 03fa9162ffd2b5c4ac4edc4eccb937d5c3577291 on pull request 16 |
| Stale review | PASS | Merge gate exit 1 when review sha was 07c6823 or 03fa916 and the head had moved |
| Verification failure | PASS | FAILED for f13db63d68db29fe4312f8b76858ef07e286b01b |
| Bug extension | PASS | slug acceptance-bug-fixture. Assess did not edit the fixture. Fix restored the approved sentence. Test result verified |
| Fresh review and verification | PASS | Both name f6b41350c070713f9c4edb93f39bb44a0c113f3c. CI run 36727275044 success on that SHA |
| PR reuse | PASS | `scripts/wi_pr_lookup.sh WI-CHG-0007` printed reuse for pull request 16 |
| Content merge | PASS | c20e07bf760a7b86a18492ec17a3a4f9344ccb35 |

speckit.converge appended no tasks. `specs/007-acceptance-b/tasks.md` was left unchanged.
