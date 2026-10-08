# VNext port

`jakeguo117/information-flow` is the AIC code repository. `jakeguo117/workspace-infrastructure-vnext` stays a read-only historical archive. This directory is the port of its rules.

## Authority order

1. AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001.
2. Ported engineering rules in `specs/vnext/` where they do not conflict with those documents.
3. Historical VNext files under `docs/vnext-port/historical/`. They are evidence of what VNext said. They are not the AIC baseline and they are not an acceptance result.

## What was inspected

- main `7168117db85befa4e9f36420d306c667ffc12cbf`
- `wi-chg-0009-strategy-execution` `c99355daf4889148dc517704bb6423de221d0770` (there is no branch named exactly `wi-chg-0009`)

## What was not imported

- The VNext baseline (v0.3.0 and implementation SHA `b9e339f65a718a00121842e531632c5c2e34e904`).
- WI-CHG-0009 execution state (`PROJECT_STATE.md`, DEC-0004, pull request 25, native-run status, review PASS, verification VERIFIED).
- Standing Git merge, push, or write permission.
- A `continue_project` caller imported from VNext. Related rules are mapped in `continue-project.md`. A later on-request wrapper lives in `continue-project-trackc.md`. It is not a webhook and it does not close R10-14.

## Where to read

- `AIC-EVT-VNEXT-PORT-INVENTORY-0001.md` — every file in the two trees.
- `CONFLICTS.md` — each withheld VNext rule, the approved section, and the resolution.
- `RULE-MAP.md` — every requirement row and the counts.
- `specs/vnext/requirements.md` — ported requirement text.
- `scripts/vnext/` — guard scripts. `self_check.sh` does not claim an AIC acceptance PASS.
