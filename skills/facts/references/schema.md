# Facts

schema_version = facts-0.1

依据是 Drive「02_数据规则与开发验收_V2.0_Draft」§2（文件 id `11gFwzKUxHsQ5_KSk3NFXcM_5vaB-QbJwrq5hk71XBIQ`）的 Fact 行：`statement`、`source_refs`（含段落或时间戳）、`as_of`、`measurement_scope`、`limitations`、`validation_state`、`validation_history`。PM 10-20 定了下面的键名、英文枚举、ID、时间和版本。D5、D6、D8 这次不做。D7 的真实存放位置不写死，工具没有默认路径。

一条 Fact 一个节点。对象 ID 稳定。一个节点可以没有任何周记引用（AC09）。入库不等于证实：不写 `validation_state` 不会变成 `verified`。

## 字段

| 键 | 写入时 | 说明 |
|---|---|---|
| `schema_version` | 必填 | 字面量 `"facts-0.1"`。其他版本拒绝写 |
| `fact_id` | 第一次写入时由工具计算 | 见下方 ID。格式 `^fact-[0-9a-f]{12}$` |
| `statement` | 必填 | 原始陈述。关键词在这里找。strip 之后为空则拒绝 |
| `source_refs` | 必填，字符串列表，至少一项 | 每一项是链接，再加上段落或时间戳。Draft 02 §2 没有把这一项拆成对象字段，工具不拆开，哈希用整段字符串 |
| `as_of` | 必填 | `YYYY-MM-DD`，或带 `+08:00` 的 `YYYY-MM-DDTHH:MM:SS+08:00`。其他拒绝 |
| `validation_state` | 必填 | 只能是下表四个英文值 |
| `measurement_scope` | 可选 | 时间或统计口径 |
| `limitations` | 可选 | 限制 |
| `validation_basis` | 可选 | 核验依据 |
| `recorded_at` | 工具自动写 | 带偏移的 ISO 8601，时区 Asia/Hong_Kong，如 `2026-10-20T11:50:00+08:00` |
| `visibility` | 有默认值 | 省略时写 `"private-jake"`。建议取值 `private-jake`｜`team`｜`public-ok`，T40 前定。工具不校验取值 |

`validation_history` 不另设字段。它就是同一个 `fact_id` 按写入顺序追加的那些行。

## 验证状态

存英文。显示用中文。

| 存储 | 显示 |
|---|---|
| `unverified` | 待核验 |
| `verified` | 已核验 |
| `disputed` | 有争议 |
| `corrected` | 已更正 |

## ID

只在这个 `fact_id` 第一次写入时计算，之后改状态或更正都沿用，不重算。

`fact-{sha1(首个 source_ref + '|' + 首次写入的 statement)[:12]}`

sha1 按 UTF-8 字节、十六进制小写，取前 12 位。调用方可以先 `--dry-run`，从输出里拿 `fact_id`。第一次写入如果自己带了 `fact_id`，必须和这个公式一致。`fact_id` strip 之后为空，算缺字段，拒绝。

例：`source_ref` 为 `https://example.com/synthetic#p1`，`statement` 为 `合成事实，关键词是南瓜。`。拼接是 `https://example.com/synthetic#p1|合成事实，关键词是南瓜。`，`fact_id` 为 `fact-3bc1db9181f7`。`#p1` 只是这一条例子里的段落位置，不是连接符规则。

## 历史

改 `validation_state` 或更正时，追加一条新记录。已写下的记录不改写，也不删除。新行不从旧行抄字段。

目标文件非空，且最后一个字节不是 `\n` 时，拒绝写入，退出码非 0，原文件一个字节不动。

这次不规定状态迁移，也不从历史里另算一条「当前状态」。`retrieve` 命中一个节点时，返回该 `fact_id` 的全部记录。

## 检索

`retrieve` 用关键词在各条记录的 `statement` 里做子串匹配，区分大小写。匹配规则的其余部分（D8）这次不做。

## 存放

调用方用 `--out` 指定目录或文件。已经存在的目录，追加到该目录下的 `facts.jsonl`。不存在的路径当成文件。上级目录必须已经存在；`--dry-run` 也做这个检查，不存在则退出码非 0，不创建目录。`--dry-run` 不写文件。

真实存放位置（D7）不写进工具，工具不设默认路径。
