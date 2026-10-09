<!-- information-flow:digest-route:start -->
## 今天 Digest / 周记（硬路由）

规则源在 `information-flow`。DigitalBrain 这份是同步副本。改行为去那边，不要只改 vault。

用户说「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」或 `/digest`：

1. 用 Asia/Shanghai 的昨天，打开 `📋 Digests/daily/YYYY-MM-DD.md`。文件不在 `main` 上就停，说明当天摘要还没有。不要自己编条目，不要改去打开按周累积的旧入口。
2. 从这份摘要提出最多两个概念。一个概念可以挂上多条原文。Jake 接受之前不写 Resource。
3. 接受之后写成 `📖 Resources/` 已有领域目录下的一页。`sources` 指回 Inbox 原文，更新 `index.md` 和 `log.md`，每页至少两个链接。不改类型。
4. 不改 `📝 Journal/`。这条不写 Cognition。Agent 发起的受管文件变更遵循当前 Global Governance / project policy：精确路径暂存，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。会修改已有文件的变更走 task branch 和 PR。PR 与 merge 服从当前授权和治理 gate。

用户说「写周记」「周记」或 `/journal`：

- 自己认周，先用旧周记和已经挂上的老项目找呼应，再对已勾选 intake。未勾选即使相关也不进入周记材料。
- 客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`。持久写入只走 `.cursor/skills/journal/tools/write_journal.py`。不写 Cognition。Journal 仍不自动 push。

用户说「记一下：」「想法：」或 `/thought`：

- 走 journal 的想法收集分支，不新开 skill。没有这句触发词的普通聊天不记。
- 原话原样写成新文件 `📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm[-n].md`（上海时间，ISO 周）。不分析，不追问，不改已有文件。
- 落盘只走 `.cursor/skills/journal/tools/capture_thought.py`。同一个 id 不写第二次。路径已存在就拒绝。
- 写入成功后，`publish` 把这一个新路径做成只新增的提交并推到 main。修改、删除、重命名都不推，也不强推。本地 main 只是落后、且没有已跟踪文件的修改时，先 fast-forward。本地已有的提交，必须每一笔都只新增想法文件或消化清单，才一起推。
- 推送或 publish 失败时，告诉 Jake「没存上」，说明原因，并把他的原话原样念回去。不要说已经存上，也不要说「记了」。
- 周记正文仍不自动 push。消化清单是另一份新文件，只在 `write_journal.py` 成功之后写，并用同一条单文件规则推送。每条是「展开」或「看过未展开」。看过未展开的以后不再捞。未消化 = 全部想法文件减去任何清单里出现过的 id。

详见 `.cursor/skills/digest/SKILL.md` 与 `.cursor/skills/journal/SKILL.md`。云端不要跑 YouTube / Digest 脚本，也不要把 token 写进 vault。

用户说「相关认知」「看看之前相关认知」「我们之前有没有相关判断？」「记成 belief / principle / evidence」，或要做有后果的项目 / 策略决定：

1. 先用 `.cursor/skills/cognition/` 做 retrieve。结果只有 found / no_match / partial / unavailable。partial / unavailable 不许说成「没有相关认知」。
2. 不要每句闲聊都检索。小事、改字、低后果操作不走 Cognition。
3. 写 Cognition 只用 cognition tools；Journal / intake 不直接落盘。没 Accept、没有对应该变更的授权之前不写。
4. 详见 `.cursor/skills/cognition/SKILL.md`。私人 Cognition 只留在 DigitalBrain，不写进 information-flow。
<!-- information-flow:digest-route:end -->
