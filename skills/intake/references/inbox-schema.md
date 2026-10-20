# Inbox 字段规范

schema_version = inbox-0.1

来自开工包 §3（10-17 23:57 版）。字段的名字、必填、含义、取值规则照该节转录，不增不减。§3 没有单列类型。类型列只复述说明里已经写明的形态；没有写明的标「未规定」。

## 存放与时间

不改各插件写出来的 Inbox 笔记（Snipd 和 WeRead 插件会覆盖它们）。另建机器索引，放在 DigitalBrain：`📥 Inbox/_index/sources.jsonl`、`📥 Inbox/_index/inputs.jsonl`，一行一条，只追加。状态变化另写一行 `state` 事件，读取时取最新那行。§3 没有给 `state` 事件的字段表，本文不补字段、不给样例。私人内容不进 information-flow 仓（AC14）。

时区：显示和分周统一用 Asia/Hong_Kong。存储一律用带时区偏移的 ISO 8601。

## Source

来源。一篇、一个视频或一本书一条。

| 字段 | 类型 | 必填 | 含义 | 取值规则 |
|---|---|---|---|---|
| `schema_version` | 字面量字符串 | 是 | 本规范版本 | `"inbox-0.1"` |
| `source_id` | 字符串 | 是 | 来源的稳定 ID | `src-{platform}-{external_content_id}`。没有平台 ID 时用 `src-{platform}-u{sha1(canonical_url)[:12]}`。改文件名、改标题都不变 |
| `platform` | 枚举字符串 | 是 | 来源平台 | `youtube`｜`snipd`｜`weread`｜`x`｜`instagram`｜`thought`｜`manual` |
| `external_content_id` | 未规定 | 有就填 | 平台上的内容 ID | YouTube `video_id`；Snipd episode uuid；WeRead `bookId`；X status id；Instagram shortcode |
| `canonical_url` | 字符串 | 是 | 规范化后的地址 | 去掉 utm 一类追踪参数，保留决定内容身份的参数（如 YouTube 的 `v`） |
| `title` | 未规定 | 尽量 | — | §3 说明为「—」 |
| `author` | 未规定 | 尽量 | — | §3 把 `title`、`author` 写在同一行，说明为「—」 |
| `published_at` | 带偏移的 ISO 8601 | 尽量 | 原内容的发布时间 | 存储用带时区偏移的 ISO 8601 |
| `raw_refs` | 字符串列表 | 是 | Inbox 笔记路径 | Inbox 笔记路径的列表 |
| `content_revision` | 整数 | 是 | 内容修订次数 | 从 1 开始。内容本身修订时 +1，不算新收藏 |
| `first_seen_at` | 带偏移的 ISO 8601 | 是 | 索引第一次看到的时间 | 存储用带时区偏移的 ISO 8601 |

## Input

输入记录。一次收藏、划线、snip 或随手记一条。

`input_id` 公式：`in-{platform}-{sha1(source_id + '|' + event_key)[:12]}`

