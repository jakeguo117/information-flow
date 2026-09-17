---
name: intake
description: Weekly DigitalBrain intake.md and Yale-style discussion. Use when Jake says 「今天 Digest」「讨论 Digest」「今天摄入」「跑 Digest」or /intake. Appends reflection to this week's intake.md. Does not write Journal.
---

# intake

信息流。不要救 Hermes。不要写 `📝 Journal/`。不要写日子、日历、Reminders、保险交易。

## 每天生成（21:00 上海，GitHub Actions）

主文件是 **`📋 Digests/{YYYY-Wnn}/intake.md`**（一篇累积）。有新 Snipd / WeRead / YouTube 才 append。没新增不动、不写空文件。旧的日 Digest 不是入口。

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

Cursor 云端不要跑这些脚本。只读仓库里已有的 `intake.md`。

Vault：本机 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`；否则当前工作区根（须有 `📝 Journal/`）。

## 讨论（Yale 式，一次一问）

用户说「今天 Digest」「讨论 Digest」或 `/intake`：

1. 打开本周 `📋 Digests/{YYYY-Wnn}/intake.md`。先读 **Briefing**（只有未勾选）。需要原文再打开该条 wikilink 的 Snipd / WeRead / YouTube-Likes。
2. 一次只问一个问题。不宣讲整周清单，不堆 CRM 流水。
3. 可以把该条挂到 Linear issue 或笔记 wikilink。intake 里只加一行 `挂钩：[[笔记]]` 或 `挂钩：ABC-123`，不把 Linear/CRM 正文写进 intake。
4. 他说可以记下之后：
   - 该条改成 `[x]`，在该条下面 **append** 带引用的 reflection（wikilink 回来源）
   - 有引用的 reflection **同时**写成 `📖 Resources/concepts/{短标题}.md`
   - 没有引用的心情句、纯逾期任务不进 wiki
   - 然后可跑 `weekly_rollup.py` 让 Briefing 更新、`[x]` 沉底；人手改 checkbox 也可以，下次脚本会沉底

Resource 卡片模板：

```markdown
---
date: {YYYY-MM-DD}
type: concept
source_digest: "[[📋 Digests/{YYYY-Wnn}/intake]]"
---

# {短标题}

{几条带引用的结论}

## 来源
- [[{具体 Snipd/YouTube/WeRead/intake 条目}]]
```

Journal 只读本周 intake 里已经 `[x]` 的条目。
