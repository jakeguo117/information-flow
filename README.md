# information-flow

Jake only. Daily content in, weekly journal out, durable Cognition in DigitalBrain.

## Skills

- `intake` — resolve this week's `📋 Digests/{YYYY-Wnn}/intake.md` from the Shanghai date (portrait + old-thread echoes first; never dump the week). Intake items and concept cards are not Evidence.
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

- `intake` — resolve this week's `📋 Digests/{YYYY-Wnn}/intake.md` from the Shanghai date (portrait + old-thread echoes first; never dump the week)
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes are not rewritten.

The previous Shanghai day's takeaway runs on GitHub Actions at 08:00 Shanghai: fetch YouTube likes, then write `📋 Digests/daily/YYYY-MM-DD.md`. The same job then runs `python3 scripts/build_weekly_digest.py --vault <vault> --also-previous`, which writes this ISO week and the previous week to `📋 Digests/{YYYY-Wnn}/digest.md` from those daily files (or that week's `intake.md` when no daily file exists). Snipd and WeRead are 可以引用的, YouTube is 值得讨论的, and X and Instagram are 可以借用的; that tag is written on the daily item. Anything else stays in 待分组. No real items means that week file is not written (exit 2). A generated file is refreshed on the next run only while its marker hash still matches and 「我的看法：」 is empty; a hand edit leaves the file in place (exit 3). The daily job continues on 2 and 3. `weekly-digest` builds one week on `workflow_dispatch`, and also when `.github/weekly-digest-request` is pushed to `main`. It tolerates exit 3 and commits that `digest.md`. It does not append weekly `intake.md`. Snipd and WeRead have no cloud API: launchd `com.jake.intake-source-push` runs `scripts/push_intake_sources.sh` at login and every 4 hours while the Mac is on, and pushes only those two trees to DigitalBrain `main`. It never runs `journal`. `com.jake.journal-daily-digest` stays unloaded.

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
