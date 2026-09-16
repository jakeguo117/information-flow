---
name: intake
description: Daily DigitalBrain index and Aristotelian discussion. Use when Jake says 「今天 Digest」「讨论 Digest」「今天摄入」「跑 Digest」or /intake. Appends reflection to that day's Digest. Does not write Journal.
---

# intake

信息流。不要救 Hermes。不要写 `📝 Journal/`。

## 每天生成（本机 21:00）

Digest 是**内容索引**（Snipd / WeRead / YouTube 标题+链接）。不写日子、不读日历/Reminders。没新内容不写文件。定时在 GitHub Actions，不依赖这台 Mac 开着。

```bash
python3 "$HOME/plugins/information-flow/scripts/youtube_likes.py"
python3 "$HOME/plugins/information-flow/scripts/daily_digest.py"
python3 "$HOME/plugins/information-flow/scripts/weekly_rollup.py"
```

Cursor 云端不要跑这些脚本。只读仓库里已有的 Digest。

## 讨论（亚里士多德式）

用户说「今天 Digest」或「讨论 YYYY-MM-DD Digest」：

1. 只拿该篇索引当材料。需要原文再打开它链到的 Snipd / WeRead / YouTube-Likes。
2. 先澄清前提，再追问矛盾，一次一个问题，不宣讲。
3. 他说可以记下之后：
   - 把 `## 讨论` **append** 到同一篇 Digest（上面的索引不动）
   - 每条结论必须有引用（wikilink 回具体来源）。有引用的 reflection **同时**写成 `📖 Resources/concepts/{短标题}.md`
   - 没有引用的心情句、纯逾期任务不进 wiki

Resource 卡片模板：

```markdown
---
date: {YYYY-MM-DD}
type: concept
source_digest: "[[📋 Digests/{YYYY-MM-DD}-Digest]]"
---

# {短标题}

{几条带引用的结论}

## 来源
- [[{具体 Snipd/YouTube/WeRead/Digest 条目}]]
```

Journal Brief 只收已经有 `## 讨论` 的天。
