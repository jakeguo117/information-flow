---
name: discuss-to-resources-ideas
description: 周六把本周已落盘的归堆和日期篇提炼成 Resources、Ideas、Cognition 互链，另出自媒体选题（按 Idea 写进 💡 Ideas/Content/），并抽出 plan 清单交给资料管理员。动手前先过本周完整性闸：本周日期篇至少 1 篇。已有至少 1 篇时，缺归堆正本只记在 cluster_gaps，不拦。没有日期篇时，有 Inbox 或没查清 Inbox 的日子缺归堆正本仍拦住。闸不过就不生成。若周六因缺被拦，同周周日用同一技能、同一闸补跑一次，不是改成只周日跑。Context 段最多出 Resources 候选；Ideas 只从讨论 log 和 Journal 来；plan 不进 Ideas。想法梳理在周六加载；周六被这道闸拦住时，同周周日可再加载一次。平日 cluster 或 Journal 落盘当下不跑。只吃库内文件。闸过之后正本和 -gpt 都读，同日去重。不写、不扫、不接管 📋 Digests/daily/。
---

# discuss-to-resources-ideas

Jake 2026-10-28 批的方案纸 v2 用本技能做每周提炼。方案纸原文把归堆写成 `📋 Digests/daily/`。该路径与 takeaway 脚本的输出撞车，PM 定归堆改为 `📋 Digests/cluster/`。takeaway 已 offline，本 PR 不另挂停排程。Jake 可以再改路径；在改口之前以 cluster 为准。

加载后先做「本周完整性闸」。闸不过，不生成 idea、resource、plan。

自媒体选题也是 Idea（见下面「自媒体选题」一节），跟其他 Ideas 一起受这道闸管：闸不过，不出自媒体选题，连候选也不展示；周六因此被拦，同周周日补跑同一道闸，闸过才出。这道闸本身怎么判、认哪几个来源子夹，本次不改。

本文件只定路径、来源分流和闸。不在 information-flow 里接 Cloud Agent，也不新开把归堆推进库的 Action。

## 谁、何时

- 加载者：想法梳理。
- 何时：仍以每周六一次为主。例程以后再接。
- 同周补跑：若周六这次因为本周完整性闸被拦住，同一个 Asia/Hong_Kong 日历周的周日，可以再加载本技能，先跑同一道闸。闸过才生成。这不是把例程改成只周日跑。周六没有被这道闸拦住的，周日不跑。周日闸过并已经开始提炼之后，本周不再跑。周日这道闸还不过，就停在缺漏清单，不要改到周一补。
- 硬禁：平日 `📋 Digests/cluster/` 或 `📝 Journal/` 落盘当下 right-away 跑本技能。digest、journal、intake 不在落盘当下调用本技能。周一到周五不跑。
- 周四 `weekly-digest.yml` 的 schedule 已停。`📋 Digests/cycles/` 是归档，不是本技能的输入，也不要为了周六去生成新 cycle。

## 本周完整性闸

加载本技能之后，先做这一节，再读「输入」，再提炼。也叫 preflight。闸不过，不生成。

本周窗口不变：Asia/Hong_Kong 周一 00:00 到周日 23:59。例：2026-10-31 周六，本周是 2026-10-26 到 2026-11-01。文件名按日历日期，不按周号。

用仓库里的检查脚本算，不要另算一套。information-flow 里是 `skills/discuss-to-resources-ideas/tools/preflight.py`。同步进库之后是 `.cursor/skills/discuss-to-resources-ideas/tools/preflight.py`。

先查周一至周五每一天有没有 Inbox，再把结果传给脚本。看的库是 `jakeguo117/obsidian-digitalbrain` 的 `main`。手头已经是同一份库时，就看手头这份。某一天算「有 Inbox」：香港时间当天 00:00 到 23:59，有新文件提交进 `📥 Inbox/` 的 `X-Bookmarks`、`WeRead`、`Snipd`、`YouTube-Likes`、`Instagram-Saves`。以提交时间为准。不看 `📥 Inbox/_index/`。查不清的那一天不要当成无 Inbox。

```bash
python3 skills/discuss-to-resources-ideas/tools/preflight.py \
  --run-at '2026-10-31T12:00:00+08:00' \
  --cluster-name 2026-10-26.md \
  --journal '📝 Journal/2026-10-30 标题.md' \
  --inbox-day 2026-10-26 \
  --empty-inbox-day 2026-10-27
```

