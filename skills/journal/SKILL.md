---
name: journal
description: Jake 的周记与随手想法。说「想法」「听完播客的一些感想」「先记一下」「追加到周记」「写周记」「周记」或 /journal 时用。想法收尾时按已保存授权追加素材并同步 main；正式周记先讨论、获准后写。不生成 Digest。
---

# journal

给 Jake 自己用。最终形状见 `references/setup.md`。读文件顺序见 `references/weekly-brief.md`。不要救 Hermes。不要抓 Snipd/YouTube/WeRead 原文。不要跑 intake 脚本，除非他明确说本周 intake 缺了要补。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。

## 口气

中英夹杂、意识流、段落之间用 `---`。有怀疑和压力就写进去。可以用 hhh。不要汇报体、不要正文里的 `##` 小标题、不要「总结」、不要编号清单当正文。标题要像 Jake 会说的话。

## 想法素材：讨论收尾后保存与同步

将随手想法与正式周记成文区分。进入本 skill 后，读取 DigitalBrain `📝 Journal/素材/同步约定.md`（若存在），核验当前有效的保存／推送授权；本轮用户的明确指示优先。授权不存在时，不推断长期自动推送权限。

- 触发：Jake 明确收尾，例如「先记一下」「就这样吧」「之后周记再聊」。用户仍在展开时继续听；沉默、关闭应用或助手自行结束不算触发。按约定有持续授权时，执行保存和同步，不重复索要「写吧」或 push 确认。
- 以 Asia/Shanghai 的事件日期确定 ISO 周，将本次用户表达和澄清追加到 `📝 Journal/素材/YYYY-Www.md`；没有就创建。使用 `type: journal-material`，不占正式「周记 N」编号。不要把本周素材回落到旧 intake 的周。
- 每条包含稳定的 `event_id` 注释、日期、用户口吻正文、来源链接及原文核验状态；保留假设、未确定处与用户修正。助手提出但用户未接受的观点不得写成用户信念。
- 素材使用可用文件工具或 GitHub 内容 API 追加；这是独立素材入口，不调用只接受正式周记审批的 `write_journal.py`，也不伪造该工具的批准短语。正式周记继续走下文的成文审批和工具。
- 写前读取现有完整文件及版本，保留历史条目；同一 event_id 与内容相同则不重复写。用户新增补充使用新的事件条目并关联原事件。已有 event_id 内容冲突时保留双方版本、先报告，不覆盖。
- 仅在有效授权的私有仓库、路径和分支范围内 commit／push；使用 GitHub API 的提交等效于推送。仅提交目标文件，禁止强推、批量暂存、改权限、删除历史或将私人素材写进 information-flow。
- 有本机 vault 时精确路径提交并正常快进推送；没有本机 vault 时，若已知且获授权的 DigitalBrain 仓库可通过 GitHub 连接读取，则核实身份与 main 后直接使用该连接。不可因只缺本机目录就宣布无法同步。无法确认目标时再问。
- 使用当前 blob SHA 更新；多文件提交基于最新 tree，更新 main 时带 expected_sha 且 force=false。冲突后只读重新核对并保留并发追加；结果不明先读回，禁止盲目重复写。
- 提交后从 main 读回目标全文、核对本次事件及 commit，成功才说已同步；失败保留材料并说明尚未上 main。最终简短返回笔记链接和结果。
- 这是一条正在进行的会话收尾流程，不是后台监听器；没有新的运行会话时不能声称仍会自动执行。授权不包括自动发表内容、Cognition 入库或未经确认写成完整周记。

## 流程

### 1. 读输入

Vault 目录（按这个顺序认，认到就停）：

1. `$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain` 若存在且有 `📝 Journal/`
2. 当前工作区根目录，若有 `📝 Journal/`（Cursor 云端 clone 的 GitHub DigitalBrain）
3. 本机目录不可用时，若用户已指定或可从当前授权确认 DigitalBrain GitHub 仓库，则核验后经连接读取 main；不可猜路径。素材可依上节直接写回。正式周记需将必需文件和写入工具带入临时工作副本，运行工具后再依授权同步。
4. 两种入口均不可用或目标不明时再问 Jake。

按 `references/weekly-brief.md` 读。先旧周记和已经挂上的老项目 / 小线。**自己认周**：Asia/Shanghai 当天的 ISO 周，没有文件就回落到 `📋 Digests/` 里已有的最近一周。不要问他是哪一周。再拿那一周 `intake.md` 里 **`[x]`** 的条目和已有 Resource 卡片去对呼应。未勾选的当索引略过，即使标题和旧线相关，也不进入这篇周记的材料。新的来源渠道样本同样先作为未勾选条目，不因为渠道名字新就落盘。周记 Connections 链已经进 `📖 Resources/` 的卡片，不再拦一道入库。

