# Journal pack (AIC-TASK-JOURNAL-PACK-0001)

Installable subset of `information-flow` for the first batch. It contains the journal skill, the journal confirmation tool, and the cognition skill/tools journal hands off to. It does not contain collectors, launchd, GitHub Actions, YouTube OAuth, or vault recovery.

This archive is not an installation. Unpacking it does not enable journaling, reminders, or schedules. Do not point it at a real DigitalBrain vault.

Journal files are written only by `skills/journal/tools/write_journal.py` after `confirmed: true` and phrase `可以写`, `写吧`, or `OK 写`. Cognition files are written only by `skills/cognition/tools/write_cognition.py` after a per-object approval. Reject writes nothing.

Synthetic inputs live under `tests/synthetic/journal_pack/`. Local checks are `python3 scripts/test_journal_pack.py`.

## ChatGPT upload ZIP

The cloud plugin is an uploaded ZIP, not a repo install. Build it from this repo:

```bash
python3 scripts/package_journal_pack.py --chatgpt-plugin
```

Output is `dist/information-flow-plugin.zip`. Every entry is timestamped 1980-01-01. The archive has `plugin.json` at the root and `.codex-plugin/plugin.json`. Both versions come from `.codex-plugin/plugin.json` in this repo. `packaging/chatgpt-upload/*.json` keeps the uploaded layout and is not itself packed. `dist/` is not committed.
