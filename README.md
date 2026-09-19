# information-flow

Jake only. Daily content in, weekly journal out.

## Skills

- `intake` — discuss this week's `📋 Digests/{YYYY-Wnn}/intake.md` (portrait + old-thread echoes first; never dump the week)
- `journal` — on demand: find echoes from recent journals / already-linked projects, then write `📝 Journal/` only after Jake says OK

Skill copies on DigitalBrain (`.cursor/skills/` + the AGENTS.md route block) are overwritten by `scripts/sync_digitalbrain_skills.py` when this repo's `main` changes. Existing notes are not rewritten.

YouTube / weekly `intake.md` append runs on GitHub Actions (12:00 and 21:00 Shanghai). Snipd and WeRead have no cloud API: launchd `com.jake.intake-source-push` runs `scripts/push_intake_sources.sh` at login and every 4 hours while the Mac is on, and pushes only those two trees to DigitalBrain `main`. It never runs `journal`. `com.jake.journal-daily-digest` stays unloaded.

## Runtime (not in git)

- `models/ggml-small.bin` — Whisper fallback
- `state/` — logs
- YouTube OAuth: iCloud `.secrets/youtube/`

## Vault

DigitalBrain is a separate private repo. This plugin does not commit the vault.