| 字段 | 类型 | 必填 | 含义 | 取值规则 |
|---|---|---|---|---|
| `schema_version` | 字面量字符串 | 是 | 本规范版本 | `"inbox-0.1"` |
| `input_id` | 字符串 | 是 | 输入记录的稳定 ID | `in-{platform}-{sha1 前 12 位}`。拼接式见上。`event_key` 是平台给的事件 ID，没有就用指纹 |
| `source_id` | 字符串 | 是 | 指向 Source | 指向 3.1 的 `source_id` |
| `external_item_id` | 未规定 | 有就填 | 平台上的事件 ID | YouTube `video_id@like_at`；Snipd snip uuid；WeRead 划线块 ID（`^bookId-章-起-止`）；X / Instagram 同 `external_content_id`；想法用 thought id |
| `event_type` | 枚举字符串 | 是 | 这一条是哪种动作 | `like`｜`save`｜`bookmark`｜`highlight`｜`snip`｜`note`｜`thought` |
| `captured_at` | 可空；有值时为带偏移的 ISO 8601 | 可空 | Jake 收藏或记录的时间 | 存储用带时区偏移的 ISO 8601 |
| `time_basis` | 枚举字符串 | 是 | `captured_at` 的时间依据 | `platform`（平台给的时间）、`first_seen`（用首次捕获时间代替，并标出来）或 `unknown`（历史导入，不知道时间） |
| `received_at` | 带偏移的 ISO 8601 | 是 | 系统接收时间 | git 第一次加进这个文件的提交时间，或索引首次看到的时间 |
| `source_published_at` | 可空；有值时为带偏移的 ISO 8601 | 可空 | 冗余的原内容发布时间 | 冗余存一份，方便汇总显示 |
| `source_week` | 可空；有值时为 ISO 周 | 可空 | 收藏或记录所在的周 | 按 `captured_at` 在香港时区算的 ISO 周。`time_basis=unknown` 时为空，不算本周新增（AC05）。周次字符串的写法 §3 未规定 |
| `origin` | 枚举字符串 | 是 | 这条记录怎么进来的 | `collected` 或 `historical_import` |
| `content_fingerprint` | sha256 | 是 | 摘录或原话的指纹 | 规范化摘录或原话的 sha256。规范化步骤 §3 未规定 |
| `completeness` | 枚举字符串 | 是 | 这条记录齐不齐 | `full`｜`excerpt`｜`metadata_only`｜`missing` |
| `missing_reason` | 未规定 | 不是 full 时必填 | 为什么不齐 | 例如 `transcript: none` |
| `process_state` | 枚举字符串 | 是 | 处理状态 | `pending`｜`processing`｜`completed`｜`failed`｜`retry_pending` |
| `last_error` | 未规定 | failed 时必填 | 最近一次错误 | — |
| `last_cycle_id` | 未规定 | 可空 | 最近一次被选中的批次 | 最近一次被哪个批次选中 |
| `topics` | 未规定 | Process 之后填 | 主题 | 见「由周四 AI 整理写回」 |
| `summary_ref` | 未规定 | Process 之后填 | 摘要所在位置 | 见「由周四 AI 整理写回」 |
| `process_version` | 未规定 | Process 之后填 | 处理规则的版本 | 见「由周四 AI 整理写回」 |
| `inbox_ref` | 字符串 | 是 | 笔记位置 | 笔记路径加锚点。路径和锚点怎么连，§3 未规定 |

### 去重

照 §3：先找来源（平台 ID → 规范化 URL）；再找输入（`external_item_id` → 指纹）。同一事件重复同步：返回已有的 `input_id`，不新增（AC01）。同一来源有新划线或新备注：新建 Input，复用 Source（AC02）。只是看起来像：记 `suspected_duplicate_of`，不删除。

`suspected_duplicate_of` 只出现在这句去重说明里，不在字段表中，本文不把它加进字段表。去重句里的「指纹」、`content_fingerprint`、以及没有 `event_key` 时用的「指纹」，§3 没有写是不是同一个值。

WeRead：每条划线单独成为一条 Input。同一本书再来一条划线，是新的 `external_item_id` / `event_key`，因此是新的 `input_id`，`source_id` 不变。

X 和 Instagram 没有收藏时间时：`time_basis` 写 `first_seen`，`captured_at` 用首次捕获时间。

## 由周四 AI 整理写回

`topics`、`summary_ref`、`process_version` 由周四 Process 的 AI 步骤写回。收集阶段不填。

本期不做摘要（J10）。收集阶段这三个字段留空。

最终写法照 §3.2：

| 字段 | 最终写法 |
|---|---|
| `topics` | 主题，可以多个，由 Process 的 AI 步骤写 |
| `summary_ref` | 指向来源卡的段落 |
| `process_version` | 处理规则的版本 |

多个主题怎么编码、段落指针怎么写、版本号怎么编号，§3 都没有写。本文不补。

## Batch

批次清单。路径：`📋 Digests/cycles/{cycle_id}/batch.json`。

§3.3 用散文列出字段，没有类型表，也没有逐项必填。下表不补类型和必填。

| 字段 | 类型 | 必填 | 含义 | 取值规则 |
|---|---|---|---|---|
| `cycle_id` | 未规定 | 未规定 | 批次 ID | `cy-YYYYMMDD`（周四的日期） |
| `cutoff_at` | 带偏移的 ISO 8601 | 未规定 | 本批截止时间 | 存储用带时区偏移的 ISO 8601。钟点 §3 未规定 |
| `coverage_start` | 带偏移的 ISO 8601 | 未规定 | 本批覆盖的起点 | 上一批的 `cutoff_at` |
| `selected_input_ids` | 字符串列表 | 未规定 | 本批选中的输入 | `received_at` ≤ `cutoff_at`，且状态是 `pending`、`retry_pending` 或 `failed` 的全部记录，跨周扫描 |
| `late_input_ids` | 字符串列表 | 未规定 | 赶不上本批的输入 | cutoff 之后才到的，留给下一批 |
| 每条记录开始和结束时的状态 | 未规定 | 未规定 | 选中记录在批次两端的状态 | §3 没有给对象结构 |
| `process_version` | 未规定 | 未规定 | 处理规则的版本 | §3 没有给出版本字符串。与 Input 上的 `process_version` 是否同一个值，§3 未规定 |

