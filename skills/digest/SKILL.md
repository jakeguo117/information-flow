---
name: digest
description: 讨论昨天的 Inbox 摘要。Jake 说「今天 Digest」「讨论昨天」「跑 Digest」或 /digest 时用。先提出最多两个概念，他接受之前不写 Resource。不写周记。
---

# digest

每天讨论前一个上海日的 Inbox。五个入口都在 `📥 Inbox/`：Snipd、WeRead、YouTube-Likes、Instagram-Saves、X-Bookmarks。Agent Handoffs 不进讨论。按周累积的旧入口只是历史，不要打开它当今天的材料，也不要往里追加。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。云端只读已经在 `main` 上的摘要，不跑 YouTube 脚本，不写 token。

## 读什么

用 Asia/Shanghai 的昨天。打开 `📋 Digests/daily/YYYY-MM-DD.md`。

这份文件不在 `main` 上：停下来，说明当天摘要还没有。不要自己编条目，不要改去读按周累积的旧入口。

## 讨论

从这份摘要提出最多两个概念。一个概念可以挂上多条原文。先说概念和它对应的原文，不要先写文件。

Jake 接受之前不写 `📖 Resources/`。没接受的概念不落盘。他说接受哪一个，才写哪一个。

## 接受之后

写到 `📖 Resources/` 已有的领域目录里，不要新开一套分类。

- frontmatter 用 `type: concept`，`sources` 指回 Inbox 原文，并写 `created` / `updated`
- 正文至少两个 wikilink
- 把新页加进 `index.md`，并在 `log.md` 追加一行
- 不改已有页的类型
- 保存时走仓库当前规则：精确路径，禁止 `git add -A`。只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推。Resource 页是修改，不直推 main。

不改 `📝 Journal/`。不写 `📖 Cognition/`。不把 Resource 页改类型当成 Cognition。

Resource 页不是 Evidence。
