# information-flow

Jake only. Daily content in, weekly journal out, durable Cognition in DigitalBrain.

## Skills

- `intake` — resolve this week's `📋 Digests/{YYYY-Wnn}/intake.md` from the Shanghai date (portrait + old-thread echoes first; never dump the week). Intake items and concept cards are not Evidence.
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK. After a journal is written, hand off to `cognition` propose; journal never writes Cognition files.
- `cognition` — propose / promote / retrieve / revise Evidence, Belief, and Principle as Markdown (`schema_version: "1.1"`) under DigitalBrain `📖 Cognition/`. Human gate. Writes go through validator + write coordinator. Retrieval returns `found | no_match | partial | unavailable`.

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes — including Cognition **content** — are not rewritten.

Privacy: this public repo has schema, skills, tools, and synthetic fixtures only. Jake's real Cognition stays in DigitalBrain.

```bash
python3 skills/cognition/tools/validate_cognition.py --vault "$VAULT"
python3 skills/cognition/tools/retrieve_cognition.py --vault "$VAULT" --query "..."
python3 skills/cognition/tools/write_cognition.py create --vault "$VAULT" --payload FILE --approval FILE
```

## Skills

- `intake` — resolve this week's `📋 Digests/{YYYY-Wnn}/intake.md` from the Shanghai date (portrait + old-thread echoes first; never dump the week)
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes are not rewritten.

YouTube / weekly `intake.md` append runs on GitHub Actions (12:00 and 21:00 Shanghai). Snipd and WeRead have no cloud API: launchd `com.jake.intake-source-push` runs `scripts/push_intake_sources.sh` at login and every 4 hours while the Mac is on, and pushes only those two trees to DigitalBrain `main`. It never runs `journal`. `com.jake.journal-daily-digest` stays unloaded.

## Runtime (not in git)

- `models/ggml-small.bin` — Whisper fallback
- `state/` — logs
- YouTube OAuth: iCloud `.secrets/youtube/`

## Vault

DigitalBrain is a separate private repo. This plugin does not commit the vault.