- `--run-at`：这次运行的时刻，必须带时区。脚本按 Asia/Hong_Kong 取日期。
- `--cluster-name`：`📋 Digests/cluster/` 里的文件名，可重复。正本和带 `-gpt` 的都可以传。脚本只用正本判断有没有盖住。
- `--journal`：`📝 Journal/` 顶层的日期篇路径，可重复。`📝 Journal/想法/` 传了也不计数。
- `--inbox-day`：确认有 Inbox 的工作日，可重复。
- `--empty-inbox-day`：确认没有 Inbox 的工作日，可重复。
- `--saturday-blocked`：只在「这次的香港日期是周日，且本周周六加载本技能时被这道闸拦住」时才加。不要因为今天是周日就加。

退出码 0：闸过。才进入「输入」和后面的提炼。正本和 `-gpt` 仍按「输入」都读。同一天两份都在：两份都读。同一条（同一来源链接、同一段引用、或同一标题）只算一次。同一条两份详略不同，留更详的那份，细节不丢。本周已有至少 1 篇 Journal 时，`cluster_gaps` 里的日期不改这个退出码。退出码 0 仍把 `cluster_gaps` 照说，缺的日子列出来，不因此停下。
退出码 2：停下。把打出的 `missing` 和 `remind` 照说。不产出 idea、resource、plan 候选。不调用 `write_idea.py`。不做 Resources 正式入库。不把 plan 清单交给资料管理员。

口径与脚本相同。会话里暂时没有这份脚本时，按下面手算，不要改口径：

1. 算出本周周一至周日。其中周一至周五要查归堆覆盖。
2. Journal：`📝 Journal/{YYYY-MM-DD}*.md`，日期落在本周周一至周日，至少 1 篇。不要求必须有周五。`📝 Journal/想法/` 的随手记不计入。子目录里的文件不计入。
3. 归堆覆盖仍按正本算：`📋 Digests/cluster/YYYY-MM-DD.md`，或一份多日正本 `YYYY-MM-DD_DD.md` 的日期区间。多日文件的结束日是同一个月里的 `DD`，并且晚于起始日，从起始日到结束日都算盖住，和平日归堆的文件名是同一规则。带 `-gpt` 的文件不拿来补这个覆盖。周末不要求归堆。没盖住的工作日是否拦住，见第 4 条。
4. 无 Inbox 的工作日不算缺归堆。没有正本、又确认当天无 Inbox：豁免，不写入 `cluster_gaps`。没有正本、当天有 Inbox，或没查清有没有 Inbox：把这一天写入 `cluster_gaps`。本周 Journal 至少 1 篇时，这些天只作记录，不拦，退出码按通过走。本周 Journal 为 0 篇时，这些天仍记入缺漏并拦住，不算豁免。
5. 缺漏不是空的才拦住并提醒。日期篇让 Jake 说「写周记」，走 `journal` skill 落盘。缺的归堆正本按平日 `daily-cluster` 路径补，不新造职责卡。有 Journal 时，`cluster_gaps` 里的日期不走这条拦住。文件入库后，再跑本技能、同一道闸。周六因此被拦的，同周周日可以补跑。闸过才生成。
6. Journal 至少 1 篇：闸过，按现有提炼往下做。`cluster_gaps` 里有日期也闸过，先把缺的日期说出来。Journal 为 0 篇：拦住；这时周一至周五若还有没盖住、又不是空 Inbox 的日子，一并拦住。

周日补跑仍是这一道闸，不是放宽。闸过并已经开始提炼之后，本周不再跑。周日这道闸还不过就停在缺漏清单，不要改到周一补。

验收：正常周六跑闸——本周至少 1 篇 `📝 Journal/{日期}*.md`，即使缺 cluster：退出码 0，`cluster_gaps` 列出缺的日期。本周 0 篇：拦住。0 篇且非豁免日缺 cluster：一并拦住。0 篇且工作日都确认无 Inbox：仍因 0 篇拦住，空日不记成缺归堆。若周六因缺被拦，同周周日允许用同一技能、同一闸补跑一次（不是改成只周日跑）。

## 平日归堆（本技能当天不跑）

想法梳理先把归堆写成文件，再聊天问点头。路径：

- `📋 Digests/cluster/YYYY-MM-DD.md`
- 多日合成：`📋 Digests/cluster/YYYY-MM-DD_DD.md`（例 `2026-10-26_27.md`）

