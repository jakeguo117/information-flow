# information-flow

Jake only. Daily content in, weekly journal out, durable Cognition in DigitalBrain.

## Skills

- `intake` — collect only, no discussion: Inbox originals stay as they are, and `📥 Inbox/_index/` gets one append-only line per Input. The weekly `📋 Digests/{YYYY-Wnn}/intake.md` is retired. 「看本周汇总」 goes to `digest`, which may read an existing Thursday archive snapshot `📋 Digests/cycles/{cycle_id}/r{n}.md`. Thursday cycle auto-run is stopped. Weekday 归堆 is `📋 Digests/cluster/YYYY-MM-DD.md` (想法梳理 writes it; a Cloud Agent pushes `jakeguo117/obsidian-digitalbrain`). Saturday `discuss-to-resources-ideas` is the weekly Resources / Ideas / Cognition extract. Intake items and concept cards are not Evidence. `📋 Digests/daily/` is not the 归堆 path. Takeaway is already offline; this change does not add a stop-cron and does not delete `scripts/daily_takeaway.py`.
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

- `intake` — collect only, no discussion; the weekly `📋 Digests/{YYYY-Wnn}/intake.md` is retired. 「看本周汇总」 reads an archive Thursday snapshot through `digest` when one exists. Thursday auto-run is stopped. Weekday 归堆 is `📋 Digests/cluster/`; Saturday `discuss-to-resources-ideas` does the weekly extract.
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes are not rewritten.

`daily-intake` runs at 07:30 Asia/Hong_Kong (cron `30 23 * * *` UTC) and can also be started by hand with `workflow_dispatch` (no inputs). It collects YouTube likes (since the last successful run, or yesterday in Asia/Hong_Kong) into DigitalBrain `📥 Inbox/YouTube-Likes/` and syncs skill copies. All three workflows check DigitalBrain out without a `ref`, so they read and push its default branch, which is `main`. It does not write a daily digest. Skill-file changes on `main` (or a manual `workflow_dispatch`) also run `sync-digitalbrain-skills`; it has no schedule, and its `TZ` is Asia/Shanghai, also UTC+8, used only for the date in its commit message. Snipd and WeRead still land from the local plugins; `com.jake.intake-source-push` pushes only `📥 Inbox/Snipd/` and `📥 Inbox/WeRead/` to DigitalBrain `main` at login and every 4 hours while the Mac is on. It never runs `journal`.

Thursday `weekly-digest` auto-run is stopped (Jake 2026-10-28 方案纸 v2). `.github/workflows/weekly-digest.yml` has no `on.schedule`. `workflow_dispatch` remains for an emergency cycle only: `stage` is `process` or `digest`, and `cycle_id` must be a Thursday `cy-YYYYMMDD`. An empty, malformed or non-Thursday `cycle_id` fails the job. A missing `📥 Inbox/_index`, or a missing or empty `inputs.jsonl`, logs 索引未建，跳过 and the job stays green. An emergency run still commits only `📋 Digests/cycles/{cycle_id}/` and `📥 Inbox/_index/` (the status lines `process_batch.py` writes), refuses any other staged path, and pushes to `obsidian-digitalbrain` `main`. Historical `📋 Digests/cycles/` stays archive. There is no Friday journal cron. This workflow does not write `📋 Digests/cluster/` or `📋 Digests/daily/`.

Weekday 归堆 is `📋 Digests/cluster/YYYY-MM-DD.md` (multi-day `YYYY-MM-DD_DD.md`, for example `2026-10-26_27.md`). 想法梳理 writes that file. 归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`. information-flow Actions do not write that vault path, and this change does not add the Cloud Agent wiring. Saturday, 想法梳理 loads `discuss-to-resources-ideas` and scans that week's `📋 Digests/cluster/` plus on-disk `📝 Journal/{YYYY-MM-DD}*.md`. That Saturday batch is the weekly Resources / Ideas / Cognition extract. Weekday cluster or journal 落盘 does not run it. `📋 Digests/daily/` is not taken over, and historical daily files are left alone. takeaway 已 offline，本 PR 不另挂停排程。`scripts/daily_takeaway.py` stays as dead code and is not deleted here. The 方案纸 originally named `📋 Digests/daily/` for 归堆; PM moved 归堆 to `cluster/` because that path belongs to the takeaway script. Jake can change that path later.

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
