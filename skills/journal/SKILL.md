---
name: journal
description: Jake 的周记，以及「记一下：」「想法：」/thought 的随手记。先读旧周记和已挂上的老项目，找呼应后再讨论；客户说 OK 之前不写周记。说「写周记」「周记」或 /journal 时用。随手记不分析、不追问。不生成 Digest。
---

# journal

给 Jake 自己用。最终形状见 `references/setup.md`。读文件顺序见 `references/weekly-brief.md`。随手记的文件布局、消化清单和自动推送见 `references/thoughts.md`。不要救 Hermes。不要抓 Snipd/YouTube/WeRead 原文。不要跑 intake 脚本，除非他明确说本周 intake 缺了要补。

## 随手记

只在他说「记一下：」「想法：」或 `/thought` 时记。普通聊天不记。触发词后面的内容是一条，原样保存，不拆句、不去空格、不改标点。不分析、不追问、不查旧周记、不写 Cognition、不进 Ideas / Experiments。

一条一个新文件。不改、不删已有文件。vault 里已经有的 `📝 Journal/素材/2026-W41.md` 和 `📝 Journal/素材/同步约定.md` 保持原样，不删除、不修改。`同步约定.md` 不再是持续授权。不要往 `📝 Journal/素材/` 写任何新内容。想法只写入 `📝 Journal/想法/`，按这一节。

```bash
python3 skills/journal/tools/capture_thought.py add --vault "$VAULT" --text-file FILE --publish
```

`FILE` 里只有原话。`publish` 只暂存这一个新文件并推到 `main`。暂存区里的差异必须全是 `A`（只新增）。有修改、删除或重命名就不推，也不强推。路径已经在 `main` 上，不推。别的未跟踪想法文件可以留着，这次只提交这一条。周记正文仍然不自动 push。

本地 `main` 只是落后 `origin/main`（例如 08:00 的日摘要已经推上去），并且工作区没有已跟踪文件的修改时，`publish` 会先 `git fetch`，再 `git merge --ff-only --no-overwrite-ignore origin/main`。被忽略的本地文件若会被盖住，快进拒绝，本地文件留着。本地已经有没推的提交、远端也前进了时：每一笔都只新增想法文件或消化清单，且这些路径在 `origin/main` 上还不存在，就把它们重放到 `origin/main` 再普通推送。有修改、删除、合并，或路径已经在 `origin/main` 上，就不重放，退出码 2。不强推。

只有这一步的退出码是 0、并且状态是成功，才说「记了」，并把原话原样给他看。推送或 publish 因任何原因失败（没有 git、没有推送权限、网络、工作区不干净、工具拒绝、路径已在 main、提交里有修改或删除、快进不了），都要清楚告诉他「没存上」，给一个短原因，再把他的原话原样念回去，让他自己留着。不要说已经存上，也不要说「记了」。

没存上之后：退出码 4 是 git 不在 PATH，或 git 调用本身报了网络失败，文件还在本地。不靠异常消息里的词来判断。远端如果没动，网络恢复后可以对同一路径 `publish`。远端如果已经前进（竞态，或断网之后赶上 08:00 日摘要），「对同一路径再 publish」本身不是恢复办法：只新增且路径还不在 origin 上时，工具会重放后再推。条件不满足时退出码 2。挡路的是修改、删除、重命名、合并、路径已在 origin 上或内容不合格时，reason 不给 push 命令：把这些提交移到 task branch 开 PR，或交给 Jake，例子是 `git branch task/thought-recovery HEAD && git reset --keep origin/main`，不推 main。分支已经建好、但 `reset --keep` 失败时，只再跑 `git reset --keep origin/main`。校验已经通过、失败出在 git 重放本身时，reason 也不给 push 命令：先排除原因，再重新 `publish`，让工具重新校验后推送。如果 rebase 停在半路，运行 `git rebase --abort`。退出码 3 是远端拒绝，不要强推。退出码 2 是门禁拒绝，reason 里会点名路径或提交；别人暂存的修改或删除留在原地，不要为了推想法把周记一起提交。退出码 5 是工具自己的异常，reason 是异常类名和消息，原话仍在 verbatim 里，这不是 git 不可用。

DigitalBrain `.cursor/skills/` 里的副本由 information-flow Actions 覆盖。改行为只改这个仓库。

## 口气

中英夹杂、意识流、段落之间用 `---`。有怀疑和压力就写进去。可以用 hhh。不要汇报体、不要正文里的 `##` 小标题、不要「总结」、不要编号清单当正文。标题要像 Jake 会说的话。

## 流程

### 1. 读输入

Vault 目录（按这个顺序认，认到就停）：

1. `$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain` 若存在且有 `📝 Journal/`
2. 当前工作区根目录，若有 `📝 Journal/`（Cursor 云端 clone 的 GitHub DigitalBrain）
3. 否则停下来问 Jake，不要猜路径

