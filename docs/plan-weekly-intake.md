# 周 intake：累积 `intake.md`

代码只在 `information-flow`。笔记写进本机 DigitalBrain：

`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`

主文件：`📋 Digests/{YYYY-Wnn}/intake.md`（一篇累积，不是每天一个 Digest）。口语里的 W38 就是 `2026-W38`。

## 形状

```markdown
---
week: 2026-W38
type: weekly-intake
item_count: N
open_count: M
generator: journal-weekly-intake
---

# Intake — 2026-W38

## Briefing
（只概括未勾选。全勾完就写「本周未讨论条目已清空」，不删文件。）

## 条目
- [ ] YouTube · **Trevor Noah** — 标题
  - [[📥 Inbox/YouTube-Likes/2026-09-08-CqtvQ9uDBho]]
  - 两到三句划线。不堆原文。
  - 摄入：2026-09-08 · youtube
```

- 每天 GitHub Actions 有新 Snipd / WeRead / YouTube 就 append；没新增不动、不写空文件。YouTube 由 Actions 拉 API。Snipd / WeRead 须先经本机 `push_intake_sources.sh` 上到 `main`，再等下一次 Actions。
- 每条：标题 + wikilink + 2–3 句划线 + checkbox。`[x]` 沉底。
- 挂钩只允许一行 `挂钩：[[笔记]]` 或 Linear 标识，不写 CRM 流水。
- 幂等：wikilink 当 id。已有条目不改 checkbox、挂钩、reflection、已有划线。
- 没有 `generator: journal-weekly-intake` 的文件拒绝覆盖。
- 划线不跑 LLM。Snipd 用 Episode AI description 或前两条 snip 要点；WeRead 用当天 📌；YouTube 用能成句的摘句。不要 transcript。
- 不写日子 / 日历 / Reminders / 保险交易。不自动 push 周记。不救 Hermes。
- 日 Digest 不再当主入口、不再生成。2026-09-08 到 2026-09-16 已有条目灌进 W37 / W38。旧日文件留盘。

## 脚本

- `daily_digest.py`：append 到当周 `intake.md`。空天 skip。
- `weekly_rollup.py`：只重写已存在 `intake.md` 的 Briefing 并把 `[x]` 沉底。不写 `📊 Journal Briefs/`。文件不存在就 skip。
- `run_digest_jobs.sh` 仍三条命令（只给 Actions / 手动；本机 digest launchd 保持卸载）。
- `push_intake_sources.sh` 另开 `origin/main` worktree，只同步 `Snipd/` 与 `📥 Inbox/WeRead`。禁止 `git add -A`、禁止 force-push、禁止 `--no-verify`。
- Actions 只 `git add` `📋 Digests` 和它写入的 `📥 Inbox/YouTube-Likes`。禁止 `git add -A`。

## Skill

- intake：读本周 `intake.md` 的 Briefing，Yale 式一次一问。记下则 `[x]` + 带引用 reflection；有引用才写 `📖 Resources/concepts/`。
- journal：只读本周 intake 的 `[x]` 与 Resource，不再依赖日 Digest 的 `## 讨论` 或 Journal Briefs。