## Digest

汇总快照。路径：`📋 Digests/cycles/{cycle_id}/r{n}.md`。

§3.4 的表是 frontmatter，没有必填列。下表不把「未写」改成「必填」。

| 字段 | 类型 | 必填 | 含义 | 取值规则 |
|---|---|---|---|---|
| `schema_version` | 字面量字符串 | 未规定 | 汇总规范版本 | `"digest-2.0"` |
| `type` | 字面量字符串 | 未规定 | 文档类型 | `cycle-digest` |
| `digest_id` | 字符串 | 未规定 | 汇总 ID | `dg-{cycle_id}` |
| `cycle_id` | 未规定 | 未规定 | 批次 ID | 同 Batch |
| `coverage_start` | 带偏移的 ISO 8601 | 未规定 | 本批覆盖的起点 | 同 Batch |
| `cutoff_at` | 带偏移的 ISO 8601 | 未规定 | 本批截止时间 | 同 Batch |
| `snapshot_revision` | 整数 | 未规定 | 快照修订号 | n。每次修订都另写一个 `r{n+1}.md`，旧文件永远不改（AC07） |
| `input_ids` | 字符串列表 | 未规定 | 本批全部条目 | 全部条目 |
| `source_weeks` | 未规定 | 未规定 | 本批涉及的周 | 本批涉及哪些周，每周多少条。数据结构 §3 未规定 |
| `counts` | 未规定 | 未规定 | 状态计数 | `ready` / `pending` / `failed` / `incomplete` / `total`。`total` == `len(input_ids)`，各项相加等于 total（AC06） |
| `late_or_cross_week` | 字符串列表 | 未规定 | 迟到或跨周材料 | 迟到或跨周材料的 id 列表 |
| `generated_at` | 带偏移的 ISO 8601 | 未规定 | 生成时间 | 存储用带时区偏移的 ISO 8601 |
| `generator` | 未规定 | 未规定 | 生成者 | §3 说明为「—」 |

`counts` 的四个状态词和 Input 的 `process_state` 不是同一套枚举。§3 没有写对应关系，本文不补。

正文：按 `topics` 聚合，每个主题一节。没打主题的放「待归类」一节，照样列出来。每条一行：`D-{cycle}-{nn}`｜一句话摘要｜来源链接｜状态｜是不是迟到或跨周。末尾三节：「失败和不完整」「历史关联（只放链接）」「本批来源统计（哪个来源是 0）」。`D-` 编号在一个批次里固定不变。周记、Idea、内容都用它连回来。`{cycle}` 和 `{nn}` 的具体拼法，§3 只给了这个模式。

## 合成样例

每类来源一条，Batch 一条，Digest 一条。全部是编造的标题和句子。URL 只用 `example.com`。

样例外层的 `source` 和 `input` 只是分组，不是字段。条件未触发的值，以及收集阶段留空的 `topics`、`summary_ref`、`process_version`，样例写成 `null`。§3 没有规定用 `null` 还是省略键。

样例里的 sha1 / sha256 按 UTF-8 字节、十六进制小写计算，sha1 取前 12 位，只为了能复核。§3 没有写编码和大小写。指纹覆盖的是下面各条写明的原文；规范化算法未使用，因为 §3 没有写步骤。

样例钟点只表示一个带偏移的时间，不是字段规则。`source_week` 写成 `2026-W42` 这种样子，因为 §3 只说 ISO 周，没有写字符串格式。`inbox_ref` 用 `路径#锚点`，连接符不是 §3 规定的。

### YouTube-Likes

`time_basis` 为 `platform`，`captured_at` 即点赞时间。`external_item_id` 按 `video_id@like_at` 拼接，`like_at` 用与 `captured_at` 相同的 ISO 8601。§3 没有规定 `@` 后面的时间格式。

