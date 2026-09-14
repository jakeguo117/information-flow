---
name: intake
description: Daily DigitalBrain content intake. Sync YouTube likes, write today's Digest from Snipd/WeRead/likes, refresh this week's Journal Brief. Use when Jake says 「跑 Digest」「每天摄入」「同步点赞」or /intake. Does not write Journal.
---

# intake

信息流。周记 skill 不开也要跑。不要救 Hermes。不要写 `📝 Journal/`。

## 跑什么

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

或 `scripts/run_digest_jobs.sh`。launchd `com.jake.journal-daily-digest` 每天 21:00 调这个。

## 写出

- `📋 Digests/{YYYY-MM-DD}-Digest.md`
- `📊 Journal Briefs/{YYYY}-W{nn}.md`
- `📥 Inbox/YouTube-Likes/{日期}-{video_id}.md`

YouTube token 在 iCloud `.secrets/youtube/`。缺 token 先跑 `scripts/youtube_oauth.py`。Whisper 模型在 plugin `models/`，不进 git。

空天跳过日 Digest。不要覆盖非 `journal-daily-digest` / `journal-weekly-rollup` 生成的文件。
