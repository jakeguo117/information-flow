# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面这些。摄入由 `intake` 生产。缺文件就跳过，不抓 Snipd / YouTube / WeRead 原文。

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。

ISO 周：本周周一 00:00 到周日 23:59（本地）。目录名 `{YYYY}-W{nn}`，例如 `2026-W38`。

## 读取顺序

1. `VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。只学口气和未收的线。不把正文写入 DigitalBrain memory。
2. `VAULT/📋 Digests/{YYYY-Wnn}/intake.md`。只读 **`[x]`** 的条目和它们下面的 reflection。Briefing / 未勾选只是索引，对不上就略过。
3. 本周相关 `VAULT/📖 Resources/` 卡片：讨论带引用时已经写进去的。周记只链，不再入库。

日 Digest 和 `📊 Journal Briefs/` 不再当输入。

## 禁止当输入

- Snipd 插件 `Snipd/Data/` 全集
- YouTube 点赞原始列表 / 全文逐字稿（只读 intake 里的划线）
- WeRead 划线库原文
- Journal 以外的私人目录当「这周发生了什么」的替代
- `📋 Daily Briefings/`（日子/任务线，不是周记燃料）
- `📊 Weekly Synthesis/`（已停）
- `📊 Journal Briefs/`（已停，改由 intake.md 的 `[x]` 承担）