指纹原文：`合成摘录：示例频道用虚构情节说明一个观点。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-youtube-exmplvid01",
    "platform": "youtube",
    "external_content_id": "exmplvid01",
    "canonical_url": "https://example.com/watch?v=exmplvid01",
    "title": "虚构标题：示例说明",
    "author": "Example Channel",
    "published_at": "2026-10-01T12:00:00+08:00",
    "raw_refs": [
      "📥 Inbox/YouTube-Likes/2026-10-14-exmplvid01.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-14T10:00:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-youtube-aa876cdaf5e3",
    "source_id": "src-youtube-exmplvid01",
    "external_item_id": "exmplvid01@2026-10-14T09:30:00+08:00",
    "event_type": "like",
    "captured_at": "2026-10-14T09:30:00+08:00",
    "time_basis": "platform",
    "received_at": "2026-10-14T10:00:00+08:00",
    "source_published_at": "2026-10-01T12:00:00+08:00",
    "source_week": "2026-W42",
    "origin": "collected",
    "content_fingerprint": "3941d306060eb0f4160e6bc95d62d2e44496b32cd678be59ae92dd99f03fe86c",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/YouTube-Likes/2026-10-14-exmplvid01.md#摘句"
  }
}
```

### Snipd

§4：每条 snip 没有自己的时间，新 snip 用 `time_basis=first_seen`。本条照此。`captured_at` 用首次捕获时间。

指纹原文：`合成摘录：示例播客里的一句虚构原话。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-snipd-11111111-1111-4111-8111-111111111111",
    "platform": "snipd",
    "external_content_id": "11111111-1111-4111-8111-111111111111",
    "canonical_url": "https://example.com/snipd/episodes/11111111-1111-4111-8111-111111111111",
    "title": "虚构标题：示例播客一集",
    "author": "Example Host",
    "published_at": "2026-09-01T08:00:00+08:00",
    "raw_refs": [
      "📥 Inbox/Snipd/example-show/synth-episode.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-18T08:15:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-snipd-6875f3fc2eff",
    "source_id": "src-snipd-11111111-1111-4111-8111-111111111111",
    "external_item_id": "22222222-2222-4222-8222-222222222222",
    "event_type": "snip",
    "captured_at": "2026-10-18T08:15:00+08:00",
    "time_basis": "first_seen",
    "received_at": "2026-10-18T08:15:00+08:00",
    "source_published_at": "2026-09-01T08:00:00+08:00",
    "source_week": "2026-W42",
    "origin": "collected",
    "content_fingerprint": "7418d4c958935036356c13ff5569e8c424e976b4cfdb424b92059a6f2e5a964c",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/Snipd/example-show/synth-episode.md#22222222-2222-4222-8222-222222222222"
  }
}
```

### WeRead

每条划线单独成为一条 Input。下面只有一条划线。同一 `bookId` 的另一条划线会是另一条 Input，Source 仍是这一条。

指纹原文：`合成划线：这是一句虚构的书中句子。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-weread-synthbook001",
    "platform": "weread",
    "external_content_id": "synthbook001",
    "canonical_url": "https://example.com/weread/book/synthbook001",
    "title": "虚构书名：示例手册",
    "author": "示例作者",
    "published_at": "2020-01-01T00:00:00+08:00",
    "raw_refs": [
      "📥 Inbox/WeRead/synthbook001.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-13T08:00:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-weread-6d560828fc45",
    "source_id": "src-weread-synthbook001",
    "external_item_id": "^synthbook001-1-10-20",
    "event_type": "highlight",
    "captured_at": "2026-10-12T21:05:00+08:00",
    "time_basis": "platform",
    "received_at": "2026-10-13T08:00:00+08:00",
    "source_published_at": "2020-01-01T00:00:00+08:00",
    "source_week": "2026-W42",
    "origin": "collected",
    "content_fingerprint": "793c679661f6af6016f35a7f0fe7e0c695c2e64b3f68b261feb032b908920574",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/WeRead/synthbook001.md#^synthbook001-1-10-20"
  }
}
```

### X-Bookmarks

纳入 Inbox（J04）。没有收藏时间。`time_basis` 为 `first_seen`，`captured_at` 用首次捕获时间。`external_item_id` 与 `external_content_id` 相同。`platform` 取值是 `x`。

