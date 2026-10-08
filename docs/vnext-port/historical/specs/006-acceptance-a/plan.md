<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Plan WI-CHG-0007

Pinned base: v0.2.0, implementation baseline f9e720953521b5ba93046242932080112b73f7d7. Current remote main is read from GitHub and is not copied into that baseline field.

Files:
- docs/acceptance/fixture.md is the only fixture the implementer creates for behavior A.
- specs/006-acceptance-a/ holds the A record. It stays readable after B exists.

Checks:
- scripts/wi_acceptance_fixture_check.sh --expect A while A is current.
- Preflight must keep Phase 1, baseline v0.2.0, change WI-CHG-0007, and the pinned SHA distinct.

Stop if the diff touches specs/001-requirements-baseline/spec.md or a Foundation document.
