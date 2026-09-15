# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面这些。摄入由 `intake` 生产。缺文件就跳过，不抓 Snipd / YouTube / WeRead 原文。

## Vault

优先本机：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`  
否则当前工作区根（Cursor 云端 clone 的 DigitalBrain，须有 `📝 Journal/`）。

ISO 周：本周周一 00:00 到周日 23:59（本地）。

## 读取顺序

1. `VAULT/📝 Journal/` 最近 2–3 篇（按文件名倒序）。只学口气和未收的线。不把正文写入 DigitalBrain memory。
2. `VAULT/📋 Digests/` 本周**全部**正式 Digest。跳过文件名含「非正式」「演示」「历史主题」的。
3. 本周汇总（若有）：优先 `VAULT/📊 Journal Briefs/{YYYY}-W{nn}.md`。没有就不要编一份假的；当场从本周每日 Digest 收 3–7 条讨论线索。
4. 本周相关 `VAULT/📖 Resources/` 卡片：仅当 Digest 或汇总里链到它们。

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
