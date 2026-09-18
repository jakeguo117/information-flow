---
name: intake
description: Weekly DigitalBrain intake.md and Yale-style discussion. Use when Jake says 「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」or /intake. Appends reflection to this week's intake.md. Does not write Journal.
---

# intake

信息流。不要救 Hermes。不要写 `📝 Journal/`。不要写日子、日历、Reminders、保险交易。

## 硬路由（今天 Digest）

用户说「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」或 `/intake`：

1. 立刻打开本周 `📋 Digests/{YYYY-Wnn}/intake.md`。只读这一份。立刻用 **Briefing** 里第一条未勾选问一句（Yale 式，一次一问）。
2. 禁止问日 Digest vs Daily Briefing。禁止让 Jake 选模板。禁止新建 `📋 Digests/{YYYY-MM-DD}-Digest.md`。禁止新建或续写 Daily Briefing。禁止用 Linear、Gmail、Drive 顶替本周 intake。
3. 找不到本周 `intake.md`：停下来，说明 GitHub `obsidian-digitalbrain` 的 `main` 还没有周入口。不要自己编一份，不要改走旧日文件。
4. Cursor 云端不要跑生成脚本。只读仓库里已有的 `intake.md`。需要原文再打开该条 wikilink 的 Snipd / WeRead / YouTube-Likes。

## 每天生成（12:00 和 21:00 上海，GitHub Actions）

主文件是 **`📋 Digests/{YYYY-Wnn}/intake.md`**（一篇累积）。有新 Snipd / WeRead / YouTube 才 append。没新增不动、不写空文件。旧的日 Digest 不是入口。Actions 直接 `git push` 回 `main`，不经过 PR。

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

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
   - **精确路径** `git add` 该条 `intake.md`，以及有引用时的 `📖 Resources/concepts/{短标题}.md`。禁止 `git add -A`。`git commit` 后 **`git push origin main`**。禁止为 Digest 开 PR。Journal 仍不自动 push。
   - 若产品强制给出 PR 卡：停下来告诉 Jake，这是 Cursor Cloud 产品限制，不要自己合，也不要去合其它 DigitalBrain PR。

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
