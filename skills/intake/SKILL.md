---
name: intake
description: Daily DigitalBrain content intake and discussion. Use when Jake says 「今天 Digest」「今天摄入」「跑 Digest」「同步点赞」or /intake. Discuss today's Digests. Does not write Journal.
---

# intake

信息流。周记 skill 不开也要跑。不要救 Hermes。不要写 `📝 Journal/`。

用户说「今天 Digest」或「今天摄入」时：读当天 `📋 Digests/`（和本周 `📊 Journal Briefs/`），跟他讨论，**不落周记**。

## 生成文件（只在本机）

若存在 `$HOME/plugins/information-flow/scripts/`（Mac 本机），可以跑：

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

或 `scripts/run_digest_jobs.sh`。launchd 每天 21:00 已在跑。

Cursor 云端 **不要**跑这些脚本（没有 vault 路径、没有 YouTube token、没有 Whisper）。只读仓库里已有的 Digest 来讨论。

## 写出

- `📋 Digests/{YYYY-MM-DD}-Digest.md`
- `📊 Journal Briefs/{YYYY}-W{nn}.md`
- `📥 Inbox/YouTube-Likes/{日期}-{video_id}.md`

YouTube token 在 iCloud `.secrets/youtube/`。缺 token 先跑 `scripts/youtube_oauth.py`。Whisper 模型在 plugin `models/`，不进 git。

空天跳过日 Digest。不要覆盖非 `journal-daily-digest` / `journal-weekly-rollup` 生成的文件。
