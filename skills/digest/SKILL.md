---
name: digest
description: 看本周汇总。Jake 说「看本周汇总」「本周汇总」「本周 digest」或 /digest 时用。读最新一份周四快照，按主题列全量，带 process_state，保留 D-{cycle}-{nn}。接受之后才写他点名的来源卡。不写周记，不写 Cognition。
---

# digest

看本周汇总。打开最新一份周四快照，把里面的条目按主题列全。不把 Inbox 当讨论材料。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。云端只读 main 上已有快照，不生成快照，不写 token。

## 什么时候用

Jake 说「看本周汇总」「本周汇总」「本周 digest」或 `/digest`，以及同类说法，用本技能。

## 读什么

读最新一份周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`。同一个 cycle 取最大的 n。

怎么找最新：在 vault 下看 `📋 Digests/cycles/`。目录名是 `cycle_id`，形式 `cy-YYYYMMDD`，这一天必须是周四。在符合的目录里取日期最新的一个，再取里面编号最大的 `r{n}.md`（n 按整数比）。

没有这份快照：说明还没有。不要编条目。不要回落到 `📋 Digests/daily/`，不要回落到旧的 `📋 Digests/{YYYY-Wnn}/digest.md`，也不要按周去读 intake。

## 怎么列

列全量。按 `topics` 分主题。没有主题的放在「待归类」。每条带 `process_state`。编号保留快照里的 `D-{cycle}-{nn}`，不要重编。可以按快照正文简述每条摘要和来源链接。

## 落盘

Jake 接受之前，落盘只允许写来源卡（`📖 Resources/` 已有领域目录里的 concept 页）。不写周记，不写 Cognition，不新开分类。接受之后才写他点名的来源卡。

来源卡写在 `📖 Resources/` 已有的领域目录里：

- frontmatter 用 `type: concept`，`sources` 指回 Inbox 原文，并写 `created` / `updated`
- 正文至少两个 wikilink
- 把新页加进 `index.md`，并在 `log.md` 追加一行
- 不改已有页的类型

保存时走仓库当前规则：精确路径，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。Resource 页是修改，不直推 main。

不改 `📝 Journal/`。Resource 页不是 Evidence。
