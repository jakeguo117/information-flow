<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# WI-CHG-0009 zero-cost capability probe

Date: 2026-10-02 Asia/Shanghai
Change: WI-CHG-0009
Method: public documentation and this repository's existing evidence. No automation was created, no cloud agent was started, no subscription was activated, and no webhook was sent.
Account check: the Cursor Automations UI was opened read-only. It returned no automation list, webhook URL, or spend limit. Jake's ChatGPT plan was not read.

| Capability | Result | Source and limit |
| --- | --- | --- |
| Cursor webhook intake | NOT_VERIFIED | Product: [Cursor Automations](https://cursor.com/docs/cloud-agent/automations) says a saved automation gets a private webhook URL and API key, and a POST starts a run. This account has no saved endpoint read back. Saving one would create an automation, which this probe does not do. |
| Automatic Cloud Agent start | NOT_VERIFIED | Product: the same page says a webhook POST starts a cloud-agent run. [Cloud Agents](https://cursor.com/docs/cloud-agent) also start from Desktop, Web, API, Slack, GitHub, or Linear. WI-CHG-0008 case 13 ran cloud agents `bc-fa58a215-90fc-40b3-a206-12383ef0161f` and `bc-81651fad-11b9-4af3-a5e1-07a3277b5170`. That is not a webhook-started run. This probe did not start one. |
| Expected-head conditional merge | PASS | GitHub `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` accepts `sha` and returns 409 when the head does not match ([REST pulls](https://docs.github.com/en/rest/pulls/pulls)). WI-CHG-0008 case 13 merged pull request 22 only while the remote head matched. This is the existing operator path. Cursor Automations do not document that guard, and this probe did not merge anything. |
| GPT inbound event and a real Strategy run from it | UNAVAILABLE | [ChatGPT scheduled tasks](https://learn.chatgpt.com/docs/automations.md) start a run from Gmail, Slack, or GitHub pull-request activity only. They do not document an inbound HTTP endpoint a Cursor automation can POST to. OpenAI staff said a native inbound webhook that starts a task is not supported ([Codex request, 2026-04-13](https://community.openai.com/t/feature-request-inbound-webhook-support/1378889)). A GitHub-event task would be the spec's fallback. A fallback-only trace fails AC-13. This account's plan eligibility was not read and stays NOT_VERIFIED. |
| Authenticated approval receipt | UNAVAILABLE | No Cursor or ChatGPT document describes a receipt that binds an authenticated person to the exact approved bytes. [ChatGPT Work admin FAQ](https://learn.chatgpt.com/docs/enterprise/work-admin-faq) says compliance logs do not establish a complete audit trail for every approval. An `actor: Jake` field is not that receipt. |
| Enforceable included-usage cap | NOT_VERIFIED | [Cloud Agents](https://cursor.com/docs/cloud-agent) bill at the model API rate and ask for a spend limit on first use. [Models and pricing](https://cursor.com/docs/models-and-pricing) draws included usage, then on-demand usage. A Cursor staff correction says a hard limit can block a start when less than about $2 of headroom remains ([forum](https://forum.cursor.com/t/what-is-the-pricing-structure-for-using-cloud-agents/156843)). This account's balance, on-demand switch, and hard limit were not read. An unknown cap blocks dispatch. |

Probe result: 2c. Neither the Cursor webhook path nor the GPT inbound path is proved. The GPT primary transport is a missing product capability, not an unread account setting.
