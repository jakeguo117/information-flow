# Setup / Goals

只给 Jake。信息流每天进当周 `intake.md`，讨论后带引用的 reflection 进 wiki，周末写成周记。

## 闭环

```
本机插件把 Snipd / WeRead 划线落到 iCloud vault
  → 开机/登录后 com.jake.intake-source-push 只推 Snipd/ 与 Inbox/WeRead 上 main
  → 电脑关着时这两路不会自己上 GitHub

GitHub Actions 每天 12:00 和 21:00 上海
  → YouTube 走 API；Snipd/WeRead 只看 main 上已有的源
  → 📋 Digests/{YYYY-Wnn}/intake.md   有新内容才 append
  → 直接 push obsidian-digitalbrain main（不经过 PR）

information-flow 的 intake / journal skill 一进 main
  → sync-digitalbrain-skills 把副本写进 DigitalBrain
    `.cursor/skills/{intake,journal}/` 和 AGENTS.md 硬路由
  → 下次打开 DigitalBrain 那个项目，读到的就是这份规则
  → 不改已经写下的 intake / 周记正文

你说「今天 Digest」或「W38 有什么」
  → 先读最近周记和已挂上的老项目，再从本周 intake 找一条呼应
  → Yale 式一次一问。禁止整周附录出文
  → 该条 [x] + reflection
  → 有引用的结论 → 📖 Resources/concepts/
  → 精确路径 commit + push main。不为 Digest 开 PR。

写周记
  → 先旧线呼应，再对已勾选 intake
  → 客户说「可以写 / 写吧 / OK 写」之前不落盘
  → 📝 Journal/   不自动 git push
```

手机 = Cursor Cloud + GitHub `obsidian-digitalbrain` 的 `main`。周入口必须已经在 `main`。找不到周文件就停，不要问日 Digest vs Daily Briefing。

Daily Briefing / Weekly Synthesis / 日 Digest / Journal Briefs 不再作为输出。不硬凑空段。不自动 git push 周记。

## 现在（2026-09-19）

| 块 | 状态 |
|---|---|
| Plugin | `information-flow` private GitHub |
| 规则源 | `information-flow/skills/{journal,intake}` |
| 仓库 skill（手机 Cloud） | DigitalBrain `.cursor/skills/{intake,journal}/`，由 Actions 覆盖 |
| AGENTS 硬路由 | DigitalBrain `AGENTS.md` 里 `information-flow:digest-route` 段，由 Actions 覆盖 |
| 主文件 | `📋 Digests/{YYYY-Wnn}/intake.md` 须在 GitHub `main` |
| Actions | 12:00 / 21:00 上海写 intake；skill 变更另走 sync-digitalbrain-skills |
| 本机 source push | `com.jake.intake-source-push`：登录 + 每 4 小时，只推 `Snipd/` 与 `Inbox/WeRead` |
| Obsidian Git | `disablePush: true`，不整仓 push |
| 日 Digest | 历史留盘，不再生成 |
| 公开 journal-skill | 已 private |

## 完成

1. 电脑周记 2026-09-13 已跑通
2. 摄入脚本 GitHub Actions 一天两次；`com.jake.journal-daily-digest` 保持卸载
3. Snipd/WeRead 靠本机 `com.jake.intake-source-push` 精确 push，再等下一次 Actions append
4. 周入口 W37/W38 已上 GitHub `main`
5. information-flow 改 skill 后，合进 main 就会覆盖 DigitalBrain 副本；已写成的笔记不重写
