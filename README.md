# information-flow

Jake only. Daily content in, weekly journal out.

## Skills

- `intake` — 21:00: YouTube likes + Snipd/WeRead → `📋 Digests/{YYYY-Wnn}/intake.md`
- `journal` — on demand: discuss the week, then write `📝 Journal/`

Launchd runs `scripts/run_digest_jobs.sh`. It never runs `journal`.

## Runtime (not in git)

- `models/ggml-small.bin` — Whisper fallback
- `state/` — logs
- YouTube OAuth: iCloud `.secrets/youtube/`

## Vault

DigitalBrain is a separate private repo. This plugin does not commit the vault.
