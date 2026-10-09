# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面这些。摄入由 `intake` 生产。缺文件就跳过，不抓 Snipd / YouTube / WeRead 原文。

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。本机不可用时，按 SKILL.md 核验用户已授权的 DigitalBrain GitHub 仓库，经连接读取 main。先读取 `📝 Journal/素材/同步约定.md`，不要将旧默认规则当作撤销用户持续授权。

**自己认周。** ISO 周按 Asia/Shanghai 当天（周一 00:00 到周日 23:59）。目录名 `{YYYY}-W{nn}`。不要问 Jake 是哪一周。本周 `intake.md` 不存在，就用 `📋 Digests/` 里已有的最近一周。有脚本就跑 `python3 scripts/weekly_intake.py --vault "$VAULT"`。

## 读取顺序

1. `VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。学口气、未收的线、已经点名的老项目。不把正文写入 DigitalBrain memory。
2. 只打开那些周记里已经出现的 `🚀 Projects/` / `📖 Resources/` wikilink（老项目、很小的线）。不要扫整个项目目录来「补这周」。
3. 读取 `VAULT/📝 Journal/素材/` 按上海当前周命名的文件及此前尚未纳入正式周记的素材；只在该目录内定位。素材是 Jake 自己的输入，不需要 intake 勾选；保留未确定状态，不把它自动当 Evidence。当前周素材不随 intake 回落旧周。听完用户这次画像后再自然接续，不用素材抢先解释用户。正式周记最终纳入后，才在对应条目追加 `included_in` 链接；原素材保留，尚未纳入的继续待聊。只用 `type: journal` 的正式篇章计算周记编号。
4. 用上面规则解析出的 `VAULT/📋 Digests/{YYYY-Wnn}/intake.md`。只读 **`[x]`** 的条目和它们下面的 reflection，用来找和旧线的 **呼应**。Briefing / 未勾选只是索引，对不上就略过。
5. 本周相关 `VAULT/📖 Resources/` 卡片：讨论带引用时已经写进去的。周记只链，不再入库。

日 Digest 和 `📊 Journal Briefs/` 不再当输入。

随手想法素材按 SKILL.md 及用户有效持续授权追加、同步；正式周记成文在客户说「可以写 / 写吧 / OK 写」之前不落盘，持久写入只走 `skills/journal/tools/write_journal.py`。未勾选 intake 即使和旧线相关，也不进入落盘材料。

## 禁止当输入

- Snipd 插件 `📥 Inbox/Snipd/Data/` 全集
- YouTube 点赞原始列表 / 全文逐字稿（只读 intake 里的划线）
- WeRead 划线库原文
- Journal 以外、旧周记又没点名的私人目录
- `📋 Daily Briefings/`（日子/任务线，不是周记燃料）
- `📊 Weekly Synthesis/`（已停）
- `📊 Journal Briefs/`（已停，改由 intake.md 的 `[x]` 承担）
- `📖 Cognition/`（写完周记之后的另一层，不是周记输入）
