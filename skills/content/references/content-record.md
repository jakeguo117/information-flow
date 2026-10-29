# Content

schema_version = content-0.1

依据是 Drive「02_数据规则与开发验收_V2.0_Draft」里 Content 那一句（file id `11gFwzKUxHsQ5_KSk3NFXcM_5vaB-QbJwrq5hk71XBIQ`）：主题、brief、用到的 Idea 和 Fact、稿件版本、Jake 批准的版本、渠道、发布结果、复盘。同文件的通用字段一并落下。流程是「03_表达挖掘与内容运营_V2.0_Draft」§3 的六步（file id `1kfrSUQu5u1eR2avFDZ9qJeI4xaPuai5xsrwiqTRPfKs`）。两份都还是 Draft。本文件只定 content-0.1 的字段、发布包和批准怎么绑版本。

一条内容一个节点。对象 ID 稳定，改标题或改表达都不改 ID。一篇内容可以引用多条 Idea 和 Fact。本包不写这个文件，也不校验。形状写在这里，避免下一包另起字段名。

例子都是合成句，不是他的笔记。

## 字段

| 键 | 写入时 | 说明 |
|---|---|---|
| `schema_version` | 必填 | 字面量 `"content-0.1"` |
| `content_id` | 第一次记下时按下方公式确定 | 身份只存这一键。格式 `^content-[0-9a-f]{12}$` |
| `type` | 必填 | 字面量 `"content"` |
| `revision` | 必填 | 整数，从 1 起。核心表达、brief、任一渠道正文，或卡片图、封面图、X 配图、正文里的图片有实质改动就加 1 |
| `created_at` | 第一次记下时必填，之后不变 | `YYYY-MM-DDTHH:MM:SS+08:00`，时区 Asia/Hong_Kong |
| `updated_at` | 必填 | 同上。每次 revision 加 1 时改成当时 |
| `origin` | 必填 | `jake`｜`ai_extension`。题目是他先提出的，用 `jake`。AI 提的候选即使用他的原话，也保持 `ai_extension` |
| `visibility` | 有默认值 | 省略时是 `private-jake`。只能是 `private-jake`｜`team`｜`public-ok` |
| `status` | 有默认值 | 省略时是 `active`。只能是 `active`｜`archived`。不承接阶段、批准或是否发出 |
| `stage` | 必填 | 见「阶段」。不写进 `status` |
| `topics` | 必填，字符串列表，允许 `[]` | 主题词 |
| `audience_problem` | 候选起必填 | 受众问题。strip 之后为空则这步没有完成 |
| `angle` | 候选起必填 | 角度 |
| `material_gaps` | 必填，字符串列表，允许 `[]` | 还缺什么材料。空列表表示他这边没有缺口 |
| `suggested_expression` | 可选 | AI 建议的那句。不能当成他的观点 |
| `expression` | 选题确定后必填 | 他的核心表达。只能是他的原话，或他改过并确认的整句 |
| `expression_by` | `expression` 非空时必填 | 只能是 `jake`。没有这键，`expression` 不算已确认 |
| `source_refs` | 必填，字符串列表 | 见「来源」。候选至少一项 |
| `experience_quotes` | 必填，字符串列表，允许 `[]` | 改写后的经历叙述，来自 Idea 或讨论确认，不是 Journal 连续原句。讲观念至少一项 |
| `form` | 选题确定后必填 | `news_comment`｜`concept_story` |
| `brief` | 策划起必填 | 结构、引用、案例、题型、排期。一段文字 |
| `channels` | 草稿起必填 | 见「渠道」。整周包或三版交齐时三版都要有。只要 X 时只要求 `x` 正文 |
| `body_sha256` | 草稿起必填 | 见「正文指纹」。小写十六进制，64 位 |
| `sensitivity` | 必填，字符串列表，允许 `[]` | 见「三层过滤」 |
| `layer2` | 必填 | `pending`｜`allowed`｜`refused` |
| `layer3` | 必填 | `unchecked`｜`passed`｜`failed` |
| `layer3_revision` | `layer3` 为 `passed` 或 `failed` 时必填 | 这次把关对应的 `revision`。与当前 revision 不一致则视为 `unchecked` |
| `approval` | 他批了这一版才有 | 见「批准」。没有批过就省略 |
| `publish_result` | 必填 | 见「发布结果」 |
| `review` | 复盘时才有 | `at`、`notes`。他补充的线下反馈写在 `notes` |
| `x_trend_note` | 可选 | 只有参考价值的那句 X 热门。省略表示没有用热门。不能充当 `source_refs` 或 `expression` |
| `history` | 必填，列表 | 只追加。每一条至少有 `revision`、`stage`、`expression`、`visibility`、`body_sha256` |

`visibility` 的 `public-ok` 与 ideas-0.1、facts-0.1 一样用连字符。不另造第四个值。

## 阶段

存英文。显示用中文。`status` 仍然只回答这个节点还在不在日常检索里。

