# Setup / Goals

只给 Jake。信息流每天进当周 `intake.md`，讨论后带引用的 reflection 进 wiki，周末写成周记。

## 闭环

```
GitHub Actions 每天 12:00 和 21:00 上海
  → 📋 Digests/{YYYY-Wnn}/intake.md   有新内容才 append
  → 直接 push obsidian-digitalbrain main（不经过 PR）

你说「今天 Digest」
  → 只读本周 intake.md，Yale 式一次一问（先读 Briefing）
  → 该条 [x] + reflection
  → 有引用的结论 → 📖 Resources/concepts/
  → 精确路径 commit + push main。不为 Digest 开 PR。

写周记
  → 只读本周 intake 的 [x] 与 Resource
  → 📝 Journal/   不自动 git push
```

手机 = Cursor Cloud + GitHub `obsidian-digitalbrain` 的 `main`。周入口必须已经在 `main`。找不到周文件就停，不要问日 Digest vs Daily Briefing。

Daily Briefing / Weekly Synthesis / 日 Digest / Journal Briefs 不再作为输出。不硬凑空段。不自动 git push 周记。

## 现在（2026-09-18）

| 块 | 状态 |
|---|---|
| Plugin | `~/plugins/information-flow` private GitHub |
| Cursor 私人 skill | `~/.cursor/skills/{journal,intake}` |
| 仓库 skill（手机 Cloud） | DigitalBrain `.cursor/skills/intake/SKILL.md` |
| 主文件 | `📋 Digests/{YYYY-Wnn}/intake.md` 须在 GitHub `main` |
| Actions | 12:00 / 21:00 上海，直接 push `main` |
| 日 Digest | 历史留盘，不再生成 |
| 公开 journal-skill | 已 private |

## 完成

1. 电脑周记 2026-09-13 已跑通
2. 摄入脚本 GitHub Actions 一天两次；本机 launchd 保持卸载
3. 周入口 W37/W38 已上 GitHub `main`；手机「今天 Digest」应直接问 Briefing 第一条未勾选
