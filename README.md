# information-flow

Jake only. Daily content in, weekly journal out, durable Cognition in DigitalBrain.

## Skills

- `intake` — collect only, no discussion: Inbox originals stay as they are, and `📥 Inbox/_index/` gets one append-only line per Input. The weekly `📋 Digests/{YYYY-Wnn}/intake.md` is retired; 「看本周汇总」 goes to `digest`, which reads the latest Thursday snapshot `📋 Digests/cycles/{cycle_id}/r{n}.md`. Intake items and concept cards are not Evidence.
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK. Persistent save goes through `write_journal.py`; without `可以写` / `写吧` / `OK 写` the tool writes 0 files. After a journal is written, hand off to `cognition` propose; journal never writes Cognition files.
- `cognition` — propose / promote / retrieve / revise Evidence, Belief, and Principle as Markdown (`schema_version: "1.1"`) under DigitalBrain `📖 Cognition/`. Human gate. Writes go through validator + write coordinator. Retrieval returns `found | no_match | partial | unavailable`.

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes — including Cognition **content** — are not rewritten.

Privacy: this public repo has schema, skills, tools, and synthetic fixtures only. Jake's real Cognition stays in DigitalBrain.

```bash
python3 skills/cognition/tools/validate_cognition.py --vault "$VAULT"
python3 skills/cognition/tools/retrieve_cognition.py --vault "$VAULT" --query "..."
python3 skills/cognition/tools/write_cognition.py create --vault "$VAULT" --payload FILE --approval FILE
python3 skills/journal/tools/write_journal.py save --vault "$VAULT" --approval FILE
```

## Skills

- `intake` — collect only, no discussion; the weekly `📋 Digests/{YYYY-Wnn}/intake.md` is retired, and 「看本周汇总」 reads the latest Thursday snapshot through `digest`
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes are not rewritten.

GitHub Actions `daily-intake` runs every day at 07:30 Asia/Hong_Kong (cron `30 23 * * *` UTC). It fetches YouTube likes since the date of the last successful run into `📥 Inbox/YouTube-Likes/`, commits only that folder to DigitalBrain `main`, then syncs the skill copies. It writes no daily takeaway and no weekly file. `weekly-digest` runs on Thursdays, Asia/Hong_Kong: at 08:00 `scripts/process_batch.py` takes every `pending`, `retry_pending` and `failed` item up to the cutoff into `📋 Digests/cycles/{cycle_id}/batch.json`, and at 20:00 `scripts/build_digest_v2.py` writes the Thursday snapshot `📋 Digests/cycles/{cycle_id}/r{n}.md`. `cycle_id` is `cy-YYYYMMDD` for that Thursday. `workflow_dispatch` takes `stage` (`process` or `digest`) and a required Thursday `cycle_id`; any other id fails the job. With no `📥 Inbox/_index/inputs.jsonl` it logs 索引未建，跳过 and stays green. It commits only that cycle folder and `_index`. `digest` and `journal` read the largest `r{n}` of this week's cycle and never fall back to `📋 Digests/daily/` or the old weekly files. Snipd and WeRead have no cloud API: launchd `com.jake.intake-source-push` runs `scripts/push_intake_sources.sh` at login and every 4 hours while the Mac is on, and pushes only those two trees to DigitalBrain `main`. It never runs `journal`. `com.jake.journal-daily-digest` stays unloaded.

ChatGPT upload ZIP (root `plugin.json`, `.codex-plugin/plugin.json`, skills, and the journal pack files, timestamps fixed at 1980-01-01):

```bash
python3 scripts/package_journal_pack.py --chatgpt-plugin
```

The file is `dist/information-flow-plugin.zip`. `dist/` is not committed.

Obsidian Git on the iCloud vault is pull-only. Plugins and skill copies land in that working tree before `HEAD` moves, and Git then refuses the whole fast-forward. `scripts/reconcile_live_vault_untracked.py` (on branch `cursor/cognition-v1.1`, not in this tree) clears incoming paths whose bytes already match, then fast-forwards. launchd `com.jake.digitalbrain-reconcile` is the Mac job for that script. This tree's `push_intake_sources.sh` does not call it. Keep or pause that job before switching the checkout to `main`: `docs/onboarding/local-switchover.md`.

## Runtime (not in git)

- `models/ggml-small.bin` — Whisper fallback
- `state/` — logs
- `config.json` in this plugin checkout (the directory that contains `scripts/`), or the absolute path in `INFOFLOW_CONFIG`. The checkout copy is gitignored. Copy `config.example.json` and replace every `REPLACE_WITH_` value. Scripts read `vault_root`, `git_remote`, `git_branch`, `storage_mode`, `git_user_name`, and `git_user_email` from that file. `INTAKE_GIT_USER_NAME` and `INTAKE_GIT_USER_EMAIL` override the two git identity fields when set. A missing value is an error. There is no built-in vault path.
- YouTube OAuth files stay outside this repo and outside the vault. `YOUTUBE_CLIENT_FILE` is the client JSON (`installed` or `web`, with `client_id` and `client_secret`). `YOUTUBE_TOKEN_FILE` is the token JSON (`youtube_oauth.py` writes it; it needs `refresh_token`). A shell profile is invisible to launchd. A job that runs `youtube_likes.py` needs both variables in that job's environment.
- Moving an existing Mac onto this config, including launchd reload and the `cursor/cognition-v1.1` reconcile job: `docs/onboarding/local-switchover.md`.

## Vault

DigitalBrain is a separate private repo. This plugin does not commit the vault.