| 存储 | 显示 | 进入这一步要有的东西 |
|---|---|---|
| `candidate` | 候选 | 受众问题、角度、至少一条来源 |
| `selected` | 已选题 | `expression_by` 为 `jake`，并且 `form` 已定 |
| `brief` | 已策划 | `brief` strip 之后非空 |
| `draft` | 草稿 | 本轮要交的渠道已写上。整周包或三版交齐时三版都已写上。只要 X 时 X 正文已写上。`body_sha256` 是这一版的 |
| `approved` | 已批准 | `approval` 对得上当前 revision 和 `body_sha256` |
| `published` | 他已确认发出 | `publish_result.state` 为 `published`，且 `by` 为 `jake` |
| `reviewed` | 已复盘 | `review.notes` strip 之后非空 |
| `rejected` | 不要 | 他回了「不要」。`approval` 必须拿掉 |

## 来源

`source_refs` 每一项是整段字符串，不拆成对象。

| 开头 | 含义 |
|---|---|
| `idea:` | 后面是 `idea-` 加 12 位十六进制 |
| `fact:` | 后面是 `fact-` 加 12 位十六进制 |
| `journal:` | 周记文件名，必要时加 `#` 和段落位置。只作出处指针，正文不得粘贴该段原话 |
| `experience:jake` | 经历在 `experience_quotes` 里，不在别的节点上 |

评新闻至少有一项 `fact:` 或一条带日期的链接。链接写成 `URL | YYYY-MM-DD | 用来做什么`。竖线两侧各一个空格。日期是事实的日期，不是写稿当天。

## ID

只在这个 `content_id` 第一次记下时计算。之后改表达、改渠道、改阶段，都沿用，不重算。

`content-{sha1(首个 source_ref + '|' + 首次记下的 audience_problem)[:12]}`

sha1 按 UTF-8 字节、十六进制小写，取前 12 位。`source_refs` 为空时，首个 source_ref 按空字符串。这和「候选至少一项来源」冲突，所以空来源的候选先不要分配 ID。

例：首个 source_ref 为 `idea:idea-e7029224ac83`，首次 audience_problem 为 `合成受众问题，离开原笔记也能懂。`。拼接是 `idea:idea-e7029224ac83|合成受众问题，离开原笔记也能懂。`，`content_id` 为 `content-1729bdab9586`。

创建之后不变的还有：`type`、`schema_version`、`origin`、`created_at`。

## 渠道

`channels` 是一个对象。整周多渠道发布包或明确三版交齐时，三个键都要在，三个正文 strip 之后都非空。

任务只要写 X、X Article、X 长文或 X 短帖：草稿只要求 `channels.x.body` 非空。小红书和公众号字段按正文指纹留空字符串，不删键。不要为了填这两栏去 Skill load `content-xhs` 或 `content-wechat`。

| 键 | 里面有什么 |
|---|---|
| `x` | `body`：中文长文，约 3000 字（口径见 content-x） |
| `xiaohongshu` | `caption`：一句短文案。`cards`：字符串列表，按页序，每项含页码 n/N |
| `wechat_mp` | `title`、`summary`、`cover_note`、`body`、`sources_note`。`body` 用小标题分段，图片说明写在正文对应的位置 |

公众号 `body` 和 X 的 `body` 说同一件事。公众号可以重排，不能新加他没说过的判断或经历。

## 正文指纹

`body_sha256` 是下面这个 JSON 对象的 UTF-8 sha256，小写十六进制。`json` 使用 `sort_keys`，分隔符是逗号和冒号，不把中文转成 `\u` 转义。`revision` 是 JSON 数字。十一个键都要在；没有内容的字符串写成 `""`，不删键。

键：`schema_version`、`content_id`、`revision`、`x_body`、`xhs_caption`、`xhs_cards`、`wechat_title`、`wechat_summary`、`wechat_cover_note`、`wechat_body`、`wechat_sources`。只要 X 时，小红书和公众号这些字符串写成 `""`，十一个键仍都在。

`xhs_cards` 是 `channels.xiaohongshu.cards` 用 `\n` 按页序接成的一个字符串。没有卡片时是 `""`。

合成例子的对象串成一行后，sha256 为 `fdb72bfb9f4bd951a2680766aa646d7c1b30c18cec519efda4347804171d996c`：

```json
{"content_id":"content-1729bdab9586","revision":1,"schema_version":"content-0.1","wechat_body":"合成公众号正文。","wechat_cover_note":"封面：合成说明，无真人。","wechat_sources":"出处：https://example.com/synthetic 2026-10-20","wechat_summary":"合成摘要","wechat_title":"合成标题","x_body":"合成 X 正文。","xhs_caption":"合成短文案。","xhs_cards":"1/1 合成卡片。"}
```

渠道正文一改，指纹就变。指纹对不上 `approval.body_sha256`，这张批就不覆盖当前稿。

## 三层过滤

`sensitivity` 的取值只有：`family`、`money_positions`、`health`、`client`、`named_person`。对应家人、钱和持仓、健康、工作客户、具体人名。列表非空时，`visibility` 只能是 `private-jake`，`layer2` 不能是 `allowed`。

