# Ideas

schema_version = ideas-0.1

依据是 Drive「02_数据规则与开发验收_V2.0_Draft」§2 Idea 行（file id `11gFwzKUxHsQ5_KSk3NFXcM_5vaB-QbJwrq5hk71XBIQ`）：核心表达、来源/上下文、主题、性质、确认状态、验证状态、适用场景/限制、关系、使用反馈与历史。同节通用字段一并落下。§3 的关系类型见下方「关系」。流程参考「01_工作流与功能需求_V2.0_Draft」§9 Ideas（file id `1hb1FPt00IoaXNGpUBQTeWgzerHQP5gfmXoJp6l74je0`）。两份都还是 Draft。本文件只定 ideas-0.1 的字段和写入约束。落盘工具是 T35，即 `skills/ideas/tools/write_idea.py`。

一条 Idea 一个节点。对象 ID 稳定，改标题或改表达都不改 ID。观点写在这里，`nature` 为 `judgment`，不另开 Viewpoints。确认这句表达，和这句是否得到验证，是两个字段。

## 字段

| 键 | 写入时 | Draft 对照 | 说明 |
|---|---|---|---|
| `schema_version` | 必填 | 通用 `schema_version` | 字面量 `"ideas-0.1"`。其他版本拒绝写 |
| `idea_id` | 第一次写入时按下方公式确定 | 通用 `id` | 身份只存这一键，不另存 `id`。格式 `^idea-[0-9a-f]{12}$` |
| `type` | 必填 | 通用 `type` | 字面量 `"idea"`。性质不写在这里 |
| `revision` | 必填 | 通用 `revision` | 整数，从 1 起。只有修订加 1 |
| `created_at` | 第一次写入时必填，之后不变 | 通用 `created_at` | `YYYY-MM-DDTHH:MM:SS+08:00`，时区 Asia/Hong_Kong |
| `updated_at` | 必填 | 通用 `updated_at` | 同上。每次追加 history 时改成该条的 `at` |
| `expression` | 必填 | 核心表达 | 离开原周记也能读懂的那句。strip 之后为空则拒绝。相对来源原话，不得新增步骤名或机制名，不得替换因果或目标。只动表面的改写见 `fidelity.md`。`suggested_expression` 不是本表的键 |
| `source_refs` | 必填，字符串列表，允许 `[]` | 来源/上下文；通用 `source_refs` | 每一项是整段引用：周记、input、fact、URL 加段落或时间戳。不拆成对象 |
| `context` | 可选 | 来源/上下文 | 引用之外的情境。省略表示没有额外情境 |
| `topics` | 必填，字符串列表，允许 `[]` | 主题 | 主题词。不按发布/自用分成互斥类 |
| `nature` | 必填 | 性质 | 只能是下表五个英文值。观点用 `judgment` |
| `confirmation_state` | 必填 | 确认状态 | 只能是确认状态表的四个英文值。省略时按 `candidate` 理解，不能因此变成 `confirmed` |
| `validation_state` | 必填 | 验证状态 | 只能是验证状态表的四个英文值。省略时写入 `untested`。确认了表达也不改这一字段 |
| `applicability` | 可选 | 适用场景/限制 | 适用场景。字符串 |
| `limitations` | 可选 | 适用场景/限制 | 限制。字符串。与 `applicability` 各写各的 |
| `relations` | 必填，列表，允许 `[]` | 关系 | 见「关系」。只有那七种 `type` |
| `usage_feedback` | 必填，列表，允许 `[]` | 使用反馈与历史 | 只追加。见「使用反馈与历史」 |
| `origin` | 必填 | 通用 `origin` | `jake`｜`ai_extension`。创建后不变 |
| `visibility` | 有默认值 | 通用 `visibility` | 省略时写 `"private-jake"`。只能是 `private-jake`｜`team`｜`public-ok` |
| `status` | 有默认值 | 通用 `status` | 省略时写 `"active"`。只能是 `active`｜`archived`。职责见下，不承接确认或验证 |
| `history` | 必填，列表 | 使用反馈与历史 | 同一 `idea_id` 的显式快照列表，只追加。最后一条等于当前字段 |

