<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Acceptance fixture behavior B

Status: Approved inside WI-CHG-0007. This file is not the project Current Approved Truth.

## Current fixture

`docs/acceptance/fixture.md` must contain both lines:

`ACCEPTANCE_FIXTURE: behavior B replaced A.`

`ACCEPTANCE_EVIDENCE: present`

## Bug fixture

`docs/acceptance/bug-fixture.txt` must contain exactly `bug-fixture: approved behavior`.

A typo in that file is a defect against this sentence. Repairing the typo does not change this requirement.

## Ancestry

Behavior A stays in `specs/006-acceptance-a/spec.md`, marked superseded. It is not the current fixture sentence.
