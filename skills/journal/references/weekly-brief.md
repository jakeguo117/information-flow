# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面这些。摄入由 `intake` 生产。除当周 digest 以外，缺文件就跳过，不抓 Snipd / YouTube / WeRead 原文。**「缺文件就跳过」不适用于 digest。**

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。

**自己认周。** ISO 周按 Asia/Shanghai 当天（周一 00:00 到周日 23:59）。目录名 `{YYYY}-W{nn}`。不要问 Jake 是哪一周。本周 `intake.md` 不存在，就用 `📋 Digests/` 里已有的最近一周。有脚本就跑 `python3 scripts/weekly_intake.py --vault "$VAULT"`。

## 读取顺序

0. `VAULT/📋 Digests/{YYYY-Wnn}/digest.md`。周是 Asia/Shanghai 当天的 ISO 周，不回落到别的周。三组按有用程度，不按来源，也不靠标题关键词：值得讨论的、可以引用的、可以借用的。只有文件里的组标题或 `group:` / `分组:` 才算已经分组；其余在「待分组」。展示时把待分组的 `P-2026W42-1` 分进三组，编号仍用文件里的，不要另编。已分组的编号是 `T-2026W42-1`、`F-2026W42-1`、`C-2026W42-1`。每条先编号，再一句话和链接。空组是「本周无」，说没有，不要补。值得讨论的下面有「我的看法：」。这个文件不在时，再查 `VAULT/📋 Digests/weekly-briefs/{YYYY-Wnn}.md` 和 `VAULT/📋 Digests/weekly-briefs/{YYYY-Wnn}/digest.md`，并说明实际打开的是哪一条。两处都没有，就说「本周 digest 还没有」，不要自己编，也不要跳过。digest 由 `scripts/build_weekly_digest.py` 写成上面的正式路径；已有文件不覆盖。写周记时不要跑这个脚本，也不要手写占位 digest。**「缺文件就跳过」不适用于 digest。**
1. `VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。学口气、未收的线、已经点名的老项目。不把正文写入 DigitalBrain memory。
2. 只打开那些周记里已经出现的 `🚀 Projects/` / `📖 Resources/` wikilink（老项目、很小的线）。不要扫整个项目目录来「补这周」。
3. 用上面规则解析出的 `VAULT/📋 Digests/{YYYY-Wnn}/intake.md`。只读 **`[x]`** 的条目和它们下面的 reflection，用来找和旧线的 **呼应**。Briefing / 未勾选只是索引，对不上就略过。
4. 本周相关 `VAULT/📖 Resources/` 卡片：讨论带引用时已经写进去的。周记只链，不再入库。
5. `VAULT/📝 Journal/想法/` 里所有未消化想法。用 `skills/journal/tools/capture_thought.py list-open`。未消化 = 想法文件的 id，减去 `想法/digests/` 任一清单里出现过的 id，不限本周。清单里是「看过未展开」的不再读。想法是燃料，不整段贴进周记，原话保持文件里的字节。消化清单和想法文件都不是周记。

日 Digest 文件和 `📊 Journal Briefs/` 不再当周记输入。周记只读已经收好的当周 `digest.md`（见读取顺序 0）。

客户说「可以写 / 写吧 / OK 写」之前不落盘周记。周记持久写入只走 `skills/journal/tools/write_journal.py`。未勾选 intake 即使和旧线相关，也不进入落盘材料。想法的新文件只走 `capture_thought.py`。消化清单只在 `write_journal.py` 成功之后写。

## 禁止当输入

- Snipd 插件 `📥 Inbox/Snipd/Data/` 全集
- YouTube 点赞原始列表 / 全文逐字稿（只读 intake 里的划线）
- WeRead 划线库原文
- Journal 以外、旧周记又没点名的私人目录
- `📋 Daily Briefings/`（日子/任务线，不是周记燃料）
- `📊 Weekly Synthesis/`（已停）
- `📊 Journal Briefs/`（已停，改由 intake.md 的 `[x]` 承担）
- `📖 Cognition/`（写完周记之后的另一层，不是周记输入）
