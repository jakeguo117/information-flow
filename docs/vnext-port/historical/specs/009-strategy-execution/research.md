<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Research: WI-CHG-0009

## Decision: Keep event admission in a repository script

- Decision: Add `scripts/wi_event_check.sh` beside the existing lifecycle scripts.
- Rationale: `scripts/wi_admit.sh` and `scripts/wi_preflight.sh` already decide admission from Git records. A normalized event only supplies identities those scripts can re-read.
- Alternatives considered: A hosted receiver or a second workflow engine. Rejected by constitution IV and the approved non-goals.

## Decision: Do not dispatch Cursor Automations in this pass

- Decision: Treat the documented Cursor Automation webhook as the approved future consumer, and do not save or call one now.
- Rationale: Cursor's automation documentation, fetched 2026-10-01 from `https://cursor.com/docs/cloud-agent/automations`, says webhook triggers exist and that automation runs are billed as cloud-agent usage. This account's remaining included allowance was not observed. Unknown allowance blocks dispatch. Saving an automation would also mint a webhook credential that this pass does not need.
- Alternatives considered: Start a cloud agent because WI-CHG-0008 used included cloud agents. That earlier allowance is not standing permission for WI-CHG-0009.

## Decision: Do not invent a GPT event endpoint

- Decision: Persist escalation records locally. Do not claim a Strategy wake-up.
- Rationale: The same automation documentation lists GitHub, webhook, Slack, Linear, Sentry, and PagerDuty triggers. It does not list a ChatGPT Work or Strategy event consumer. The spec forbids inventing that API.
- Alternatives considered: Computer Use driving the Cursor or GPT UI. Rejected as the production transport.

## Decision: Store effects in the change directory

- Decision: Append pending and acknowledged effects to a per-change effects file. Escalations use a per-change escalation record.
- Rationale: WI-REQ-039 requires pending and acknowledged effects without a new database. The change directory is already the record location.
- Alternatives considered: A shared queue. Rejected.