指纹原文：`合成帖文：这是一条虚构的短帖。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-x-1000000000000000001",
    "platform": "x",
    "external_content_id": "1000000000000000001",
    "canonical_url": "https://example.com/x/status/1000000000000000001",
    "title": "虚构短帖：示例标题",
    "author": "example_user",
    "published_at": "2026-10-10T12:00:00+08:00",
    "raw_refs": [
      "📥 Inbox/X-Bookmarks/2026-10-18-example-user.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-18T16:00:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-x-bda5d173b6da",
    "source_id": "src-x-1000000000000000001",
    "external_item_id": "1000000000000000001",
    "event_type": "bookmark",
    "captured_at": "2026-10-18T16:00:00+08:00",
    "time_basis": "first_seen",
    "received_at": "2026-10-18T16:00:00+08:00",
    "source_published_at": "2026-10-10T12:00:00+08:00",
    "source_week": "2026-W42",
    "origin": "collected",
    "content_fingerprint": "5fe0dd5f05ab1de6e5e9248977f4ed6a381ca4395bc0355a0ac2e2213cc076e4",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/X-Bookmarks/2026-10-18-example-user.md#1000000000000000001"
  }
}
```

### Instagram-Saves

没有收藏时间。`time_basis` 为 `first_seen`，`captured_at` 用首次捕获时间。`published_at` 是视频发布时间，不是收藏时间。`external_item_id` 与 `external_content_id` 相同。

§4 另有一条：2021–2022 的大批文件标 `historical_import`，`source_week` 留空（AC05）。§3 只规定 `time_basis=unknown` 时 `source_week` 为空，没有写 `historical_import` 是否必须搭配 `unknown`。本条不合并这两句，只演示 `first_seen`。

指纹原文：`合成收藏：这是一条虚构的短视频说明。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-instagram-EXMPL00001",
    "platform": "instagram",
    "external_content_id": "EXMPL00001",
    "canonical_url": "https://example.com/p/EXMPL00001",
    "title": "虚构短视频：示例说明",
    "author": "example_author",
    "published_at": "2026-10-01T18:00:00+08:00",
    "raw_refs": [
      "📥 Inbox/Instagram-Saves/2026-10-01-example-author.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-16T19:40:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-instagram-4f845a930248",
    "source_id": "src-instagram-EXMPL00001",
    "external_item_id": "EXMPL00001",
    "event_type": "save",
    "captured_at": "2026-10-16T19:40:00+08:00",
    "time_basis": "first_seen",
    "received_at": "2026-10-16T19:40:00+08:00",
    "source_published_at": "2026-10-01T18:00:00+08:00",
    "source_week": "2026-W42",
    "origin": "collected",
    "content_fingerprint": "27d7702cdc2e0564f3ea74a7713209ab36886b0ac32122ac6dbfc6619daacf9c",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/Instagram-Saves/2026-10-01-example-author.md#EXMPL00001"
  }
}
```

### 想法

`platform` 为 `thought`。`external_item_id` 用 thought id。§3 的 `external_content_id` 清单没有想法，本条走「没有平台 ID」的 `source_id`：`src-thought-` + `u` + sha1 前 12 位。§3 没有规定想法的 `time_basis`；本条样例取 `platform`，因为记录自带 `captured_at`。这不是新规则。

指纹原文：`合成原话：这是一句虚构的随手记。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-thought-ua07dea66a1be",
    "platform": "thought",
    "external_content_id": null,
    "canonical_url": "https://example.com/thoughts/thought-20261020-example",
    "title": "虚构原话：示例一则",
    "author": null,
    "published_at": null,
    "raw_refs": [
      "📝 Journal/想法/thought-20261020-example.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-20T09:05:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-thought-1c47920095d4",
    "source_id": "src-thought-ua07dea66a1be",
    "external_item_id": "thought-20261020-example",
    "event_type": "thought",
    "captured_at": "2026-10-20T09:00:00+08:00",
    "time_basis": "platform",
    "received_at": "2026-10-20T09:05:00+08:00",
    "source_published_at": null,
    "source_week": "2026-W43",
    "origin": "collected",
    "content_fingerprint": "3ae699348b0d289c10e328d4a24b90be5409496cf0a9bad2d25170645e74bdb1",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📝 Journal/想法/thought-20261020-example.md#thought-20261020-example"
  }
}
```

### manual

§3 的 `platform` 含 `manual`，没有对应的 `external_content_id` 写法，也没有对应的 `event_type`。本条 `source_id` 用 URL 指纹。没有平台事件 ID，样例的 `event_key` 用与 `content_fingerprint` 相同的 sha256。§3 没有写这两处指纹必须相同。`event_type` 样例取 `note`。这不是新规则。`canonical_url` 用 example.com，因为 §3 要求每条 Source 都有 `canonical_url`，但没有写没有平台地址时填什么。

