---
name: discuss-to-resources-ideas
description: 周六把本周已落盘的归堆和日期篇提炼成 Resources、Ideas、Cognition 互链。想法梳理在周六加载。平日 cluster 或 Journal 落盘当下不跑。只吃库内文件。不写、不扫、不接管 📋 Digests/daily/。
---

# discuss-to-resources-ideas

Jake 2026-10-28 批的方案纸 v2 用本技能做每周提炼。方案纸原文把归堆写成 `📋 Digests/daily/`。该路径与 takeaway 脚本的输出撞车，PM 定归堆改为 `📋 Digests/cluster/`。takeaway 已 offline，本 PR 不另挂停排程。Jake 可以再改路径；在改口之前以 cluster 为准。

本文件只定路径和闸。不在 information-flow 里接 Cloud Agent，也不新开把归堆推进库的 Action。

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

1. 本周 `📋 Digests/cluster/` 下的 `YYYY-MM-DD.md` 与 `YYYY-MM-DD_DD.md`。
2. 本周 `📝 Journal/{YYYY-MM-DD}*.md`。这是 ChatGPT Work 写好并已落入 DigitalBrain 的日期篇。盘上没有该文件就跳过。

`📝 Journal/想法/` 的随手记不是主扫。没有 cluster、也没有符合的 Journal 文件：停。不要编 Resources 或 Ideas。不要改去 `📋 Digests/daily/`，不要改去 `📋 Digests/cycles/`。

## 输出

复用现成写入工具，不另写一套。

| 类型 | 路径 | 工具 | 闸 |
| --- | --- | --- | --- |
| Resources | `📖 Resources/` 已有领域目录里的 concept 页（`type: concept`） | 与来源卡相同的写法：`sources` 指回原文件，写 `created` / `updated`，正文至少两个 wikilink，更新 `index.md` 与 `log.md`，不新开分类，不改已有页的类型 | 正式入库须 Jake 点头，或他在同一批里点头 |
| Ideas | `💡 Ideas/{Content,Insurance,Life,Tech,Trading}/idea-xxxxxxxxxxxx.md` | `skills/ideas/tools/write_idea.py` | 点头之后。判断用 `nature: judgment`。`source_refs` 写整段引用，指向本周 cluster 或 Journal，以及对应 Resources |
| Cognition | `📖 Cognition/{Evidence,Beliefs,Principles}/` | `skills/cognition/tools/write_cognition.py` | Evidence 草稿沿用 cognition 现闸。Belief、Principle 须点头 |
| Facts | 另轨，不并进这次提炼 | `skills/facts/tools/write_fact.py` | 本技能不改 Facts 的规则 |

## 互链

- Ideas 的 `source_refs` 与 Resources concept 互指。
- Cognition 的 `origin_ref` / `related_to` 指向相关 Ideas 与 Resources。
- 禁 concept→Evidence。intake 条目和 concept 卡不能直接写成 Evidence。
- 不批量把旧 Journal / Resources 转成 Cognition。无点头不写 Belief、Principle。

## 点头

可自动的只有：读已落盘的 cluster 与 Journal、展示候选、按 cognition 现闸留下的 Evidence 草稿和互链草案。

须点头：Ideas 落盘、Resources 正式入库、Belief、Principle。

禁：平日 right-away；concept 或 intake→Evidence；没有点头就写 Belief 或 Principle。

## 不要做

- 不新建周六 GitHub Action，也不在本仓库接 Cloud Agent 推送。
- 不删 `scripts/daily_takeaway.py`（dead code，另开 hygiene PR 再清）。不写、不改、不接管 `📋 Digests/daily/`。
- 不删除历史 `📋 Digests/cycles/`。
- 不手写 Markdown 绕过 `write_idea.py` 或 `write_cognition.py`。
- 工具找不到或拒绝写入时，停在已点头的草稿上，说明这次没有写入。