`visibility` 的 `public-ok` 就是要保留的 public_ok（与 facts-0.1 一样用连字符）。枚举里保留这三项，不改名，不删 `public-ok`。`public-ok` 只表示可见范围，不表示当前 `expression` 已确认，也不能单独把 `ai_extension` 交给 content。

## 确认状态

存英文。显示用中文。

| 存储 | 显示 | 谁可以把它写成当前值 |
|---|---|---|
| `candidate` | 候选 | Jake，或 `origin: ai_extension` 的延伸 |
| `confirmed` | 已确认 | 只有 Jake 确认记录 |
| `rejected` | 已舍弃 | 只有 Jake 的舍弃记录 |
| `deferred` | 暂存 | 只有 Jake 的暂存记录 |

Jake 确认记录是 `history` 里的一条，同时满足：`by` 为 `jake`，`confirmation_state` 为 `confirmed`，`expression` strip 之后等于节点当前 `expression` strip 之后。舍弃记录、暂存记录同样要求 `by` 为 `jake`，并且该条的 `confirmation_state` 与 `expression` 对得上当前值。对话里说过、没有写进 `history` 的句子不算记录。

### AC10

`origin` 为 `ai_extension`，且没有 Jake 确认记录时，`confirmation_state` 不得为 `confirmed`。`skills/ideas/tools/write_idea.py` 遇到这种写入会拒绝，退出码非 0，不创建文件，也不改已有文件。

同一条写入可以把 Jake 确认记录放进 `history` 再把当前状态写成 `confirmed`。`origin` 仍是 `ai_extension`，不改成 `jake`。AI 延伸在确认前的状态是 `candidate`。

`rejected` 与 `deferred` 同样要有对应的 Jake history 条目。延伸不能替他写成已舍弃或暂存。

### AC-Fidelity

未经他确认的 `expression`，若相对来源原话新增了步骤名或机制名，或因果、目标被替换，则不得写入。这一条否决的是模型改写。他亲自改过并确认的整句以那句为准。模型多出来的增量只允许出现在确认前候选里的 `suggested_expression`。`suggested_expression` 不是 ideas-0.1 的节点字段，不进 frontmatter，也不进 `history`。短清单 `public-ok` 不能单独把 `ai_extension` 的改写句写成 `confirmed`，也不能单独把它交给 content。

这一条在落盘前拦住。节点字段里没有来源原话，不能靠枚举代替这次自检。不合格的句子不得放进提交的 `expression`。选取、表面改写和自检见 `fidelity.md`。

## 验证状态

存英文。显示用中文。Draft 没有给 Idea 的验证枚举；ideas-0.1 用这四个值，只表示核验，不表示他是否认可这句表达。

| 存储 | 显示 |
|---|---|
| `untested` | 未验证 |
| `supported` | 得到支持 |
| `disputed` | 有争议 |
| `refuted` | 被否定 |

关系里出现 `supports` 或 `challenges`，不自动改 `validation_state`。要改验证状态，单独写入新快照。

## status

`status` 只回答这个节点还在不在日常检索里。

| 存储 | 含义 |
|---|---|
| `active` | 日常检索要看到 |
| `archived` | 先从日常检索拿开；文件和 history 都还在 |

确认状态只写 `confirmation_state`。验证只写 `validation_state`。被替代只在新节点的 `relations` 里写 `supersedes`。这三处不回写成 `status` 的别的词。`status` 不使用 `candidate`、`confirmed`、`rejected`、`deferred`、`untested`、`supported`、`disputed`、`refuted`、`superseded`。

## 性质

| 存储 | 显示 |
|---|---|
| `question` | 问题 |
| `hypothesis` | 假设 |
| `judgment` | 判断（观点归这里） |
| `method` | 方法 |
| `business_idea` | 商业设想 |

## ID

只在这个 `idea_id` 第一次写入时计算。之后改表达、改状态、修订，都沿用，不重算。文件名和标题变了也不变。