指纹原文：`合成笔记：这是一条虚构的手工记录。`

```json
{
  "source": {
    "schema_version": "inbox-0.1",
    "source_id": "src-manual-u888511f02cc3",
    "platform": "manual",
    "external_content_id": null,
    "canonical_url": "https://example.com/notes/synth-manual-001",
    "title": "虚构笔记：示例一条",
    "author": null,
    "published_at": null,
    "raw_refs": [
      "📥 Inbox/manual/synth-manual-001.md"
    ],
    "content_revision": 1,
    "first_seen_at": "2026-10-19T14:05:00+08:00"
  },
  "input": {
    "schema_version": "inbox-0.1",
    "input_id": "in-manual-0c21a1b7d316",
    "source_id": "src-manual-u888511f02cc3",
    "external_item_id": null,
    "event_type": "note",
    "captured_at": "2026-10-19T14:00:00+08:00",
    "time_basis": "platform",
    "received_at": "2026-10-19T14:05:00+08:00",
    "source_published_at": null,
    "source_week": "2026-W43",
    "origin": "collected",
    "content_fingerprint": "d06273963ddfaaf7ab116fef416571570870eefa0afe805ad501e18a82006769",
    "completeness": "full",
    "missing_reason": null,
    "process_state": "pending",
    "last_error": null,
    "last_cycle_id": null,
    "topics": null,
    "summary_ref": null,
    "process_version": null,
    "inbox_ref": "📥 Inbox/manual/synth-manual-001.md#note"
  }
}
```

### Batch

`cy-20261015` 的日期是周四。YouTube 那条的 `received_at` 早于 cutoff，状态是 `pending`，放进 `selected_input_ids`。X-Bookmarks 那条的 `received_at` 晚于 cutoff，放进 `late_input_ids`。

「每条记录开始和结束时的状态」没有对象结构。样例用规格原文做键，里面用 `input_id`、`开始`、`结束`，只为了 JSON 能解析。这不是字段规范。两端都写 `pending`，因为 §3 没有状态迁移表。`process_version` 留空，因为 §3 没有给出版本字符串。

```json
{
  "cycle_id": "cy-20261015",
  "cutoff_at": "2026-10-15T08:00:00+08:00",
  "coverage_start": "2026-10-08T08:00:00+08:00",
  "selected_input_ids": [
    "in-youtube-aa876cdaf5e3"
  ],
  "late_input_ids": [
    "in-x-bda5d173b6da"
  ],
  "每条记录开始和结束时的状态": [
    {
      "input_id": "in-youtube-aa876cdaf5e3",
      "开始": "pending",
      "结束": "pending"
    }
  ],
  "process_version": null
}
```

### Digest

下面是 frontmatter 字段的 JSON。文件本身仍是 §3.4 的 Markdown。`counts` 只演示加总：0+1+0+0 = 1 = `total` = `input_ids` 的条数。不表示 `process_state` 与 `ready` / `incomplete` 的对应。

`source_weeks` 样例写成「周 → 条数」。§3 没有规定这个结构。

正文一行（不是字段）：`D-cy-20261015-01`｜合成一句话｜`https://example.com/watch?v=exmplvid01`｜pending｜否

`D-{cycle}-{nn}` 里 `{cycle}` 样例填了 `cy-20261015`。§3 没有写 `{cycle}` 是 `cycle_id` 还是日期。末尾三节只保留 §3 的节名，样例不填正文。

```json
{
  "schema_version": "digest-2.0",
  "type": "cycle-digest",
  "digest_id": "dg-cy-20261015",
  "cycle_id": "cy-20261015",
  "coverage_start": "2026-10-08T08:00:00+08:00",
  "cutoff_at": "2026-10-15T08:00:00+08:00",
  "snapshot_revision": 1,
  "input_ids": [
    "in-youtube-aa876cdaf5e3"
  ],
  "source_weeks": {
    "2026-W42": 1
  },
  "counts": {
    "ready": 0,
    "pending": 1,
    "failed": 0,
    "incomplete": 0,
    "total": 1
  },
  "late_or_cross_week": [],
  "generated_at": "2026-10-15T20:00:00+08:00",
  "generator": "example"
}
```
