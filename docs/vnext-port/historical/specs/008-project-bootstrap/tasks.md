<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Tasks WI-CHG-0008

- Owner: IMPLEMENTER. Record Jake's approval of commit 7a9ebbcff929ea52e7cad8373baaf518472ed669. Stop if the decision is missing.
- Owner: IMPLEMENTER. Add reusable detect and bootstrap commands. Stop if a script hardcodes this repository as the only project.
- Owner: IMPLEMENTER. Teach preflight, approval, admission, pull-request lookup, merge proof, retry bounds, and convergence to read the declared project. Stop if an existing acceptance fixture starts failing.
- Owner: IMPLEMENTER. Run scripts/wi_bootstrap_acceptance.sh on disposable repositories and on this checkout. Stop at STOP — JAKE DECISION REQUIRED when a bound is exhausted or a material conflict appears.
- Owner: RUNTIME_OPERATOR. Push this branch to pull request 21. Do not open another pull request.
- Owner: IMPLEMENTER. Pull request 21 is merged, so the Case 13 fixture uses branch wi-chg-0008-native-e2e. Add the marker, acceptance assertion, and CI step named by the handoff. Stop if the change would alter approved requirements or create a standing Automation.
