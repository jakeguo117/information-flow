# 想法收集

随手记是 journal 的一个分支，不是新 skill。这里定文件布局、消化清单，以及写入之后怎么推到 DigitalBrain 的 `main`。合成例子里的句子是编的，不是私人笔记。

## 文件布局

每条想法是一个新文件。时间用 Asia/Shanghai，周目录用该时刻的 ISO 周（周一 00:00 到周日 23:59）。跨年以 ISO 周年为准，例如上海时间 2025-12-29 00:00 落在 `2026-W01/`。

```
📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm.md
📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm-2.md
📝 Journal/想法/digests/digest-{journal_event_id}.md
```

同一分钟里的下一条用 `-2`、`-3`，不覆盖第一条。id 就是文件名（不含 `.md`）。路径已经存在就拒绝，不改那个文件。

`原话:` 这一行之后到文件结尾是原话本身，字节与当时传入的文本一致，工具不去空格、不补换行。frontmatter 里的 `verbatim_sha256` 是这段 UTF-8 的 SHA-256。

```markdown
---
id: thought-20261008-1748
type: thought
tags:
  - thought
captured_at: 2026-10-08T17:48:00+08:00
week: 2026-W41
verbatim_sha256: <sha256 of the verbatim utf-8>
---
原话:
合成原话：先放着，一字不改。
```

`📝 Journal/` 顶层的周记列举不进入 `想法/`。`type: thought` 或 `type: thought-digest` 也不会被当成周记。

## 消化清单

不改旧想法，不打勾。一篇周记落盘成功之后，另写一个新文件，记下当时每一条未消化想法。没写成功的周记不产生清单。

未消化 = 全部想法文件的 id，减去任何一份清单里出现过的 id。不限本周。

每条只有两种结果：

- `展开`：写进了这篇周记
- `看过未展开`：看过，没有展开。之后 `list-open` 不再返回它

清单必须正好覆盖当时的未消化集合。漏一条、多一条、或重复，都不写文件。没有未消化想法时，不写空清单。

```markdown
---
type: thought-digest
tags:
  - thought-digest
journal_event_id: AIC-SYN-JOURNAL-0001
journal_stem: "2026-10-05 合成周记一"
consumed_count: 2
---

# 想法消化 AIC-SYN-JOURNAL-0001

- id: thought-20261006-0912
  disposition: 看过未展开
  journal: [[2026-10-05 合成周记一]]
- id: thought-20261008-1748
  disposition: 展开
  journal: [[2026-10-05 合成周记一]]
```

上面两句原话都是合成例子。

## 自动推送

决定：只新增文件的提交（想法文件、消化清单）可以直接推 main。任何修改或删除都不直推 main，不强推。周记正文不自动推。

`capture_thought.py publish` 只接受 `📝 Journal/想法/` 下面的一个想法文件或一份消化清单。它在 `main` 上取出 `origin/main`，然后只在下面两种情况继续：

- 工作区除了这一个未跟踪的新文件以外是干净的，并且 `HEAD` 等于 `origin/main`。它只暂存这一个路径。`git diff --cached --name-status` 必须只有这一条 `A`。然后 `git push origin HEAD:main`，不带 force。
- 或者工作区是干净的，本地正好多一个尚未推送的提交，且该提交只新增这一个路径。这时只推送，不再做第二个提交。

其他情况都拒绝，包括：路径已经在 `main` 上、暂存区里有修改（`M`）或删除（`D`）、工作区还有别的改动、当前分支不是 `main`、本地还有别的未推送提交。拒绝时不覆盖文件，也不删除已经写好的新文件，也不去动别人已经暂存的修改或删除。

周记刚写完时，周记文件本身就是工作区里的另一处改动，所以这时推消化清单会拒绝。不要为了推清单把周记一起提交。清单留在本地；等这一个清单路径变成工作区里唯一的改动，再单独 `publish`。

## 没存上

