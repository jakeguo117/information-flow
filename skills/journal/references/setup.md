# Setup / Goals

只给 Jake。周四 `weekly-digest.yml` schedule 已停。现行闭环是：平时收集 → 平日想法梳理把归堆落在 `📋 Digests/cluster/YYYY-MM-DD.md`（Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`）→ 周六 `discuss-to-resources-ideas` 扫 cluster 与已落盘 Journal → Ideas / Cognition / Resources。历史 `📋 Digests/cycles/` 保留。takeaway 已 offline，本 PR 不另挂停排程。不接管历史 `📋 Digests/daily/`。

当周 `intake.md` 不再追加，也不是讨论入口。

## 闭环

```
平时收集
  → GitHub Actions daily-intake，07:30 Asia/Hong_Kong，只收集 YouTube-Likes
  → 写入 📥 Inbox/YouTube-Likes/，不写日摘要
  → Snipd / WeRead 仍由本机插件落到 iCloud vault
  → 开机/登录后 com.jake.intake-source-push 只推 📥 Inbox/Snipd/ 与 Inbox/WeRead 上 main
  → 电脑关着时这两路不会自己上 GitHub

周四整理（process）— schedule 已停，只留救急
  → weekly-digest.yml 不再按周四自动跑
  → workflow_dispatch 救急时仍可跑 process_batch.py
  → 写入 📋 Digests/cycles/{cycle_id}/batch.json
  → cycle_id 是当天 cy-YYYYMMDD（必须是周四）
  → 索引目录不在，或 inputs.jsonl 缺失/为空：跳过，不编批次
  → 本 Action 不写 📋 Digests/cluster/，也不写 📋 Digests/daily/

周四汇总（digest r{n}）— schedule 已停，只留救急
  → 不再在周四 20:00 自动跑 build_digest_v2.py
  → 救急 dispatch 仍写入 📋 Digests/cycles/{cycle_id}/r{n}.md
  → 同一 cycle 里 n 递增；已有修订的字节不改
  → 索引未建时同样跳过，不编快照
  → 救急提交仍只覆盖该 cycle 与 index，并 push obsidian-digitalbrain main
  → 归堆推库不是这条 Action。历史 cycles 不删

平日归堆
  → 正本路径 📋 Digests/cluster/YYYY-MM-DD.md（多日 YYYY-MM-DD_DD.md），由想法梳理 21:00 写
  → 双跑期间 ChatGPT 只写 -gpt，正本由想法梳理 21:00 写，两份由 Workflow 每天对比，周六提炼两边 cluster 都读、同日去重；切换之后的做法另行更新
  → 归堆推库＝Cloud Agent 推 jakeguo117/obsidian-digitalbrain
  → information-flow Actions 不写这份归堆，本文件不接推送接线
  → 落盘当下不跑 discuss-to-resources-ideas
  → 第二天归堆以 skills/daily-cluster/SKILL.md 开头三条为准，不另写岗位职责。前一天文件里已有讨论块（## 深挖、## 讨论 log 或 ## 语音整理）就是开过聊，没聊到的条不要再翻出来。完全没有这类块，整包带到第二天，跟新收的一起问「今天这些里（含昨天整包还没开过聊的）你想先聊哪几条？」。正本例程看没有 -gpt 的文件，本插件看 -gpt。微信读书／@bot 当天没聊可以带到第二天；第二天还没聊就丢掉，以后不再带。带到第二天只在摘要和问句里摆出来。落盘仍只写当天文件，不把旧料重抄进新文件。不另开聊天，不自动写讨论纪要。他没回就不写进选题／资料库

周六提炼
  → 想法梳理加载 discuss-to-resources-ideas
  → 本周 cluster 正本和 -gpt 都扫（有哪份读哪份）。同一天两份都在：两份都读。同一条（同一来源链接、同一段引用、或同一标题）只算一次。同一条两份详略不同，留更详的那份，细节不丢。另扫 📝 Journal/{YYYY-MM-DD}*.md（文件不在盘上就跳过）
  → Resources / Ideas / Cognition 互链；Ideas、Belief、Principle、Resources 正式入库仍要点头
  → 禁 concept→Evidence

周五周记
  → Jake 说「写周记」「周记」或 /journal。没有周五定时任务
  → 先读最近 3–4 篇旧周记（按文件名），给一段 recap：未收的线、发生过什么、已点名的项目。旧周记里的状态不能当作本周事实
  → 再用本会话的 Notion 连接看正在推进、待办池、可执行计划清单。读不到就说一声，不编，只按周记 recap 继续
  → 然后跟 Jake 讨论。不读 digest、cluster、周四快照或周 digest
  → 客户说「可以写 / 写吧 / OK 写」之前不落盘
  → 持久写入只走 skills/journal/tools/write_journal.py
  → 不带 --digest-snapshot。旧调用仍可传这个参数，当前流程不传，也不要 --append-digest
  → 📝 Journal/ 周记正文不自动 git push
  → 落盘后如有可复用判断，交给 cognition propose；周记自己不写 Cognition
  → 落盘当下不跑 discuss-to-resources-ideas。周四接受不再写每周 Resources

