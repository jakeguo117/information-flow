---
name: journal
description: Jake 的周记。读旧周记和本周全部 Digest / Journal Brief，启发式讨论后写入 DigitalBrain。说「写周记」「周记」或 /journal 时用。不生成 Digest。
---

# journal

给 Jake 自己用。最终形状见 `references/setup.md`。读文件顺序见 `references/weekly-brief.md`。不要救 Hermes。不要抓 Snipd/YouTube/WeRead 原文。不要跑 intake 脚本，除非他明确说 Digests 缺了要补。

## 口气

中英夹杂、意识流、段落之间用 `---`。有怀疑和压力就写进去。可以用 hhh。不要汇报体、不要正文里的 `##` 小标题、不要「总结」、不要编号清单当正文。标题要像 Jake 会说的话。

## 流程

### 1. 读输入

`VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"`

按 `references/weekly-brief.md` 读。本周 Digest 要**全部**正式篇。跳过文件名含「非正式」「演示」的。`generator: journal-daily-digest` 的每日篇要读。周汇总在 `📊 Journal Briefs/`。没有汇总就把本周 Digest 收成 3–7 条线索。没有 Digest 就只用旧周记，照样开讨论。

缺文件时不要自己去抓源。摄入是 `intake` skill，每天 21:00 跑。

从最近一篇周记标题读出「周记 N」，这篇是 N+1。

### 2. 讨论（写之前必须来回）

不要一上来甩摘要清单。顺序：

1. 先让他把这周的事说完。可以点一下上周还悬着的线，但不要在他说完之前用 Digest 来 reflect。Digest 先只读、不上场。
2. 他说「这周就这些」或明确讲完之后，再拿本周划线/点赞去对刚才讲的事。对不上的略过。
3. 对上之后再往下挖。一次不要堆很多题。
4. 他没说讲完、没说可以写之前，不落盘。

禁止：把 Digest 原文贴进周记；没讨论就写完整篇；定时任务代写；他这周的事还没说完就开始用 Digest 解释他。

### 3. 落盘

路径：`$VAULT/📝 Journal/{YYYY-MM-DD} {中文标题}.md`

文件名只要日期 + 空格 + 标题。frontmatter 的 title 可以是 `周记 {N} — …`。

```markdown
---
date: {YYYY-MM-DD}
type: journal
tags:
  - journal
title: "周记 {N} — {Jake 口气的一句}"
---

# 周记 {N} — {同上}

{意识流正文。段落之间 --- 。自然提到旧周记。结尾随便看一眼下周。}

---
## Connections / 关联
**Topics / 主题:**
{相关 [[wikilink]]}

**Previous / 上一篇:** [[{上一篇文件名不含 .md}]]
```

用文件工具写。不要 `git commit` / `git push` DigitalBrain，除非 Jake 这轮明确说 push。不要把周记正文写入 DigitalBrain memory。

### 4. 给他看

告诉他文件路径，问要不要改。要改就改文件，仍不自动 push。

## 不要做

- 不要读 Journal 以外的私人目录来「补这周发生了什么」
- 不要同步 Notion
- 不要把 Claude/Codex/Hermes 那几份旧 skill 一并改掉
- 不要在没授权时改公开 GitHub `journal-skill`
