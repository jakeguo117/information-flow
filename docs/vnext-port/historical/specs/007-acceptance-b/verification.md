<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

change_id: WI-CHG-0007
sha: f6b41350c070713f9c4edb93f39bb44a0c113f3c
result: verified
evidence: scripts/wi_acceptance_fixture_check.sh --expect B exit 0; scripts/wi_preflight.sh --check exit 0; CI run 36727275044 success on this SHA