Ideas / 认知 / 内容
  → 「看本周汇总」或 /digest：只读归档里的周四快照。不把周四接受写成每周来源卡。不写 Journal / Cognition
  → 周六 discuss-to-resources-ideas 才做 Resources／Ideas／Cognition。点头后的 Idea 走 write_idea.py
  → 「提炼想法」走 ideas。规则源在 information-flow 的 skills/ideas/SKILL.md
  → 「相关认知」走 cognition retrieve。partial / unavailable 不许说成没有相关认知
  → 「记成事实」走 facts 入口。仓库尚无 facts/SKILL.md，规则源在 information-flow 的 skills/facts/
  → 来源卡、认知、事实都不是周记正文

随手记
  → 触发只有「记一下：」「想法：」/thought。普通聊天不记
  → 原话原样写入 📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm[-n].md
  → 新文件。不改、不删旧文件。同一个 id 不写第二次
  → capture_thought.py publish 只把这一个新路径做成只新增的提交并推到 main。修改、删除、重命名不推，不强推
  → 本地 main 只是落后、且没有已跟踪文件的修改时，先 fast-forward，并且不覆盖被忽略的本地文件。远端也前进时，已有的只新增想法或消化清单提交会重放到 origin/main 再一起推；修改、删除或路径已在 origin 上则拒绝，不强推
  → 失败要告诉 Jake「没存上」，说明原因，并把他的原话原样念回去
  → 周记正文仍不自动 push
  → write_journal.py 成功之后才写消化清单。每条是「展开」或「看过未展开」，并链到那篇周记
  → 清单也是新文件，按同一条规则推送。周记文件还没提交时，不要把周记和清单打进同一个提交
  → 未消化 = 全部想法文件减去任何清单里的 id。看过未展开不再捞
  → 不写 Cognition，不进 Ideas / Experiments
```

手机 = Cursor Cloud + GitHub `obsidian-digitalbrain` 的 `main`。写周记不读周四快照，也不要改去 `📋 Digests/daily/` 或旧周路径，不要为了周记生成新 cycle。归堆不由本技能读。周六提炼不靠这份快照。

Daily Briefing / Weekly Synthesis / Journal Briefs 不再作为输出。不硬凑空段。不自动 git push 周记。聊天里的 agent 不跑 YouTube / process / digest 脚本，也不把 token 写进 vault。

## 现在（V2.0）

| 块 | 状态 |
|---|---|
| Plugin | `information-flow` private GitHub |
| 规则源 | `information-flow/skills/{journal,intake,digest,cognition,ideas,discuss-to-resources-ideas}`。facts 尚无 SKILL.md |
| 仓库 skill（手机 Cloud） | DigitalBrain `.cursor/skills/` 由 Actions 覆盖。本变更不接归堆推送 |
| AGENTS 硬路由 | DigitalBrain `AGENTS.md` 里 `information-flow:digest-route` 段，由 Actions 覆盖 |
| 主文件 | 平日归堆 `📋 Digests/cluster/YYYY-MM-DD.md`。写周记不读它，也不读周四快照。周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md` 只作归档。`--digest-snapshot` 只留给旧调用。历史 `📋 Digests/daily/` 不接管。旧的 `📋 Digests/{YYYY-Wnn}/digest.md` 不是主文件 |
| Actions | daily-intake 只收集 YouTube-Likes（07:30 Asia/Hong_Kong）。周四 process／digest 的 schedule 已停，`workflow_dispatch` 只作救急。归堆不由 information-flow Actions 写入。skill 变更另走 sync-digitalbrain-skills |
| 本机 source push | `com.jake.intake-source-push`：登录 + 每 4 小时，只推 `📥 Inbox/Snipd/` 与 `Inbox/WeRead` |
| Obsidian Git | `disablePush: true`，不整仓 push |
| 日摘要 / takeaway | takeaway 已 offline，本 PR 不另挂停排程。`scripts/daily_takeaway.py` 留作 dead code，不在本变更删除。历史 `📋 Digests/daily/` 文件不改 |
| 公开 journal-skill | 已 private |

information-flow 改 skill 后，合进 main 就会覆盖 DigitalBrain 副本；已写成的笔记不重写。
