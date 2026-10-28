---
name: digest
description: 看本周汇总。Jake 说「看本周汇总」「本周汇总」「本周 digest」或 /digest 时用。周四 weekly-digest schedule 已停；只读归档里的周四快照，按主题列全量，保留 D-{cycle}-{nn}。不把周四接受写成每周来源卡。不写周记，不写 Cognition。平日归堆是 📋 Digests/cluster/，周六提炼走 discuss-to-resources-ideas。
---

# digest

看归档里的周四快照。不把 Inbox 当讨论材料。周四 `📋 Digests/cycles/` 自动跑已停。`.github/workflows/weekly-digest.yml` 没有 schedule，只留 `workflow_dispatch` 救急。历史 cycle 不删。本技能不生成新 cycle。

平日归堆落盘是 `📋 Digests/cluster/YYYY-MM-DD.md`（多日 `YYYY-MM-DD_DD.md`）。写的人是想法梳理。归堆推库＝Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`，不是 information-flow Actions 写 vault。本技能不写 cluster，也不接这条推送。

`📋 Digests/daily/` 是 takeaway 的历史路径。takeaway 已 offline，本 PR 不另挂停排程。`scripts/daily_takeaway.py` 留作 dead code，本变更不删。不改、不接管历史 daily 文件，也不把 daily 当归堆。

周六由想法梳理加载 `discuss-to-resources-ideas`，扫本周 `📋 Digests/cluster/` 和已落盘的 `📝 Journal/{YYYY-MM-DD}*.md`。那才是每周 Resources／Ideas／Cognition 提炼。平日 cluster 或 Journal 落盘当下不跑那个技能。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。云端只读 main 上已有快照，不生成快照，不写 token。

## 什么时候用

Jake 说「看本周汇总」「本周汇总」「本周 digest」或 `/digest`，以及同类说法，用本技能。只列归档。不据此写每周来源卡。

## 读什么

读最新一份周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`。同一个 cycle 取最大的 n。

怎么找最新：在 vault 下看 `📋 Digests/cycles/`。目录名是 `cycle_id`，形式 `cy-YYYYMMDD`，这一天必须是周四。在符合的目录里取日期最新的一个，再取里面编号最大的 `r{n}.md`（n 按整数比）。

没有这份快照：说明还没有。不要编条目。不要回落到 `📋 Digests/daily/`，不要回落到旧的 `📋 Digests/{YYYY-Wnn}/digest.md`，也不要按周去读 intake。不要把 `📋 Digests/cluster/` 冒充周四快照。

## 怎么列

列全量。按 `topics` 分主题。没有主题的放在「待归类」。每条带 `process_state`。编号保留快照里的 `D-{cycle}-{nn}`，不要重编。可以按快照正文简述每条摘要和来源链接。

## 落盘

本技能不把周四接受写成每周来源卡。Jake 接受之前，不写 `📖 Resources/`。每周提炼在周六 `discuss-to-resources-ideas`：正式 Resources 仍要他点头，Ideas／Belief／Principle 也要他点头。Resource 页不是 Evidence。

不写周记，不写 Cognition，不新开分类。不改 `📝 Journal/`。

保存别的受管文件时仍走仓库当前规则：精确路径，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。
