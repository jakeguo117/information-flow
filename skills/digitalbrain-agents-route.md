<!-- information-flow:digest-route:start -->
## V2.0 硬路由

规则源在 `information-flow`。DigitalBrain 这份是同步副本。改行为去那边，不要只改 vault。时区用 Asia/Hong_Kong。

用户说「看本周汇总」「本周汇总」「本周 digest」或 `/digest`：

周四 `weekly-digest.yml` schedule 已停。`📋 Digests/cycles/` 只作归档。`/digest` 不生成新 cycle，也不把周四接受写成每周 Resources。

1. 归档里若有周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`，可以按主题列全量。`cycle_id` 形如 `cy-YYYYMMDD`，这一天是周四（Asia/Hong_Kong）。在 `📋 Digests/cycles/` 里取日期最新的周四 cycle，再取编号最大的 `r{n}.md`（n 按整数比）。带状态，保留快照里的 `D-` 编号。不要讨论昨天的日摘要。
2. 没有这份快照就说明还没有。不要编条目。不要回落到 `📋 Digests/daily/`，不要回落到旧的 `📋 Digests/{YYYY-Wnn}/digest.md`，也不要打开 weekly-briefs。不要把 `📋 Digests/cluster/` 冒充周四快照。
3. Jake 接受之前不写来源卡。`/digest` 不把接受之后的来源卡当作每周提炼。每周 Resources／Ideas／Cognition 由周六 `discuss-to-resources-ideas` 做。Resource 页不是 Evidence。
4. 不写 `📝 Journal/`。不写 Cognition。Agent 发起的受管文件变更遵循当前 Global Governance / project policy：精确路径暂存，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。会修改已有文件的变更走 task branch 和 PR。PR 与 merge 服从当前授权和治理 gate。

平日归堆正本是 `📋 Digests/cluster/YYYY-MM-DD.md`（多日 `YYYY-MM-DD_DD.md`），由想法梳理 21:00 写。双跑期间 ChatGPT 只写 -gpt，正本由想法梳理 21:00 写，两份由 Workflow 每天对比，周六提炼两边 cluster 都读、同日去重；切换之后的做法另行更新。归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`，不是 information-flow Actions 写 vault。这里不实现推送接线。不碰、不接管历史 `📋 Digests/daily/`。takeaway 已 offline，本 PR 不另挂停排程。

第二天归堆以 `skills/daily-cluster/SKILL.md` 开头三条为准，不另写岗位职责。正本例程读前一个 Asia/Hong_Kong 日历日、没有 `-gpt` 的文件；本插件读带 `-gpt` 的那份。多日文件盖住那一天就读那一份；没有这份文件就当没有。那天文件里已有 `## 深挖`、`## 讨论 log` 或 `## 语音整理`，就是开过聊：没聊到的条＝他不感兴趣，第二天不要再翻出来。那天文件里没有任何这类讨论块，就是完全没开过聊：整包带到第二天，跟新收的一起问「今天这些里（含昨天整包还没开过聊的）你想先聊哪几条？」。微信读书／@bot 当天没聊可以带到第二天；第二天还没聊就丢掉，以后不再带，不再置顶。这条不跟着整包再多走一天。带到第二天只在归堆摘要和聊天问句里摆出来一起问。落盘仍只写当天文件，不把旧料重抄进新文件。不另开聊天。不自动写讨论纪要。他没回就不写进选题／资料库。周六提炼仍只在周六跑，只凭 Context 不能出 Ideas。换地方装上这个 plugin，现行归堆／带到第二天／周六两边都读等功能应能完整跑。

周六想法梳理加载 `discuss-to-resources-ideas`：本周 cluster 正本（`YYYY-MM-DD.md`、`YYYY-MM-DD_DD.md`）和 GPT 线（`YYYY-MM-DD-gpt.md`、`YYYY-MM-DD_DD-gpt.md`）都扫，不区分来源，有哪份读哪份。同一天两份都在：两份都读。同一条（同一来源链接、同一段引用、或同一标题）只算一次。同一条两份详略不同，留更详的那份，细节不丢。另扫已落盘的 `📝 Journal/{YYYY-MM-DD}*.md`。平日落盘当下不跑。

用户说「写周记」「周记」或 `/journal`：

- 先读最近 3–4 篇旧周记（按文件名），给 Jake 一段 recap：未收的线、发生过什么、已点名的项目。旧周记里的状态不能当作本周事实说。
- 再用本会话的 Notion 连接看正在推进、待办池、可执行计划清单。读不到就用一句话说明，不编，只按 recap 继续。
- 然后讨论。不读 digest、`📋 Digests/cluster/`、周四快照 `📋 Digests/cycles/` 或周 digest。不要列 `D-` 条目，没有快照也不停。不写 cluster，不改 `📋 Digests/daily/`。周记落盘当下不跑 `discuss-to-resources-ideas`。
- 客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`。持久写入只走 `.cursor/skills/journal/tools/write_journal.py`，不带 `--digest-snapshot`，不要 `--append-digest`。不写 Cognition。Journal 仍不自动 push。

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

- 走 `ideas`。确认前不落盘。落盘用 `skills/ideas/tools/write_idea.py`。规则源在 information-flow。
- 每周批量提炼不在周四 digest 接受时写 Resources。周六 `discuss-to-resources-ideas` 在 Jake 点头后调用同一个写入工具。平日 `📋 Digests/cluster/` 或 Journal 落盘当下不跑。归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`，不是本路由接的 Action。

用户说「记成事实」：

- 走 facts 入口。仓库尚无 `facts/SKILL.md`。规则源在 information-flow 的 `skills/facts/`。这里不规定字段或落盘步骤。

详见 `.cursor/skills/digest/SKILL.md` 与 `.cursor/skills/journal/SKILL.md`。云端不要跑 YouTube / Digest 脚本，也不要把 token 写进 vault。
<!-- information-flow:digest-route:end -->