| 键 | 存储 | 显示 | 规则 |
|---|---|---|---|
| `layer2` | `pending` | 未回复 | 不公开。不能写公开稿 |
| `layer2` | `allowed` | 可以 | 只有他在短清单里点过这条 |
| `layer2` | `refused` | 不要 | 他点了不要。不能写公开稿 |
| `layer3` | `unchecked` | 未查 | 不能交卡 |
| `layer3` | `passed` | 通过 | `layer3_revision` 等于当前 revision，自检也全部通过 |
| `layer3` | `failed` | 不过 | 不能交卡 |

`public-ok` 只在 `sensitivity` 为空、`layer2` 为 `allowed`、并且他确认过核心表达时使用。三者缺一个，就保持 `private-jake`。`team` 只表示队友可见，不是公开稿，也不是发帖许可。

## 批准

`approval` 是一个对象：

| 键 | 说明 |
|---|---|
| `by` | 只能是 `jake` |
| `phrase` | 只能是 `批` |
| `revision` | 他批的那一版。必须等于当前 `revision`，这张批才有效 |
| `body_sha256` | 必须等于按当前渠道重算的指纹 |
| `channels` | `x`、`xiaohongshu`、`wechat_mp` 的子集。他只说「批」时，三项都写上。他点了渠道，就只写点名的那些 |
| `at` | `YYYY-MM-DDTHH:MM:SS+08:00` |

「改」不写入 `approval`。改完是新的 revision，旧对象作废，整段省略，直到他再批。「不要」同样拿掉 `approval`，`stage` 改为 `rejected`。

这张批不是发帖动作。渠道登录、接口和代发都不在批准里面。

## 发布结果

| 键 | 说明 |
|---|---|
| `state` | `unconfirmed`｜`published`。默认 `unconfirmed` |
| `by` | 只有 `published` 时才填，而且只能是 `jake` |
| `notes` | 他怎么确认的。一句原话即可 |
| `channels` | 列表。每一项是 `channel`、`url`、`published_at`。链接可以空，时间有他就记 |

他没有亲口确认发过，`state` 保持 `unconfirmed`，即使 `approval` 已经对得上。不把未确认写成已发布。

## 发布包

一条内容只有这一份发布包，审批卡按渠道交，一个渠道一张。整周多渠道包或明确三版交齐时，X、公众号、小红书各一张卡，每张附发布包里本渠道那一段，三张一次交齐。只要写 X、X Article、X 长文或 X 短帖时，只交 X 一张卡，不为凑三版去加载 content-xhs 或 content-wechat。周日 20:00 前交出时自检已经全部通过。周一 10:00 把这几张交统一出口（PM·总协调）转他，等「批 / 改 / 不要」。

不落盘是指不把发布包写到这台机器的本地磁盘，也不在本机新建内容目录。发布包的正式副本在 Google Drive「内容/草稿/{周}/」。对话里交的是同一份。X 文案（X 长文定稿）由 X 运营交。小红书文案由内容写手从这版 X 定稿展开后交，不另起底稿。公众号由公众号编辑按 X 定稿转换后交，不另写新稿。三渠道配图由内容视觉按渠道裁后交实际的卡片图和封面图，不只写配图说明。渠道字段里的文案、封面说明和正文里的图片说明仍是文字，图片字节不写进 `body_sha256`，所以换图也要把 revision 加一，旧的 `approval` 随之不再覆盖。动画链接可选，空着合法。动画字节不进 `body_sha256`，只记链接。

```markdown
# 发布包 {content_id} r{revision}

经统一出口转 Jake 本人。

- content_id：
- revision：
- body_sha256：
- 受众问题：
- 角度：
- 缺的材料：
- 核心表达：
- 题型：评新闻｜讲观念
- 来源：
- visibility：
- 敏感：无，或五类的中文名
- 第二层：未回复｜可以｜不要
- 第三层：未查｜通过｜不过
- X 热门参考：无，或只写参考句
- 动画链接：（可选，空着合法）

## 自检

按 skills/content-core/SKILL.md 的自检清单，每项写过或不过。旧 skills/content/SKILL.md 已停用。

## X

{x.body}

## 小红书

短文案：{caption}

卡片：
- {n/N} {这一页的文案}

卡片图：实际的卡片图。图源按 content-core：优先 Grok Bot 按论点生成的定制图；自家数据图或表可以，并写出处。未授权网图不得当作新闻现场照。生成图若像实拍新闻，文内标明「配图/示意」。讲观念可以用生成图，图里没有真人。不只写配图说明。

## 公众号

标题：
摘要：
封面图：实际的封面图
封面说明：
正文：
出处：

## 这一版的批准

只覆盖上面的 content_id、revision、body_sha256，以及这次列出的渠道。
回复「批」「改」或「不要」。
```

自检有一项不过，就不交这张卡。卡上的 `body_sha256` 用「正文指纹」重算，不手填一个对不上的值。

## 从一条内容能查回什么

`source_refs` 里的 `idea:`、`fact:`、`journal:` 和 `experience_quotes` 就是这条用过的材料。发布只认 `approval` 对得上的那一版。复盘不改 Idea 的确认状态，也不改 Belief 的验证状态。
