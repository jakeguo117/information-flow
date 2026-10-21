<!-- information-flow:digest-route:start -->
## V2.0 硬路由

规则源在 `information-flow`。DigitalBrain 这份是同步副本。改行为去那边，不要只改 vault。时区用 Asia/Hong_Kong。

用户说「看本周汇总」「本周汇总」「本周 digest」或 `/digest`：

1. 读最新一份周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`。`cycle_id` 形如 `cy-YYYYMMDD`，这一天是周四（Asia/Hong_Kong）。在 `📋 Digests/cycles/` 里取日期最新的周四 cycle，再取编号最大的 `r{n}.md`（n 按整数比）。按主题列全量，带状态，保留快照里的 `D-` 编号。不要讨论昨天的日摘要。
2. 没有这份快照就说明还没有。不要编条目。不要回落到 `📋 Digests/daily/`，不要回落到旧的 `📋 Digests/{YYYY-Wnn}/digest.md`，也不要打开 weekly-briefs。
3. Jake 接受之前不写来源卡以外的东西。接受之后写成 `📖 Resources/` 已有领域目录下的 concept 页。`sources` 指回 Inbox 原文，更新 `index.md` 和 `log.md`，每页至少两个链接。不改类型。
4. 不写 `📝 Journal/`。不写 Cognition。Agent 发起的受管文件变更遵循当前 Global Governance / project policy：精确路径暂存，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。会修改已有文件的变更走 task branch 和 PR。PR 与 merge 服从当前授权和治理 gate。

用户说「写周记」「周记」或 `/journal`：

- 后台先读最近 2–3 篇旧周记和未解问题（不输出）。旧周记里的状态不能当作本周事实说。
- 然后第一段列出本周周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md` 的全部 `D-` 条目，含待归类。一行一条，带编号和该行状态。`cycle_id` 是本周周四（Asia/Hong_Kong）的 `cy-YYYYMMDD`，取编号最大的修订。没有快照就说「本周没有周四汇总快照」，不要凭记忆编，不要回落到 `📋 Digests/daily/`、旧的 `📋 Digests/{YYYY-Wnn}/digest.md` 或 weekly-briefs。
- 不把整份汇总贴进周记。自己认周。
- 客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`。持久写入只走 `.cursor/skills/journal/tools/write_journal.py`。本周快照实际打开时，保存用 `--digest-snapshot <digest_id>@r<n>`，不要 `--append-digest`。不写 Cognition。Journal 仍不自动 push。

用户说「记一下：」「想法：」或 `/thought`：

- 走 journal 的想法收集分支，不新开 skill。没有这句触发词的普通聊天不记。
- 原话原样写成新文件 `📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm[-n].md`（上海时间，ISO 周）。不分析，不追问，不改已有文件。
- vault 里已有的 `📝 Journal/素材/2026-W41.md` 和 `📝 Journal/素材/同步约定.md` 保持原样，不删、不改。`同步约定.md` 不再是持续授权。不再往 `📝 Journal/素材/` 写新内容。想法只写到 `📝 Journal/想法/`，按本技能。
- 落盘只走 `.cursor/skills/journal/tools/capture_thought.py`。同一个 id 不写第二次。路径已存在就拒绝。
- 写入成功后，`publish` 把这一个新路径做成只新增的提交并推到 main。修改、删除、重命名都不推，也不强推。本地 main 只是落后、且没有已跟踪文件的修改时，先 fast-forward。本地已有的提交，必须每一笔都只新增想法文件或消化清单，才一起推。
- 远端也前进时，只新增且路径还不在 origin 上的提交会重放后再推，不强推。退出码 5 是工具自己的异常，不是 git 不可用。
- 推送或 publish 失败时，告诉 Jake「没存上」，说明原因，并把他的原话原样念回去。不要说已经存上，也不要说「记了」。
- 周记正文仍不自动 push。消化清单是另一份新文件，只在 `write_journal.py` 成功之后写，并用同一条单文件规则推送。每条是「展开」或「看过未展开」。看过未展开的以后不再捞。未消化 = 全部想法文件减去任何清单里出现过的 id。

用户说「相关认知」「看看之前相关认知」「我们之前有没有相关判断？」「记成 belief / principle / evidence」，或要做有后果的项目 / 策略决定：

1. 先用 `.cursor/skills/cognition/` 做 retrieve。结果只有 found / no_match / partial / unavailable。partial / unavailable 不许说成「没有相关认知」。
2. 不要每句闲聊都检索。小事、改字、低后果操作不走 Cognition。
3. 写 Cognition 只用 cognition tools；Journal / intake 不直接落盘。没 Accept、没有对应该变更的授权之前不写。
4. 详见 `.cursor/skills/cognition/SKILL.md`。私人 Cognition 只留在 DigitalBrain，不写进 information-flow。

用户说「提炼想法」：

- 走 ideas / 提炼想法入口。仓库尚无 `ideas/SKILL.md`。规则源在 information-flow。这里不规定文件布局、字段或落盘步骤。

用户说「记成事实」：

- 走 facts 入口。仓库尚无 `facts/SKILL.md`。规则源在 information-flow 的 `skills/facts/`。这里不规定字段或落盘步骤。

详见 `.cursor/skills/digest/SKILL.md` 与 `.cursor/skills/journal/SKILL.md`。云端不要跑 YouTube / Digest 脚本，也不要把 token 写进 vault。
<!-- information-flow:digest-route:end -->
