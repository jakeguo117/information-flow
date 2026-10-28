---
name: discuss-to-resources-ideas
description: 周六把本周已落盘的归堆和日期篇提炼成 Resources、Ideas、Cognition 互链，并抽出 plan 清单交给资料管理员。Context 段最多出 Resources 候选；Ideas 只从讨论 log 和 Journal 来；plan 不进 Ideas。想法梳理在周六加载。平日 cluster 或 Journal 落盘当下不跑。只吃库内文件。不读 *-gpt.md。不写、不扫、不接管 📋 Digests/daily/。
---

# discuss-to-resources-ideas

Jake 2026-10-28 批的方案纸 v2 用本技能做每周提炼。方案纸原文把归堆写成 `📋 Digests/daily/`。该路径与 takeaway 脚本的输出撞车，PM 定归堆改为 `📋 Digests/cluster/`。takeaway 已 offline，本 PR 不另挂停排程。Jake 可以再改路径；在改口之前以 cluster 为准。

本文件只定路径、来源分流和闸。不在 information-flow 里接 Cloud Agent，也不新开把归堆推进库的 Action。

## 谁、何时

- 加载者：想法梳理。
- 何时：每周六一次。例程以后再接。平日不跑。
- 硬禁：平日 `📋 Digests/cluster/` 或 `📝 Journal/` 落盘当下 right-away 跑本技能。digest、journal、intake 不在落盘当下调用本技能。
- 周四 `weekly-digest.yml` 的 schedule 已停。`📋 Digests/cycles/` 是归档，不是本技能的输入，也不要为了周六去生成新 cycle。

## 平日归堆（本技能当天不跑）

想法梳理先把归堆写成文件，再聊天问点头。路径：

- `📋 Digests/cluster/YYYY-MM-DD.md`
- 多日合成：`📋 Digests/cluster/YYYY-MM-DD_DD.md`（例 `2026-10-26_27.md`）

归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`。不是 information-flow Actions 写 vault。本技能不实现这条推送接线。

不碰 `📋 Digests/daily/` 里已有文件，也不接管这条路径。takeaway 已 offline，本 PR 不另挂停排程。`scripts/daily_takeaway.py` 留作 dead code，不在本变更里删除。

## 输入

只吃已经在库里的文件。聊天里没落盘的稿不吃。

本周按 Asia/Hong_Kong，周一 00:00 到周日 23:59。

1. 本周 `📋 Digests/cluster/` 下的 `YYYY-MM-DD.md` 与 `YYYY-MM-DD_DD.md`。不读 `*-gpt.md`，只读这些主 cluster 文件。
2. 本周 `📝 Journal/{YYYY-MM-DD}*.md`。这是 ChatGPT Work 写好并已落入 DigitalBrain 的日期篇。盘上没有该文件就跳过。

`📝 Journal/想法/` 的随手记不是主扫。没有 cluster、也没有符合的 Journal 文件：停。不要编 Resources 或 Ideas。不要改去 `📋 Digests/daily/`，不要改去 `📋 Digests/cycles/`。

周六这个技能除了 Resources、Ideas、Cognition，还要提炼 plan。从本周 `📝 Journal/{YYYY-MM-DD}*.md` 日期篇，和本周 `📋 Digests/cluster/`（含打了 `plan` 标签的条目）里，把「有执行步骤的未来打算」收成一份 plan 清单。每条四栏：计划、下一步、负责人、来源链接。来源链接指回对应的 cluster 或 Journal 文件。同一遍也可以看这些计划的进度，用来填写或核对「下一步」。不另写一份进度报告。进度和清单都不进 Ideas。Context 段、讨论 log、Journal 里出现的 plan 都收进这一份清单。怎么认 Context 和讨论 log，见下一节。

## 来源分流

Jake 2026-10-28 ~23:03 HKT 定的。周六先分来源，再决定这段能不能出 Ideas。这一节不改上面的路径，也不把点头闸放宽：Ideas 落盘、Resources 正式入库、Belief、Principle 仍然要 Jake 点头。plan 清单和 Ideas 同一批点头后再交，见「点头」。

Context 和讨论 log 的小节标题还没定。在 Jake 选定固定标题之前，暂时用字样认段，不靠猜标题。

### 暂时用字样认段

只切本周 cluster 主文件里的段：`📋 Digests/cluster/YYYY-MM-DD.md` 和 `YYYY-MM-DD_DD.md`。`*-gpt.md` 整份不读。不拿 gpt 文件认段，也不拿它出 Resources、Ideas、plan 或 Cognition。

**Context**（Inbox 整理 / 未讨论段）。标题或小标题里出现下面任一字样，就先当成 Context：

- `21:00`
- `inbox 新料`
- `每天消化`
- `Part · Inbox`

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

## 输出

复用现成写入工具，不另写一套。

| 类型 | 路径 | 工具 | 闸 |
| --- | --- | --- | --- |
| Resources | `📖 Resources/` 已有领域目录里的 concept 页（`type: concept`） | 与来源卡相同的写法：`sources` 指回原文件，写 `created` / `updated`，正文至少两个 wikilink，更新 `index.md` 与 `log.md`，不新开分类，不改已有页的类型 | 正式入库须 Jake 点头，或他在同一批里点头。Context 段只出候选，见「来源分流」 |
| Ideas | `💡 Ideas/{Content,Insurance,Life,Tech,Trading}/idea-xxxxxxxxxxxx.md` | `skills/ideas/tools/write_idea.py` | 点头之后。判断用 `nature: judgment`。`source_refs` 写整段引用，指向本周讨论 log 那段或 Journal 日期篇，以及对应 Resources。不能只指 Context |
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

可自动的只有：读已落盘的 cluster 与 Journal、展示候选（含 plan 清单草案）、按 cognition 现闸留下的 Evidence 草稿和互链草案。plan 清单在点头前只展示，不交给资料管理员。

须点头：Ideas 落盘、Resources 正式入库、Belief、Principle。

plan 清单和 Ideas 同一批给 Jake 点头，点头之后才交给资料管理员写进 Notion，本技能自己不写 Notion。

禁：平日 right-away；concept 或 intake→Evidence；没有点头就写 Belief 或 Principle；只凭 Context 出 Ideas；读 `*-gpt.md`；把 plan 写进 Ideas。

## 不要做

- 不新建周六 GitHub Action，也不在本仓库接 Cloud Agent 推送。
- 不删 `scripts/daily_takeaway.py`（dead code，另开 hygiene PR 再清）。不写、不改、不接管 `📋 Digests/daily/`。
- 不删除历史 `📋 Digests/cycles/`。
- 不手写 Markdown 绕过 `write_idea.py` 或 `write_cognition.py`。
- 工具找不到或拒绝写入时，停在已点头的草稿上，说明这次没有写入。
- 不读 `*-gpt.md`。不从 Context（Inbox 整理 / 未讨论段）单独提 Ideas。认不出是讨论 log 的段，也不出 Ideas。
- 不把带 `plan` 标签的条目或提炼出来的 plan 写进 `💡 Ideas/`（也不调用 `write_idea.py` 写 plan），不另开第四类库或新目录，本技能自己不写 Notion。plan 要提炼成 plan 清单，交给资料管理员写进 Notion。