归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`。不是 information-flow Actions 写 vault。本技能不实现这条推送接线。

不碰 `📋 Digests/daily/` 里已有文件，也不接管这条路径。takeaway 已 offline，本 PR 不另挂停排程。`scripts/daily_takeaway.py` 留作 dead code，不在本变更里删除。

## 输入

这一节是本周完整性闸过了之后才读。闸本身不靠 `-gpt` 判断全不全。提炼时正本和 `-gpt` 都读。

只吃已经在库里的文件。聊天里没落盘的稿不吃。

本周按 Asia/Hong_Kong，周一 00:00 到周日 23:59。

1. 本周 `📋 Digests/cluster/` 里的 `YYYY-MM-DD.md`（Grok／想法梳理正本）和 `YYYY-MM-DD-gpt.md`（GPT 线）。多日是 `YYYY-MM-DD_DD.md` 和 `YYYY-MM-DD_DD-gpt.md`。不区分来源。Jake 通常只消化一边，有哪份读哪份。同一天两份都在：两份都读。同一条（同一来源链接、同一段引用、或同一标题）只算一次。同一条两份详略不同，留更详的那份，细节不丢。
2. 本周 `📝 Journal/{YYYY-MM-DD}*.md`。这是 ChatGPT Work 写好并已落入 DigitalBrain 的日期篇。某一篇不在盘上就跳过这一篇。整周 0 篇已经在本周完整性闸拦住，不会进到这里。

`📝 Journal/想法/` 的随手记不是主扫，也不计入本周完整性闸。闸未过就停，见「本周完整性闸」。不要改去 `📋 Digests/daily/`，不要改去 `📋 Digests/cycles/`。

周六这个技能除了 Resources、Ideas、Cognition，还要提炼 plan。从本周 `📝 Journal/{YYYY-MM-DD}*.md` 日期篇，和本周 `📋 Digests/cluster/`（含打了 `plan` 标签的条目）里，把「有执行步骤的未来打算」收成一份 plan 清单。每条四栏：计划、下一步、负责人、来源链接。来源链接指回对应的 cluster 或 Journal 文件。同一遍也可以看这些计划的进度，用来填写或核对「下一步」。不另写一份进度报告。进度和清单都不进 Ideas。Context 段、讨论 log、Journal 里出现的 plan 都收进这一份清单。怎么认 Context 和讨论 log，见下一节。

周六这个技能还要出一份「自媒体选题」（Jake 2026-10-31 美东 11:24 定）。写法、来源、落点见下面「自媒体选题」一节。本周 `📥 Inbox/Trends/` 里的趋势原文可以打开，用来核对参考爆款的链接和数字；它们只当参考，不是 Jake 的料，不能单独出 Idea 或自媒体选题。

## 来源分流

Jake 2026-10-28 ~23:03 HKT 定的。周六先分来源，再决定这段能不能出 Ideas。这一节不改上面的路径，也不把点头闸放宽：Ideas 落盘、Resources 正式入库、Belief、Principle 仍然要 Jake 点头。plan 清单和 Ideas 同一批点头后再交，见「点头」。

Context 和讨论 log 的小节标题还没定。在 Jake 选定固定标题之前，暂时用字样认段，不靠猜标题。

### 暂时用字样认段

本周正本和 `-gpt` 都切段，路径见「输入」。不区分来源。同一天两份都在，先按上面的同日去重，再认段。两份都可以出 Resources、Ideas、plan 或 Cognition，认段规则相同。

**Context**（Inbox 整理 / 未讨论段）。标题或小标题里出现下面任一字样，就先当成 Context：

- `21:00`
- `inbox 新料`
- `每天消化`
- `Part · Inbox`
- `外面在聊什么`（每天消化周二、周五摆的趋势块，原料来自 `📥 Inbox/Trends/`）

同类说法同样算 Context，但必须写明是 Inbox 整理、未讨论、或还没讨论过的收料。对不上这些字样、也没有这层意思的，不要猜成 Context。

**讨论 log**。标题或小标题里出现下面任一字样，就先当成讨论 log：

- `语音整理`
- `深挖`
- `讨论 log`

同类说法同样算讨论 log，但必须写明是语音整理出来的、深挖过的、或标成讨论 log 的。对不上这些字样、也没有这层意思的，不要猜成讨论 log。

同一段两边字样都有：标出来，问 Jake 这段算哪边。他开口之前，这段不出 Ideas。同一内容若另外写在已认出的讨论 log 或 Journal 日期篇里，仍按那两处提 Ideas。

一段对不上上面任一字样：标「认不出」。这段不出 Ideas，也不要为了凑候选把它算进讨论 log。它仍可以当 Resources 候选（和 cluster 里其他收料一样）。同一内容若另外写在已认出的讨论 log 或 Journal 日期篇里，仍按那两处提 Ideas。

Journal 不靠这套字样拆。已落盘的 `📝 Journal/{YYYY-MM-DD}*.md` 整份按下面「讨论 log ＋ Journal」处理。`📝 Journal/想法/` 的随手记仍然不是主扫，不从那里出 Ideas。

### 各来源能出什么

1. **Context**（Inbox 整理 / 未讨论段）→ 最多出 **Resources 候选**。不得只凭 Context 提 Ideas。只在 Context 里出现、讨论 log 和 Journal 都没有的内容，不能写成 Idea。Resources 候选仍是候选，正式入库要 Jake 点头。
2. **讨论 log ＋ Journal** → 只有这两处可以提 **Ideas**。讨论 log 指上面用字样认出的 cluster 段。Journal 指本周已落盘的日期篇。这两处也可以出 Resources 候选。Ideas 的 `source_refs` 要指到讨论 log 那段或 Journal 文件（以及对应 Resources），不能只指 Context。
3. **plan** → 可以扫进度，也可以抽出 plan 清单。不进 Ideas，不调用 `write_idea.py` 写 plan。Context 段里扫到的 plan 也只进清单，不改写成 Idea。清单四栏、交给资料管理员、本技能自己不写 Notion，见「输入」里的 plan 段和「输出」。
4. **趋势**（`📥 Inbox/Trends/` 原文，以及归堆里「外面在聊什么」那块）→ 算 Context。只能当自媒体选题的参考，附在 `source_refs` 后面。不得只凭趋势出 Idea 或自媒体选题：一条趋势要配上讨论 log 或 Journal 里 Jake 自己的料（经历、策略、数字或他说过的看法），才成一条自媒体选题。Jake 在深挖或讨论 log 里聊过某个趋势，那段讨论 log 才是来源，趋势仍只是参考。

## 自媒体选题

Jake 2026-10-31 美东 11:24 定：自媒体选题每条当一个 Idea，原始趋势放 `📥 Inbox/Trends/`。

- 是什么：具体到能开做的一条内容选题，给内容写手立题用。每天消化里只摆方向和切入角度，不给具体选题；具体选题在周六这里出。
- 写到哪：每条一个 Idea，用 `skills/ideas/tools/write_idea.py` 写进 `💡 Ideas/Content/`（调用时 `--directory Content`）。不开子目录，不新开库。它是 Idea，所以不违反下面「plan 不另开第四类库或新目录」那几句。
- 怎么标：`topics` 第一项写 `自媒体选题`，后面每个平台一项，写 `小红书` 或 `X`（可以两个都写）。不写 `公众号`：公众号不另立题，仍从 X 定稿转换（见 content-wechat）。`nature` 统一写 `judgment`，跟下面 Ideas 那行一样。`write_idea.py` 不收新字段，所以标签只放在 `topics` 里，不另加 frontmatter 键。
- 来源：`source_refs` 第一项必须指到本周讨论 log 那段或 Journal 日期篇；趋势文件（`📥 Inbox/Trends/YYYY-MM-DD-xhs-trends.md` 之类）只能附在后面当参考。只有趋势、没有讨论 log 或 Journal 的，不出。
- 每条写什么：`expression` 写 Jake 点头的那句选题；`applicability` 写为什么适合我们（拿 Jake 自己同类内容的数据比）；`context` 写参考爆款（标题｜作者｜赞／藏／评｜封面和钩子｜链接）和可借的写法；`limitations` 写反例和本轮采样局限。数字照抄趋势原文，不编。
- 点头：跟本周其他 Ideas 同一批给 Jake 点头，点头之后才写入；写入之后交内容写手立题。没点头的不写，也不交。
- 闸：跟其他 Ideas 一样受「本周完整性闸」管，闸不过不出。

## 输出

复用现成写入工具，不另写一套。

| 类型 | 路径 | 工具 | 闸 |
| --- | --- | --- | --- |
| Resources | `📖 Resources/` 已有领域目录里的 concept 页（`type: concept`） | 与来源卡相同的写法：`sources` 指回原文件，写 `created` / `updated`，正文至少两个 wikilink，更新 `index.md` 与 `log.md`，不新开分类，不改已有页的类型 | 正式入库须 Jake 点头，或他在同一批里点头。Context 段只出候选，见「来源分流」 |
| Ideas | `💡 Ideas/{Content,Insurance,Life,Tech,Trading}/idea-xxxxxxxxxxxx.md` | `skills/ideas/tools/write_idea.py` | 点头之后。判断用 `nature: judgment`。`source_refs` 写整段引用，指向本周讨论 log 那段或 Journal 日期篇，以及对应 Resources。不能只指 Context |
| 自媒体选题 | `💡 Ideas/Content/idea-xxxxxxxxxxxx.md`（不开子目录） | `skills/ideas/tools/write_idea.py --directory Content` | 跟 Ideas 同一批点头之后。`topics` 写 `自媒体选题`＋平台（`小红书`／`X`），`nature: judgment`。`source_refs` 第一项指讨论 log 那段或 Journal 日期篇，趋势只附在后面当参考。点头写入后交内容写手 |
| Cognition | `📖 Cognition/{Evidence,Beliefs,Principles}/` | `skills/cognition/tools/write_cognition.py` | Evidence 草稿沿用 cognition 现闸。Belief、Principle 须点头 |
| Facts | 另轨，不并进这次提炼 | `skills/facts/tools/write_fact.py` | 本技能不改 Facts 的规则 |
| Plan | Notion「可执行计划清单」（经资料管理员写） | 无。本技能只产出清单，交给资料管理员 | plan 清单展示给 Jake，和 Ideas 同一批点头后再交 |

Ideas 和 Resources 照旧写进 Obsidian（DigitalBrain），不变。plan 不写进 `💡 Ideas/`，也不调用 `write_idea.py` 写 plan，不为 plan 另开第四类库或新目录。本技能自己不写 Notion。在 Grok Bot 里，跑这个技能的那次对话把 plan 清单发给资料管理员，由资料管理员写进 Notion「可执行计划清单」（collection://7e171618-6ac3-49f3-aa57-342e896cd0c1）。

## 互链

- Ideas 的 `source_refs` 与 Resources concept 互指。
- Cognition 的 `origin_ref` / `related_to` 指向相关 Ideas 与 Resources。
- 禁 concept→Evidence。intake 条目和 concept 卡不能直接写成 Evidence。
- 不批量把旧 Journal / Resources 转成 Cognition。无点头不写 Belief、Principle。

## 点头

可自动的只有：本周完整性闸已过之后，读已落盘的 cluster 与 Journal、展示候选（含 plan 清单草案）、按 cognition 现闸留下的 Evidence 草稿和互链草案。闸未过时，连候选都不要展示。plan 清单在点头前只展示，不交给资料管理员。

须点头：Ideas 落盘、Resources 正式入库、Belief、Principle。

plan 清单和 Ideas 同一批给 Jake 点头，点头之后才交给资料管理员写进 Notion，本技能自己不写 Notion。

自媒体选题和 Ideas 同一批给 Jake 点头，点头之后才写入 `💡 Ideas/Content/`、交给内容写手。禁：只凭趋势出自媒体选题；闸未过就出自媒体选题。

禁：平日 right-away；闸未过就生成 idea、resource 或 plan；concept 或 intake→Evidence；没有点头就写 Belief 或 Principle；只凭 Context 出 Ideas；把 plan 写进 Ideas。

## 不要做

- 本周完整性闸未过时，不产出 idea、resource、plan 候选，不调用 `write_idea.py`，不做 Resources 正式入库，不把 plan 清单交给资料管理员。
- 不把周六例程改成只周日跑。平日不补跑。
- 不新建周六 GitHub Action，也不在本仓库接 Cloud Agent 推送。
- 不删 `scripts/daily_takeaway.py`（dead code，另开 hygiene PR 再清）。不写、不改、不接管 `📋 Digests/daily/`。
- 不删除历史 `📋 Digests/cycles/`。
- 不手写 Markdown 绕过 `write_idea.py` 或 `write_cognition.py`。
- 工具找不到或拒绝写入时，停在已点头的草稿上，说明这次没有写入。
- 不从 Context（Inbox 整理 / 未讨论段）单独提 Ideas。认不出是讨论 log 的段，也不出 Ideas。
- 不从 `📥 Inbox/Trends/` 或「外面在聊什么」单独出 Idea 或自媒体选题。不为自媒体选题开子目录或新库。
- 不把带 `plan` 标签的条目或提炼出来的 plan 写进 `💡 Ideas/`（也不调用 `write_idea.py` 写 plan），不另开第四类库或新目录，本技能自己不写 Notion。plan 要提炼成 plan 清单，交给资料管理员写进 Notion。