`idea-{sha1(首个 source_ref + '|' + 首次写入的 expression)[:12]}`

`source_refs` 为空时，首个 source_ref 按空字符串。sha1 按 UTF-8 字节、十六进制小写，取前 12 位。第一次写入如果自己带了 `idea_id`，必须和这个公式一致。`idea_id` 或 `expression` strip 之后为空，算缺字段，拒绝。

例：首个 source_ref 为 `journal:synthetic#p1`，首次 expression 为 `合成想法，离开原周记也能懂。`。拼接是 `journal:synthetic#p1|合成想法，离开原周记也能懂。`，`idea_id` 为 `idea-e7029224ac83`。

创建之后不变的还有：`type`、`schema_version`、`origin`、`created_at`。

## 关系

机器字段引用稳定 ID。正文里的 Obsidian wikilink 只方便阅读，不是第二份权威。关系写在发出方节点上，只存一个方向；反向由检索派生，不在对端再写一条。

| `type` | 显示 | 方向 |
|---|---|---|
| `sourced_from` | 来源于 | 本节点来源于 `target_id` |
| `supports` | 支持 | 本节点支持 `target_id` |
| `challenges` | 挑战 | 本节点挑战 `target_id` |
| `supplements` | 补充 | 本节点补充 `target_id` |
| `applies_to` | 应用于 | 本节点应用于 `target_id` |
| `uses` | 使用了 | 本节点使用了 `target_id` |
| `supersedes` | 替代 | 本节点替代 `target_id` |

每一项是：

| 键 | 写入时 | 说明 |
|---|---|---|
| `type` | 必填 | 上表七个值之一 |
| `target_id` | 必填 | 稳定 ID，strip 后非空。可以是别的 `idea_id`、`fact_id` 或其他稳定 ID，不写标题 |
| `note` | 可选 | 短说明 |

同一节点上，相同的 `type` + `target_id` 只保留一条。`supersedes` 的 `target_id` 不得等于本节点的 `idea_id`。

### 写入前的操作分类

Draft 01 §9 / 开工包 T35 的六种操作。本文件只写对应关系，工具见 `skills/ideas/tools/write_idea.py`。操作名不是第八种关系类型。

| 操作 | history `op` | 节点与关系 |
|---|---|---|
| 新建 | `create` | 新的 `idea_id`，`revision` 为 1。可以带 `sourced_from` 指回周记、反思或来源。没有来源则 `relations` 为 `[]` |
| 补充 | `supplement` | 给已有节点加场景、限制、来源或反馈时，沿用该 `idea_id`，`revision` 不变。补充来自另一个节点时，在补充方写 `supplements` |
| 支持 | `support` | 在指出支持的一方写 `supports`。`revision` 不变 |
| 挑战 | `challenge` | 在指出挑战的一方写 `challenges`。`revision` 不变 |
| 修订 | `revise` | 同一 `idea_id`，`revision` + 1，新快照写下修订后的 `expression`。这是版本，不是新的关系类型 |
| 替代 | `supersede` | 新的 `idea_id`，`revision` 为 1，该节点写 `supersedes` 指向旧 `idea_id`。旧文件保留，不在旧文件上写反向关系 |

一次改动只走修订或替代中的一种。修订只动原来的 `idea_id`。替代才用新 ID 加 `supersedes`。不要为了修订再发明关系类型，也不要让 `supersedes` 指向自己。

`history.op` 只能是 `create`｜`supplement`｜`support`｜`challenge`｜`revise`｜`supersede`。

## 使用反馈与历史

同一个 `idea_id` 只有一个节点。历史是这个节点上的 `history` 列表，只追加，不改旧条目，不删旧条目。用法与 facts 的「同一 ID 追加记录」相同，存放形式是列表，因为一个 Idea 是一个 Markdown 节点，不是 jsonl 多行。

`usage_feedback` 单独只追加，不塞进 history 快照：