按 `references/weekly-brief.md` 读。先旧周记和已经挂上的老项目 / 小线。**自己认周**：Asia/Shanghai 当天的 ISO 周，没有文件就回落到 `📋 Digests/` 里已有的最近一周。不要问他是哪一周。再拿那一周 `intake.md` 里 **`[x]`** 的条目和已有 Resource 卡片去对呼应。未勾选的当索引略过，即使标题和旧线相关，也不进入这篇周记的材料。新的来源渠道样本同样先作为未勾选条目，不因为渠道名字新就落盘。周记 Connections 链已经进 `📖 Resources/` 的卡片，不再拦一道入库。

再跑 `capture_thought.py list-open`。它返回的是全部未消化想法，不限本周。未消化 = `📝 Journal/想法/` 里的想法文件，减去任何消化清单里出现过的 id。清单里标成「看过未展开」的不再出现。想法文件和消化清单都不是周记条目。

缺文件时不要自己去抓源。摄入是 `intake` skill，每天 21:00 跑。

从最近一篇周记标题读出「周记 N」，这篇是 N+1。

### 2. 讨论（写之前必须来回）

不要一上来甩摘要清单。不要整周 appendix。顺序：

1. 先读最近 2–3 篇周记，以及那些篇里已经点名的 `🚀 Projects/` / Resource（老项目、很小的未收线）。点一下还悬着的线。intake 先只读、不上场。
2. 听他这周的画像。他说「这周就这些」或明确讲完之前，不要用本周 intake 解释他。
3. 再拿刚解析出的那一周 **已勾选** 的 intake 条目 / Resource 卡片，以及 `list-open` 的未消化想法，去找 **呼应**。对不上的略过。未勾选的不要当成结论。想法是燃料，不整段贴进周记，也不改原话。
4. 对上之后再往下挖。一次不要堆很多题。讨论时记下每条想法是「展开」还是「看过未展开」。没被展开的也要记下，以后不再捞。
5. **客户说「可以写 / 写吧 / OK 写」之前，不落盘。** 他说「写周记」只是开始讨论，不是授权出文。

禁止：把 intake 原文贴进周记；没讨论就写完整篇；定时任务代写；他这周的事还没说完就开始用 intake 解释他。不自动 git push 周记。

### 3. 落盘

只在他说可以写之后。持久写入只走工具，不要手写文件绕过确认：

```bash
python3 skills/journal/tools/write_journal.py save --vault "$VAULT" --approval FILE
python3 skills/journal/tools/write_journal.py retry --vault "$VAULT" --approval FILE
```

`FILE` 是这一次的 JSON。`confirmed` 必须是 true，并且 `phrase` 必须正好是 `可以写`、`写吧` 或 `OK 写`。「写周记」只是开始讨论，不是这句短语。不符合时工具返回 `refused`，写入数为 0，不创建 `📝 Journal/`。同一 `event_id` 重复送达只保留 1 份；内容不一致则 `conflict`，不覆盖。`retry` 在磁盘已有相同内容时直接读回，不另写一篇。工具不写 `📖 Cognition/`，不 `git commit` / `git push`。周记文件本身仍不自动 push。

`write_journal.py` 返回 `success` 之后，才把这次 `list-open` 的每一条写进一份新的消化清单。失败、拒绝、冲突都不写清单，那些想法下次还能捞到。清单必须正好覆盖当前未消化的 id，每条是 `展开` 或 `看过未展开`，并链到这篇周记。不改旧的想法文件，也不在旧文件上打勾。

```bash
python3 skills/journal/tools/capture_thought.py record-digest \
  --vault "$VAULT" --journal-result RESULT.json --dispositions DISPOSITIONS.json
python3 skills/journal/tools/capture_thought.py publish \
  --vault "$VAULT" --path '📝 Journal/想法/digests/digest-….md'
```

消化清单也是新文件，写入成功后用同一条 `publish` 规则只推这一个路径。周记文件还躺在工作区里时，`publish` 会拒绝，这是对的：不要为了推清单把周记一起提交。清单留在本地，等工作区里除了这份清单没有别的改动，再单独 `publish`。没有未消化想法时不创建空清单。

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

正文由上面的 `write_journal.py` 落盘，不要另用文件工具绕过它。不要把周记正文 `git commit` / `git push`，除非 Jake 这轮明确说 push。想法文件和消化清单只走 `capture_thought.py publish`。不要把周记正文写入 DigitalBrain memory。模板里的 `event_id` 由工具写入 frontmatter，用来识别同一次保存。

### 4. 给他看

告诉他文件路径，问要不要改。要改就改文件，仍不自动 push。

### 5. 写完之后交给 cognition propose

周记已经落盘，或一次反思已经明确收束之后，可以交给 `cognition` skill 做 propose（0–3 条，0 也合法）。**Journal 不写 `📖 Cognition/`。** 接受、改写、校验、落盘只走 cognition tools。

## 不要做

- 不要为了「补这周发生了什么」去扫 Journal 以外的私人目录。只跟旧周记已经出现的 wikilink 打开项目 / 卡片
- 不要同步 Notion
- 不要把 Claude/Codex/Hermes 那几份旧 skill 一并改掉
- 不要用已删除的公开仓 `jakeguo117/journal-skill`；只跟 information-flow
- 不要把普通聊天记成想法。不要改、不要删 `📝 Journal/想法/` 里已有的文件
- 不要把想法或消化清单当成周记条目。不要把想法分流进 Ideas / Experiments
