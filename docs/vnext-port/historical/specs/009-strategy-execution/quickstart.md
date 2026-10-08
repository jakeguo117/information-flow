<!-- Ported from jakeguo117/workspace-infrastructure-vnext @ c99355daf4889148dc517704bb6423de221d0770 (branch wi-chg-0009-strategy-execution).
Historical VNext material. Not the AIC baseline. Not an AIC acceptance result.
AIC-DOC-REQ@0.1.1, AIC-DOC-WORKFLOW@0.2.0, AIC-DOC-HANDOFF@0.2.0, and AIC-APR-0001 win on conflict.
This port grants no standing Git merge, push, or write permission. -->

# Quickstart: WI-CHG-0009 guards

## Prerequisites

Repository checkout of `wi-chg-0009-strategy-execution`. Python 3. No cloud credential is required for these checks.

## Run

```bash
bash scripts/wi_strategy_acceptance.sh
bash scripts/wi_preflight.sh --check
bash scripts/wi_admit.sh --check specs/009-strategy-execution PROJECT_STATE.md
```

## Expected

`wi_strategy_acceptance.sh` prints `strategy-acceptance: ok`. Preflight passes on a clean tree whose handoff `expected_remote_sha` is still the implementation baseline `b9e339f65a718a00121842e531632c5c2e34e904`.

`wi_admit.sh` requires `plan.md` and `tasks.md`. It does not prove a native webhook or a GPT run.

## Not proved here

Do not POST a Cursor Automation webhook and do not start a GPT session from this guide. Included cloud allowance and a Strategy event consumer are `NOT_VERIFIED`.