| 键 | 写入时 | 说明 |
|---|---|---|
| `at` | 必填 | `YYYY-MM-DDTHH:MM:SS+08:00` |
| `note` | 必填 | strip 后非空 |
| `source_ref` | 可选 | 这次反馈指向的稳定引用 |

history 每一条是写入之后的快照，创建那一次也在里面。最后一条就是当前值。frontmatter 里的 `expression`、`source_refs`、`context`、`topics`、`nature`、`confirmation_state`、`validation_state`、`applicability`、`limitations`、`relations`、`origin`、`visibility`、`status`、`revision`、`idea_id`、`type`、`schema_version` 与最后一条一致，否则拒绝写。`usage_feedback` 不要求出现在快照里。

快照还要有 `at`、`by`（`jake`｜`ai_extension`）、`op`。每一条快照都写下这次写入之后仍然有效的全量字段。读取时不从更早的快照补空键。旧快照里的关系留在旧快照里。

## 存放

新节点进 DigitalBrain 已有的 `💡 Ideas/` 主题目录之一：`Content/`、`Insurance/`、`Life/`、`Tech/`、`Trading/`。同层已有 `MOC.md`、`README.md`。不新建第六个目录。不改、不删、不重命名旧笔记、`MOC.md`、`README.md`。旧的 `YYYY-MM-DD-[主题].md` 继续只读，新文件与它们并存。

文件名是 `{idea_id}.md`，例如 `idea-e7029224ac83.md`。frontmatter 里的 `idea_id` 与文件名主名相同。改表达不改文件名。

目录：调用方指定时，只能是上面五个目录名。未指定时，用 `topics` 的整项去对（strip，大小写不敏感）：`content`／`内容` → `Content`，`insurance`／`保险` → `Insurance`，`life`／`生活` → `Life`，`tech`／`技术` → `Tech`，`trading`／`交易` → `Trading`。正好对上一个目录就用它。对上零个或多于一个，用 `Life/`。

不手写这个文件，落盘走 `skills/ideas/tools/write_idea.py`（T35）。`scripts/sync_digitalbrain_skills.py` 的 allowlist 只有 `ideas/SKILL.md`，`references/` 和 `tools/` 没有同步到 DigitalBrain（那是 T38）。

## 检索

按 `topics`、`nature`、`confirmation_state`、`validation_state`、`applicability` 查。成熟度看确认和验证两个字段，不另设 maturity。可见范围看 `visibility`，不把它当成发布/自用分类。一个 Idea 可以被多个项目或多篇内容用 `uses` / `applies_to` 引用。

被别的节点 `supersedes` 指向的 `idea_id`，检索时当历史；不回写它的 `status`。图上有连线不等于关系已经验证。

## 写入时拒绝

由 `write_idea.py`（T35）执行，测试在 `skills/ideas/tools/test_ideas.py`。拒绝时退出码非 0，目标文件一个字节不动。AC-Fidelity 不在下面这份枚举里：来源原话不在节点上，组 payload 时就要拦住，见上文 AC-Fidelity。下面这些仍然拒绝：

- `schema_version` 不是 `ideas-0.1`，或 `type` 不是 `idea`
- `expression` 或 `idea_id` strip 后为空；第一次写入的 `idea_id` 与公式不一致；之后重算 `idea_id`
- 修改 `idea_id`、`type`、`schema_version`、`origin`、`created_at`
- `nature`、`confirmation_state`、`validation_state`、`origin`、`visibility`、`status`、关系 `type`、`history.op`、`history.by` 不在枚举内
- AC10：`origin` 为 `ai_extension`，当前是 `confirmed`，却没有 Jake 确认记录
- 当前是 `confirmed`、`rejected` 或 `deferred`，却没有对应的 Jake history 条目
- 改或删已有 `history` 条目，或已有 `usage_feedback` 条目
- frontmatter 与最后一条 history 不一致
- 关系不是七种之一，`target_id` 为空，重复的 `type` + `target_id`，或 `supersedes` 指向自己
- 写入路径会改动旧笔记、`MOC.md`、`README.md`，或落到上述五个目录以外
