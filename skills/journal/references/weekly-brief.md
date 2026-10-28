# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面的读取顺序。不抓 Snipd / YouTube / WeRead 原文。

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。

**自己认周。** ISO 周按 Asia/Shanghai 当天（周一 00:00 到周日 23:59）。不要问 Jake 是哪一周。本周周四的日期写成 `cycle_id`，形式 `cy-YYYYMMDD`。

## 读取顺序

① 旧周记 2–3 篇。`VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。学口气、未收的线、已经点名的老项目。不把正文写入 DigitalBrain memory。只打开那些周记里已经出现的 `🚀 Projects/` / `📖 Resources/` wikilink（老项目、很小的线）。不要扫整个项目目录来「补这周」。

② 周四汇总快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`。`cycle_id` 是本周周四（Asia/Shanghai）的 `cy-YYYYMMDD`。同一个 cycle 里取编号最大的 `r{n}.md`（n 按整数比）。不回落到另一周：这个 cycle 没有快照，就说本周没有周四汇总快照。不要改开别的 `cycle_id`，不要改开 `📋 Digests/daily/`，不要改开旧的 `📋 Digests/{YYYY-Wnn}/digest.md` 或 `📋 Digests/weekly-briefs/`，也不要按周去读 intake。不要自己编条目。写周记时不要生成这份快照，也不要手写占位。

③ 未消化想法。`VAULT/📝 Journal/想法/` 里所有未消化想法。用 `skills/journal/tools/capture_thought.py list-open`。未消化 = 想法文件的 id，减去 `想法/digests/` 任一清单里出现过的 id，不限本周。清单里是「看过未展开」的不再读。想法是燃料，不整段贴进周记，原话保持文件里的字节。消化清单和想法文件都不是周记。

客户说「可以写 / 写吧 / OK 写」之前不落盘周记。周记持久写入只走 `skills/journal/tools/write_journal.py`。想法的新文件只走 `capture_thought.py`。消化清单只在 `write_journal.py` 成功之后写。讨论里已经写进 `📖 Resources/` 的卡片，周记只链，不再入库。

## 禁止当输入

- Snipd 插件 `📥 Inbox/Snipd/Data/` 全集
- YouTube 点赞原始列表 / 全文逐字稿
- WeRead 划线库原文
- Journal 以外、旧周记又没点名的私人目录
- `📋 Daily Briefings/`（日子/任务线，不是周记燃料）
- `📊 Weekly Synthesis/`（已停）
- `📊 Journal Briefs/`（已停）
- `📖 Cognition/`（写完周记之后的另一层，不是周记输入）
- `📋 Digests/daily/`，以及旧路径 `📋 Digests/{YYYY-Wnn}/digest.md`、`📋 Digests/weekly-briefs/`

## 交接

周四 `weekly-digest.yml` schedule 已停。上面的周四快照只作归档，没有文件不要生成。平日归堆是 `📋 Digests/cluster/YYYY-MM-DD.md`（多日 `YYYY-MM-DD_DD.md`），想法梳理落盘，Cloud Agent 推 `jakeguo117/obsidian-digitalbrain`。周记落盘当下不跑 `discuss-to-resources-ideas`。周六才扫本周 cluster 和已落盘的 `📝 Journal/{YYYY-MM-DD}*.md`。不接管历史 `📋 Digests/daily/`。takeaway 已 offline，本 PR 不另挂停排程。