缺文件时不要自己去抓源。摄入是 `intake` skill，每天 21:00 跑。

从最近一篇正式周记标题读出「周记 N」，这篇是 N+1。排除 `📝 Journal/素材/` 和 `type: journal-material`。按 weekly-brief 读取用户已经保存的素材，供这次周记讨论接续。

### 2. 讨论（写之前必须来回）

不要一上来甩摘要清单。不要整周 appendix。顺序：

1. 先读最近 2–3 篇周记，以及那些篇里已经点名的 `🚀 Projects/` / Resource（老项目、很小的未收线）。点一下还悬着的线。intake 先只读、不上场。
2. 听他这周的画像。他说「这周就这些」或明确讲完之前，不要用本周 intake 解释他。
3. 再拿刚解析出的那一周 **已勾选** 的 intake 条目 / Resource 卡片去找 **呼应**。对不上的略过。未勾选的不要当成结论。
4. 对上之后再往下挖。一次不要堆很多题。
5. **正式周记成文在客户说「可以写 / 写吧 / OK 写」之前，不落盘。** 他说「写周记」只是开始讨论，不是授权出文。

禁止：把 intake 原文贴进周记；没讨论就写完整篇；定时任务代写；他这周的事还没说完就开始用 intake 解释他。正式周记不默认自动 push；随手想法素材按上节及持续授权同步。

### 3. 落盘

本节只处理正式周记成文，素材按上面的独立入口处理。正式周记只在他说可以写之后，持久写入只走工具，不要手写文件绕过确认：

```bash
python3 skills/journal/tools/write_journal.py save --vault "$VAULT" --approval FILE
python3 skills/journal/tools/write_journal.py retry --vault "$VAULT" --approval FILE
```

`FILE` 是这一次的 JSON。`confirmed` 必须是 true，并且 `phrase` 必须正好是 `可以写`、`写吧` 或 `OK 写`。「写周记」只是开始讨论，不是这句短语。不符合时工具返回 `refused`，写入数为 0，不创建 `📝 Journal/`。同一 `event_id` 重复送达只保留 1 份；内容不一致则 `conflict`，不覆盖。`retry` 在磁盘已有相同内容时直接读回，不另写一篇。工具不写 `📖 Cognition/`，不 `git commit` / `git push`。

路径：`$VAULT/📝 Journal/{YYYY-MM-DD} {中文标题}.md`

文件名只要日期 + 空格 + 标题。frontmatter 的 title 可以是 `周记 {N} — …`。

```markdown
---
date: {YYYY-MM-DD}
type: journal
tags:
  - journal
title: "周记 {N} — {Jake 口气的一句}"
event_id: {这一次保存的事件 id}
---

# 周记 {N} — {同上}

{意识流正文。段落之间 --- 。自然提到旧周记。结尾随便看一眼下周。}

---
## Connections / 关联
**Topics / 主题:**
{相关 [[wikilink]]}

**Previous / 上一篇:** [[{上一篇文件名不含 .md}]]
```

正文由上面的 `write_journal.py` 落盘，不要另用文件工具绕过它。正式周记篇章不要 `git commit` / `git push` DigitalBrain，除非 Jake 这轮明确说 push；随手想法素材另按上节有效持续授权。不要把周记正文写入 DigitalBrain memory。模板里的 `event_id` 由工具写入 frontmatter，用来识别同一次保存。

### 4. 给他看

告诉他文件路径，问要不要改。要改就改文件，仍不自动 push。

### 5. 写完之后交给 cognition propose

周记已经落盘，或一次反思已经明确收束之后，可以交给 `cognition` skill 做 propose（0–3 条，0 也合法）。**Journal 不写 `📖 Cognition/`。** 接受、改写、校验、落盘只走 cognition tools。

## 不要做

- 不要为了「补这周发生了什么」去扫 Journal 以外的私人目录。可以读取用户已保存的 `📝 Journal/素材/`；项目／卡片只跟旧周记已经出现的 wikilink 打开
- 不要同步 Notion
- 不要把 Claude/Codex/Hermes 那几份旧 skill 一并改掉
- 不要用已删除的公开仓 `jakeguo117/journal-skill`；只跟 information-flow
