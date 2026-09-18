# 手机：Cursor Cloud + GitHub DigitalBrain

手机这条路走 **Cursor Cloud + `jakeguo117/obsidian-digitalbrain` 的 `main`**。电脑关了，云端只能看见已经在 GitHub `main` 里的文件。开在别的分支或未合的 PR 里，下次新会话从 main clone 就看不见。

两条写入都 **直接进 main**，不为 Digest 走 PR。

| 谁写 | 何时 | 进哪里 |
|---|---|---|
| GitHub Actions | 12:00 和 21:00 上海 | checkout `main` → YouTube 走 API；有 `main` 上已有的 Snipd/WeRead/YouTube 才 append `📋 Digests/{YYYY-Wnn}/intake.md` → `git push` 回 `main` |
| 本机 `com.jake.intake-source-push` | 登录后；Mac 开着每 4 小时 | 只把 `Snipd/` 和 `📥 Inbox/WeRead` 从 iCloud vault 精确推到 `main`。不打开 Obsidian Git 全仓 push。 |
| 手机说「记下」 | 讨论完一条 | 只暂存该条 `intake.md` 勾选/reflection，以及有引用时的 `📖 Resources/concepts/` 卡片；精确路径 commit，**push `main`** |
| 写周记 | 你明确说写 | 改 `📝 Journal/`。**不自动 push** |

禁止 `git add -A`。禁止为 Digest 开 PR。Cursor Cloud 若仍强制出 PR 卡，那是产品限制：停下来告诉 Jake，不要自己合，也不要去合其它 DigitalBrain PR（包括 [#3](https://github.com/jakeguo117/obsidian-digitalbrain/pull/3)）。

## 周入口必须在 GitHub `main`

「今天 Digest」只读：

`📋 Digests/{YYYY-Wnn}/intake.md`

不读日 Digest，不读 Daily Briefing。本机 iCloud 有、GitHub `main` 没有，等于手机找不到入口。

Skill 在仓库内：`.cursor/skills/intake/SKILL.md`。Cloud clone 仓库就能看见，不依赖 Sync Skills。`AGENTS.md` 有同一条硬路由。

**YouTube** 由 Actions 自己拉 API，不依赖开机。**Snipd / WeRead** 没有同等云 API：本机插件先落到 iCloud vault，登录后 `com.jake.intake-source-push` 只把这两棵树推上 `main`，再等下一次 12:00/21:00 Actions 才会 append 进周 `intake.md`。一周没开机，手机 Digest 就还是上次 `main` 上的源。Obsidian Git 保持 `disablePush: true`。`com.jake.journal-daily-digest` 保持卸载，避免和 Actions 双写。

## 电脑开着 vs 关着

| | 电脑开着 | 电脑关着 |
|---|---|---|
| 今天 Digest | 本机 Cursor 可读 iCloud vault | Cloud 只读 GitHub `main` 上的本周 `intake.md` |
| 记下 | 本机改文件；手机路径要 push `main` 才进下一轮 | 精确路径 commit + push `main` |
| 写周记 | 本机写 `📝 Journal/` | Cloud 可写 Journal；**仍不自动 push** |

## 不做

- 不把 YouTube / Digest 脚本或 token 塞进 DigitalBrain
- 不自动 merge 所有 DigitalBrain PR（以免把 #3 这类错误稿合进 main）
- 不自动 push 周记
