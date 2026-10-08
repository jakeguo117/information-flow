<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Plan WI-CHG-0007 behavior B

Affected implementation against behavior A is stopped. The replanned files are docs/acceptance/fixture.md and docs/acceptance/bug-fixture.txt.

Behavior A remains readable in specs/006-acceptance-a/spec.md.

Checks:
- scripts/wi_acceptance_fixture_check.sh --expect B
- scripts/wi_approval_check.sh --check specs/007-acceptance-b/change.md
- scripts/wi_ancestry_check.sh --check specs/006-acceptance-a/spec.md specs/007-acceptance-b/spec.md "ACCEPTANCE_FIXTURE: behavior A is the current sentence."
