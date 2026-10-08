# Setup / Goals

只给 Jake。五个入口都在 Inbox。每天一份摘要，讨论后进入 Resource。当周 `intake.md` 不再追加。

## 闭环

```
本机插件把 Snipd / WeRead 划线落到 iCloud vault
  → 开机/登录后 com.jake.intake-source-push 只推 📥 Inbox/Snipd/ 与 Inbox/WeRead 上 main
  → 电脑关着时这两路不会自己上 GitHub

GitHub Actions 每天 08:00 上海
  → 先拉 YouTube，再写前一个上海日的 `📋 Digests/daily/YYYY-MM-DD.md`
  → Snipd 和 WeRead 只列当时已经在 main 上的文件
  → 空日也写文件，并写明为空
  → 不再追加 `📋 Digests/{YYYY-Wnn}/intake.md`
  → 直接 push obsidian-digitalbrain main（不经过 PR）

information-flow 的 intake / journal / cognition skill 一进 main
  → sync-digitalbrain-skills 把副本写进 DigitalBrain
    `.cursor/skills/{intake,journal,cognition}/` 和 AGENTS.md 硬路由
  → 下次打开 DigitalBrain 那个项目，读到的就是这份规则
  → 不改已经写下的 intake / 周记 / Cognition 正文

你说「今天 Digest」
  → 上海当天自己认周；本周没有就用最近一周。不要问他 W38
  → 先读最近周记和已挂上的老项目，再从那一周 intake 找一条呼应
  → Yale 式一次一问。禁止整周附录出文
  → 该条 [x] + reflection
  → 有引用的结论 → 📖 Resources/concepts/
  → 精确路径 commit + push main。不为 Digest 开 PR。

写周记
  → 先旧线呼应，再对已勾选 intake
  → 未勾选即使相关也不进入材料
  → 客户说「可以写 / 写吧 / OK 写」之前不落盘
  → 持久写入只走 skills/journal/tools/write_journal.py
  → 📝 Journal/ 周记正文不自动 git push
  → 落盘后如有可复用判断，交给 cognition propose；周记自己不写 Cognition

随手记
  → 触发只有「记一下：」「想法：」/thought。普通聊天不记
  → 原话原样写入 📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm[-n].md
  → 新文件。不改、不删旧文件。同一个 id 不写第二次
  → capture_thought.py publish 只把这一个新路径推到 main
  → 周记正文仍不自动 push
  → write_journal.py 成功之后才写消化清单。每条是「展开」或「看过未展开」，并链到那篇周记
  → 清单也是新文件，按同一条单文件规则推送。推的时候工作区还有别的改动就拒绝
  → 未消化 = 全部想法文件减去任何清单里的 id。看过未展开不再捞
  → 不写 Cognition，不进 Ideas / Experiments
```

手机 = Cursor Cloud + GitHub `obsidian-digitalbrain` 的 `main`。周入口必须已经在 `main`。找不到周文件就停，不要问日 Digest vs Daily Briefing。

Daily Briefing / Weekly Synthesis / 日 Digest / Journal Briefs 不再作为输出。不硬凑空段。不自动 git push 周记。

## 现在（2026-09-19）

| 块 | 状态 |
|---|---|
| Plugin | `information-flow` private GitHub |
| 规则源 | `information-flow/skills/{journal,intake,cognition}` |
| 仓库 skill（手机 Cloud） | DigitalBrain `.cursor/skills/{intake,journal,cognition}/`，由 Actions 覆盖 |
| AGENTS 硬路由 | DigitalBrain `AGENTS.md` 里 `information-flow:digest-route` 段，由 Actions 覆盖 |
| 主文件 | `📋 Digests/daily/YYYY-MM-DD.md` 和 `📋 Digests/讨论说明.md` 在 GitHub `main`。旧的周 intake 只留历史 |
| Actions | 08:00 上海写每日摘要；skill 变更另走 sync-digitalbrain-skills |
| 本机 source push | `com.jake.intake-source-push`：登录 + 每 4 小时，只推 `📥 Inbox/Snipd/` 与 `Inbox/WeRead` |
| Obsidian Git | `disablePush: true`，不整仓 push |
| 日 Digest | 历史留盘，不再生成 |
| 公开 journal-skill | 已 private |

## 完成

1. 电脑周记 2026-09-13 已跑通
2. 摄入脚本 GitHub Actions 一天两次；`com.jake.journal-daily-digest` 保持卸载
3. Snipd/WeRead 靠本机 `com.jake.intake-source-push` 精确 push。08:00 的摘要只收录当时已经在 main 上的文件
4. 周入口 W37/W38 已上 GitHub `main`
5. information-flow 改 skill 后，合进 main 就会覆盖 DigitalBrain 副本；已写成的笔记不重写