推送或 publish 只要失败，就要清楚告诉 Jake「没存上」，给一个短原因，并把他说的原话原样念回去，让他自己留着。失败包括：没有推送权限、网络、工作区不干净、工具拒绝、路径已经在 main 上、这次提交里有修改或删除。不要说已经存上，也不要说「记了」。磁盘上也许还留着刚写出的新文件，那不算存上。

`capture_thought.py` 只有在推送真正成功之后才打印成功状态，退出码 0。任何失败都退出非 0，并打印：

```json
{"status":"not_saved","reason":"...","verbatim":"..."}
```

退出码：2 是拒绝（工作区不干净、修改或删除、路径已在 main），3 是远端拒绝这次推送，4 是 git 或网络不可用。

## 两个环境能不能做这件事

### GPT Cloud Work

本仓库记录的决定是：周记的正式入口是 GPT Cloud Work（`docs/vnext-port/continue-project.md`，owner decision 2026-10-08）。这句没有写那个入口有没有 shell，也没有写它能不能跑 git。

OpenAI Help Center 文章 “Connecting GitHub to ChatGPT”（https://help.openai.com/en/articles/11145903 ，2026-10-08 的检索结果；直接打开该页返回 403，所以下面只采用检索摘录，不当作全文复核）：

- ChatGPT 的 GitHub app 按授权读取仓库内容。
- 同一篇写道：这个 GitHub app 只能读仓库；要生成、修改并推送代码，去用 Codex。
- 同一篇写道：符合条件的用户可以在 Work 里为已连接的 github.com 仓库做事件任务（PR 打开、review、评论、提交、合并）。这是监听，不是一篇写明的单文件提交接口。

UNKNOWN：

- Jake 用来写周记的那个 GPT Cloud Work 会话有没有 git 或 shell。
- 那个会话的连接器有没有「只创建文件」的写工具。社区帖描述 Work 里 `github_update_file` 可以成功，那不是 Help Center 的合同，这里不把它当成已核实能力。
- `obsidian-digitalbrain` 的 `main` 有没有分支保护，会不会拒绝直接推送。本次没有查询那个私有仓库。

所以在 Cloud Work 里不要假设 `publish` 跑得了。没有 git / shell 时，工具退出码 4，状态是 `not_saved`。告诉 Jake「没存上」，说明没有 git / shell，并把原话原样念回去。

退路：只有当会话里确实有 GitHub 写工具时，才发 contents API 的创建请求。官方文档是 `PUT /repos/{owner}/{repo}/contents/{path}`，同一端点既能创建也能替换；更新时必须带现有 blob 的 `sha`，文档里的创建示例不带 `sha`（https://docs.github.com/en/rest/repos/contents ，API version 2026-03-10）。`contents-body` 打出的 JSON 只有 `message`、`content`、`branch`，没有 `sha`。不要事后补上 `sha`。如果手头的工具必须带 `sha` 才能调用，就不要调用，那是更新。如果响应不是一次新建，就停，不要改用更新或删除。创建示例在文件已存在时的具体 HTTP 状态，文档没有写死，标 UNKNOWN。

git 和创建工具都没有时，告诉 Jake「没存上」，把原话原样念回去，留给有 git 的 Cursor 会话再 `publish`。不要把原话抄进周记文件来代替推送，也不要说已经存上。

### Cursor

Cursor 本地或云端 agent 有 shell 和 git 时，可以在 DigitalBrain 的检出里跑 `publish`。条件是：检出就是 vault 根、当前分支是 `main`、能 `fetch` / `push` `origin` 的 `main`，并且工作区满足上面的单文件规则。

UNKNOWN：某一次 Cursor 会话有没有推 `jakeguo117/obsidian-digitalbrain` `main` 的凭据，以及分支保护会不会拒绝这次推送。推送失败时退出码 3，状态是 `not_saved`，不删除新文件，不强推。告诉 Jake「没存上」，说明原因，并把原话原样念回去。有 token 时可以用上面的 contents 创建请求当退路；那个请求没成功也一样说「没存上」。这次实现没有调用那个 API，也没有推送真实 vault。
