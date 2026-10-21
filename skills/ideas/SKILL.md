---
name: ideas
description: "提炼想法。Jake 说「提炼想法」，或周记/反思收束后要集中确认 Idea 候选时使用。读周记或反思，查已有 Idea，再建议新建、补充、支持、挑战、修订或替代。AI 延伸只标候选。确认前不落盘。不写 Journal、Facts、Cognition。"
---

# ideas

给 Jake 自己用。字段、枚举、AC10 和七种关系见 `references/schema.md`。`schema_version` 字面量是 `ideas-0.1`。时区 Asia/Hong_Kong。

规则源在 information-flow。本包不改 DigitalBrain 里已有的 Ideas 笔记。落盘将走 `skills/ideas/tools/write_idea.py`（T35），现在只定义字段与流程。

## 什么时候用

- 他说「提炼想法」
- 路由把这一步交给 ideas
- 周记已经落盘，或一次反思已经收束，在讨论末尾集中给候选

普通聊天不提炼。「记一下：」「想法：」仍是 journal 的随手记，不进这里。

## 流程

### 1. 读周记或反思

读刚写完的那篇周记，或这次已经收束的反思。用他的原话理解核心表达。旧周记里的状态不当作当前事实。不改周记，不写 `📝 Journal/`。

每条候选离开原文也要能看懂：表达、适用场景、限制写全。不为了凑数硬拆。

### 2. 查已有 Idea

只读 `💡 Ideas/`。已有子目录是 `Content/`、`Insurance/`、`Life/`、`Tech/`、`Trading/`，同层有 `MOC.md`、`README.md`。旧的 `YYYY-MM-DD-[主题].md` 照样读。

先查重，再建议下面六种操作之一：新建、补充、支持、挑战、修订、替代。操作怎么对应七种关系，以 schema 为准。修订用同一 `idea_id` 的 `revision` 加一；替代用新节点的 `supersedes`。不发明第八种关系。

### 3. 讨论末尾集中确认

候选放在这一轮讨论的末尾，一次给完。每条写清：

- 操作：新建 / 补充 / 支持 / 挑战 / 修订 / 替代
- `nature`：`question`｜`hypothesis`｜`judgment`｜`method`｜`business_idea`
- `origin`：`jake`｜`ai_extension`
- 建议的 `confirmation_state`

他的原话，或他已经说完整的那句，`origin` 为 `jake`。模型补出来的问题、假设、归纳、改写，`origin` 为 `ai_extension`。

AI 延伸单列，`confirmation_state` 为 `candidate`。不把它们说成 Jake 的观点，也不预填 `confirmed`。

他逐条选择：保留、改写、暂存、舍弃。

- 保留：认可当前这句，确认为 `confirmed`
- 改写：以他改过的整句为当前 `expression`，再确认
- 暂存：`deferred`
- 舍弃：`rejected`

已经明确确认过的完整表达，不要机械重问。把那次原话记成 Jake 确认记录即可。

观点归入 Idea，`nature` 为 `judgment`。不新开 Viewpoints，不写到 Cognition。

### 4. 确认前不落盘

他选定之前不写文件。选定之后也不要手写 Markdown 绕过工具。

```bash
python3 skills/ideas/tools/write_idea.py
```

这个工具是 T35，本包没有，也没有命令行参数可调用。工具还没落地时，停在已确认的字段草稿上，告诉他这次没有写入。

### AC10

`origin` 为 `ai_extension`，且没有 Jake 确认记录时，`confirmation_state` 不得为 `confirmed`。将来 `write_idea.py` 应拒绝这种写入。记录的形状以 schema 为准：写在该 `idea_id` 的 `history` 里，`by` 为 `jake`，表达与当前 `expression` 一致。只在聊天里说过、没有进入记录的，不算已确认。

`visibility` 省略时为 `private-jake`。取值保留 `private-jake`｜`team`｜`public-ok`（public_ok）。

## 新节点放哪

只放到已有的五个主题目录之一。按 `topics` 选；调用方可以指定目录；不确定就用 `Life/`。文件名带稳定 `idea_id`（`idea-xxxxxxxxxxxx.md`），ID 不随标题变。

禁止改、删、重命名旧笔记、`MOC.md`、`README.md`。不新建主题目录。新格式文件与旧文件名并存。

## 不要做

- 不写 `📖 Cognition/`、Facts、`📝 Journal/`
- 不改 facts、cognition、journal、digest、intake 的技能和工具
- 不改 `scripts/sync_digitalbrain_skills.py`（allowlist 是 T38）
- 不改 workflow、路由、定时任务
- 不把确认状态写进 `validation_state` 或 `status`。认可这句表达用 `confirmation_state`；有没有得到验证用 `validation_state`；节点是否留在日常检索用 `status`
- 确认前不落盘。本包不手写 `💡 Ideas/`
