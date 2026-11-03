# DigitalBrain 笔记库同步：谁推、谁拉（2026-11-01 起）

DigitalBrain 是单独的私有仓库。这份说明写的是本机插件写出来的笔记怎么上 GitHub、GitHub 上的内容怎么回到 iCloud 笔记库。本仓库的通用脚本不写死任何人的路径或账号；最后一节「本机部署示例」里的标签和路径只是 Jake 自己那套机器的样子，换人部署时按自己的改。

## 现在的分工

| 谁 | 做什么 | 多久一次 |
| --- | --- | --- |
| 常开的那台 Mac（推送方） | 唯一从电脑往 GitHub 推笔记的地方。只推三个文件夹：「📥 Inbox/Snipd/」「📥 Inbox/WeRead/」「📚 Books/」（含「📚 Books/📖 读后感/」）。提交说明以「imac: sync」开头 | 每 10 分钟，开机也跑一次 |
| 同一台 Mac 上的拉取 | Obsidian Git 只做快进拉取，推送关掉，拉取那份 Git 的推送地址设成无效地址 | 每 2 分钟 |
| 另一台 Mac（原来的推送方） | 不再推。上面的 Obsidian Git 已停用，原来的推送任务和对齐任务都已停掉 | 不跑 |
| 云端（GitHub 自动流程、云端代理、网页接口） | 直接写进 GitHub：YouTube 点赞、X 收藏、Instagram 收藏、索引、归堆、提炼 | 各自的时间表 |

## 推送任务的规矩

- 只推上面三个文件夹，其他路径一律不推；每次只加具体文件路径，不用 `git add -A`。
- 不强推，不变基，不合并。推送被拒就丢掉自己克隆里的提交，下一轮再来。
- 本地删掉的文件，GitHub 上不删。
- 跳过：iCloud 还没下载的占位文件、「xxx 2.md」这种冲突副本、3 分钟内刚改过的文件、两边都改过的文件。
- 推送任务只读 iCloud 笔记库，不在笔记库里跑 Git，不写笔记库里的任何文件。它用自己的一份克隆（放在 iCloud 外面）做提交。
- 避开交易任务和备份任务的时段，低优先级运行，每轮最多 2 分钟。
- 推送脚本、三份定时任务模板和测试的正本在 `ops/digitalbrain-imac-push/`，怎么部署、怎么回退见那里的 README。

## 出了问题怎么知道

推送任务自己不往外发消息，不开 GitHub 议题。

- 告警只写两处，都在推送那台 Mac 上：推送日志，和一份状态文件（最近一次运行时间、推了几篇、跳过几篇和原因、要人看的条目）。
- 每天 08:30（香港时间）的例行检查从 GitHub 这边看两件事，不用登录那台 Mac：
  1. 三个文件夹超过 48 小时没有「imac: sync」提交：推送可能停了，或者那台 Mac 上的 Snipd／微信读书插件没在同步（比如微信读书登录过期）。要看原因，再批准一次只读检查，读日志和状态文件。
  2. 出现说明以「intake: sync Snipd WeRead sources」或「vault backup:」开头的提交：说明原来那台 Mac 又在推了，要提醒。

## 已停用、留作备份的东西

- `launchd/com.jake.intake-source-push.plist` 和 `scripts/push_intake_sources.sh`：原来的推送任务，只推 Snipd 和 WeRead，每 4 小时一次。2026-11-01 起停用，文件留在仓库里备查，不要再装。
- 原来那台 Mac 上的 `com.jake.digitalbrain-reconcile`（每 2 分钟对齐一次笔记库）：同一天停掉。

## 本机部署示例（Jake 的机器，2026-11-01 装好）

下面是 Jake 自己的部署，路径和标签只适用于这套机器：

- 推送方是 iMac（HermesdeiMac）。定时任务标签 `com.jake.digitalbrain-imac-push`，每 600 秒一次，从 `~/digitalbrain-pusher/repo` 推；日志 `~/digitalbrain-pusher/logs/push.log`，状态文件 `~/digitalbrain-pusher/state/status.json`。
- iMac 上的拉取：Obsidian 用单独的配置文件夹 `.obsidian-imac`，里面的 Obsidian Git 指向 `~/Library/Application Support/digitalbrain-git-imac`，每 2 分钟只快进拉取，推送关掉。
- iMac 上原来的 `com.jake.obsidian-vault-sync`（整库提交推送，一直失败）已卸载并禁用。
- MacBook 上的 `com.jake.intake-source-push` 和 `com.jake.digitalbrain-reconcile` 已由 Jake 在 2026-11-01 01:18（美东）停掉并禁用；MacBook 上的 Obsidian Git 不推。
- 切换当天推了两个提交：0be1e76（01:19:14 美东，5 篇）和 f0c1da5（01:19:44 美东，2 个新文件）。2026-11-02 从 GitHub 核对过：这之后没有 MacBook 式提交，改这三个文件夹的只有「imac: sync」提交。
