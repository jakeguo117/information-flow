---
name: ideas
description: "提炼想法。Jake 说「提炼想法」，或周记/反思收束后要集中确认 Idea 候选时使用。读周记或反思，查已有 Idea，再建议新建、补充、支持、挑战、修订或替代。AI 延伸只标候选。确认前不落盘。不写 Journal、Facts、Cognition。"
---

# ideas

给 Jake 自己用。字段、枚举、AC10、AC-Fidelity 和七种关系见 `references/schema.md`。选取与改写的细则见 `references/fidelity.md`。`schema_version` 字面量是 `ideas-0.1`。时区 Asia/Hong_Kong。

规则源在 information-flow。本包不改 DigitalBrain 里已有的 Ideas 笔记。落盘将走 `skills/ideas/tools/write_idea.py`（T35），现在只定义字段与流程。

## 什么时候用

- 他说「提炼想法」
- 路由把这一步交给 ideas
- 周记已经落盘，或一次反思已经收束，在讨论末尾集中给候选

普通聊天不提炼。「记一下：」「想法：」仍是 journal 的随手记，不进这里。

## 流程

### 1. 读周记或反思

读刚写完的那篇周记，或这次已经收束的反思。用他的原话理解核心表达。能整句用他的原话，就整句用，标 `origin` 为 `jake`，少动。旧周记里的状态不当作当前事实。不改周记，不写 `📝 Journal/`。

每条候选离开原文也要能看懂：表达、适用场景、限制写全。不为了凑数硬拆，也不为了更像一篇文章而换因果。

### 2. 查已有 Idea

只读 `💡 Ideas/`。已有子目录是 `Content/`、`Insurance/`、`Life/`、`Tech/`、`Trading/`，同层有 `MOC.md`、`README.md`。旧的 `YYYY-MM-DD-[主题].md` 照样读。

先查重，再建议下面六种操作之一：新建、补充、支持、挑战、修订、替代。操作怎么对应七种关系，以 schema 为准。修订用同一 `idea_id` 的 `revision` 加一；替代用新节点的 `supersedes`。不发明第八种关系。

### 3. 讨论末尾集中确认

候选放在这一轮讨论的末尾，一次给完。每条写清：

- 操作：新建 / 补充 / 支持 / 挑战 / 修订 / 替代
- `nature`：`question`｜`hypothesis`｜`judgment`｜`method`｜`business_idea`
- `origin`：`jake`｜`ai_extension`
- 建议的 `confirmation_state`

他亲口说完整的一句，`origin` 为 `jake`。模型补出来的问题、假设、归纳、改写，`origin` 为 `ai_extension`。怎么选、怎么改、什么时候能交给 content，按下一小节，不另用一套标准。

#### 选取与改写保真

准确传递这句 Idea 要说的意思。好听、好排、好写成几步机制，都排在保真后面。下面是浓缩。对照表、自检五题和反面例子见 `references/fidelity.md`。

选取优先原话。周记、聊天或确认记录里，他已经说完整的一句，`origin` 为 `jake`，`expression` 用这句原话，不要先改写再拿去确认。模型从多句归纳、补问或改写出来的，`origin` 为 `ai_extension`，`confirmation_state` 只能是 `candidate`。不把延伸说成他的观点，也不预填 `confirmed`。短清单已经标可公开，但还没有确认这句 `expression` 时，只可当作来源线索，不是 content 能用的 `expression`。

改写只动表面。允许语序微调、把中英夹杂改成通顺中文、去掉口头赘词，以及不引入新步骤名或机制名的同义替换。离开周记之后仍要可读。禁止换因果（因为 A 所以做 B，不能改成因为 C 所以做 D）。禁止换目标。禁止添加原话没有的步骤名或机制名。禁止用外部框架反填进 `expression`。把「存下来、积起来／滚复利」收成「捕获—回看—改写／叠厚」，就是不合格改写。（「坚持迭代」半句已按 Jake 19:22 默认从锁定 expression 去掉；示例勿再写成「存下来 → 坚持迭代 → 滚复利」。）改完之后，因果箭头还要用原话里的词画得出来。画不出，就退回原话，或只做更小的表面改动。

交候选前先做保真自检。原话里的原因、手段、结果，改写句里还必须在，方向相同。目标词保留，或只做同义，不换成新口号。`expression` 里不得出现原话没有的步骤名或机制名。多出来的解释、例子、机制拿掉，或只放进 `suggested_expression`，不得进 `expression`。`suggested_expression` 不是 ideas-0.1 的节点字段，不写入 Idea 文件。表面改写不要和 Journal 或短清单原话连续 20 个字相同；`origin` 为 `jake` 且用的就是原话时除外。任一题不过，不得把该句标成可交给 content 的 `expression`。

短清单「可公开」不等于这句已经确认。`public-ok` 只表示可以作为公开素材来源，只解决 `visibility`。交给 content 的 `expression` 必须是他保留的原话，或他改过并确认的整句，并且有确认记录：`history` 里 `by` 为 `jake`，表达与当前 `expression` 一致。未再确认的改写句保持 `candidate`。节点测试和演示不得用短清单已批跳过这次确认。

他逐条选择：保留、改写、暂存、舍弃。这里的改写只指他改过的整句，不是模型先改好的句子。

- 保留：认可当前这句，确认为 `confirmed`。当前这句必须已经过保真自检
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

### AC-Fidelity

未经他确认的 `expression`，相对来源原话若新增了步骤名或机制名，或因果、目标被替换，不得写入。这一条否决的是模型改写。他亲自改过并确认的整句以那句为准。模型多出来的步骤名、机制名、解释和例子，只允许出现在 `suggested_expression`。`suggested_expression` 只出现在确认前的候选里，不是节点字段。短清单 `public-ok` 不能单独把 `ai_extension` 的改写句升为可交 content。来源原话不在节点字段里，这一条在落盘前拦住，不靠枚举代替。细则见 `references/fidelity.md`。

`visibility` 省略时为 `private-jake`。取值保留 `private-jake`｜`team`｜`public-ok`（public_ok）。`public-ok` 只表示可见范围，不表示这句 `expression` 已确认。

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
