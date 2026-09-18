# information-flow

Jake only. Daily content in, weekly journal out.

## Skills

- `intake` — 21:00: YouTube likes + Snipd/WeRead → `📋 Digests/{YYYY-Wnn}/intake.md`
- `journal` — on demand: discuss the week, then write `📝 Journal/`

YouTube / weekly `intake.md` append runs on GitHub Actions (12:00 and 21:00 Shanghai). Snipd and WeRead have no cloud API: launchd `com.jake.intake-source-push` runs `scripts/push_intake_sources.sh` at login and every 4 hours while the Mac is on, and pushes only those two trees to DigitalBrain `main`. It never runs `journal`. `com.jake.journal-daily-digest` stays unloaded.

## Runtime (not in git)

- `models/ggml-small.bin` — Whisper fallback
- `state/` — logs
- YouTube OAuth: iCloud `.secrets/youtube/`

## Vault

DigitalBrain is a separate private repo. This plugin does not commit the vault.
