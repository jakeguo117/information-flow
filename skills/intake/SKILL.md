---
name: intake
description: Weekly DigitalBrain intake.md and Yale-style discussion. Use when Jake says 「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」or /intake. Resolves this week's intake from Asia/Shanghai date. Does not write Journal.
---

# intake

信息流。不要救 Hermes。不要写 `📝 Journal/`。不要写日子、日历、Reminders、保险交易。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。

## 硬路由（今天 Digest）

用户说「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」或 `/intake`：

1. **自己认周。不要问他是哪一周，不要等他说 W38。** 用 Asia/Shanghai 当天算 ISO 周，打开 `📋 Digests/{YYYY-Wnn}/intake.md`。有 information-flow 脚本就先跑 `python3 scripts/weekly_intake.py --vault "$VAULT" --date YYYY-MM-DD`。本周文件不存在，就用 `📋 Digests/` 里已有的最近一周。一个都没有：停下来，说明 GitHub `main` 还没有周入口。不要自己编一份，不要改走旧日文件，不要问他选周。
2. 先读最近 2–3 篇 `📝 Journal/`，以及那些周记里已经挂上的 `🚀 Projects/` / Resource 小线（老项目、很小的未收线）。intake 先不上场。
3. 他如果已经说了这周画像，接住。没有就先问一句人在哪、心里在转什么。不要甩本周清单，不要出文。
4. 再打开 **刚解析出的那一周** `intake.md`。只挑 **一条** 和旧线 / 画像呼应的未勾选来问（Yale 式，一次一问）。对不上的略过。
5. 禁止问日 Digest vs Daily Briefing。禁止让 Jake 选模板。禁止新建 `📋 Digests/{YYYY-MM-DD}-Digest.md`。禁止新建或续写 Daily Briefing。禁止用 Linear、Gmail、Drive 顶替本周 intake。
6. Cursor 云端不要跑生成脚本。只读仓库里已有的 `intake.md`。需要原文再打开该条 wikilink 的 Snipd / WeRead / YouTube-Likes。
7. **客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`。** 周记不是这条路的输出。

禁止整周附录。禁止把 Briefing 贴进对话当出文。

## 每天生成（12:00 和 21:00 上海，GitHub Actions）

主文件是 **`📋 Digests/{YYYY-Wnn}/intake.md`**（一篇累积）。有新 Snipd / WeRead / YouTube 才 append。没新增不动、不写空文件。旧的日 Digest 不是入口。Actions 直接 `git push` 回 `main`，不经过 PR。

YouTube 由 Actions 拉 API。Snipd / WeRead 靠本机插件落盘，再由 `scripts/push_intake_sources.sh`（launchd `com.jake.intake-source-push`：登录后跑，Mac 开着每 4 小时）只推这两棵树上 `main`。下一次 Actions 才 append。一周没开机，手机只能读上次已经在 `main` 上的源。不要重新加载 `com.jake.journal-daily-digest`。

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

Vault：本机 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`；否则当前工作区根（须有 `📝 Journal/`）。

## 讨论（先旧线，再呼应，一次一问）

用户说「今天 Digest」「讨论 Digest」或 `/intake`：

1. 先读最近 2–3 篇周记，以及旧周记已经点名的项目 / 卡片。需要原文再打开该条 wikilink。不要为了「补这周发生了什么」去扫整个 vault。
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

Journal 只读本周 intake 里已经 `[x]` 的条目。客户没说可以写周记之前，这条 skill 不写周记。

intake 条目和 `📖 Resources/concepts/` 卡片 **不是 Evidence**。Cognition 以后可以把它们当 provenance，但 Evidence 必须有具体 claim、来源和 validation。不要改 intake 文件格式来迁就 Cognition。
