# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面这些。摄入由 `intake` 生产。缺文件就跳过，不抓 Snipd / YouTube / WeRead 原文。

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。

ISO 周：本周周一 00:00 到周日 23:59（本地）。

## 读取顺序

1. `VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。只学口气和未收的线。不把正文写入 DigitalBrain memory。
2. `VAULT/📋 Digests/` 本周正式 Digest。优先读已有 `## 讨论` 的篇。没讨论过的只是索引，对不上就略过。
3. 本周汇总（若有）：`VAULT/📊 Journal Briefs/{YYYY}-W{nn}.md`（只含已讨论的天）。
4. 本周相关 `VAULT/📖 Resources/` 卡片：讨论带引用时已经写进去的。周记只链，不再入库。

## 周汇总

`📊 Journal Briefs/{YYYY}-W{nn}.md`

由 `intake` 每天 21:00 日更之后重写。每条一行来源 + 一句划线。只收 `generator: journal-daily-digest` 的每日篇。

## 禁止当输入

- Snipd 插件 `Snipd/Data/` 全集
- YouTube 点赞原始列表 / 全文逐字稿（只读 Digest 里的摘句）
- WeRead 划线库原文
- Journal 以外的私人目录当「这周发生了什么」的替代
- `📋 Daily Briefings/`（日子/任务线，不是周记燃料）
- `📊 Weekly Synthesis/`（已停）
