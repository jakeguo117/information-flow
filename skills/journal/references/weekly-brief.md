# 周记输入接口

最终闭环见 `setup.md`。周记 skill 只读下面的读取顺序。不抓 Snipd / YouTube / WeRead 原文。不读 digest，不读 `📋 Digests/cluster/`，不读周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`，也不读周 digest。

## Vault

按这个顺序认，认到就停。和 `SKILL.md` 的 Vault 目录同一套：

1. 本机 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain` 若存在且有 `📝 Journal/`
2. 当前工作区根（须有 `📝 Journal/`）
3. 否则用本会话 GitHub 读 `jakeguo117/obsidian-digitalbrain` 的 `main`。不要先问路径，不要猜本机路径。
4. 这座仓也 404 或无授权，才问 Jake。单个文件 404 不是仓读不到。

## 读取顺序

① 旧周记 3–4 篇。`VAULT/📝 Journal/` 按文件名倒序取最新的 3–4 篇。给 Jake 一段 recap：还没收的线、发生过什么、已经点名的项目。学口气。不把正文写入 DigitalBrain memory。只打开那些周记里已经出现的 `🚀 Projects/` / `📖 Resources/` wikilink（老项目、很小的线）。不要扫整个项目目录来「补这周」。**旧周记里的状态不能当作本周事实说。** 这一步的 recap 说给 Jake。

② Notion。用本会话里的 Notion 连接看最近在做什么：正在推进的项、待办池、可执行计划清单。Notion 读不到就用一句话说明，然后只按 ① 继续；不要编 Notion 里的内容。

③ 讨论时才看未消化想法。`VAULT/📝 Journal/想法/` 里所有未消化想法。用 `skills/journal/tools/capture_thought.py list-open`。未消化 = 想法文件的 id，减去 `想法/digests/` 任一清单里出现过的 id，不限本周。清单里是「看过未展开」的不再读。想法是燃料，不整段贴进周记，原话保持文件里的字节。消化清单和想法文件都不是周记。这不是第一步，也不代替 recap。没有本地目录、已走 GitHub 时，不要跑 `list-open`，改为用 GitHub 读 `📝 Journal/想法/` 和 `📝 Journal/想法/digests/`，按同一条未消化规则减掉清单里出现过的 id。

客户说「可以写 / 写吧 / OK 写」之前不落盘周记。周记持久写入只走 `skills/journal/tools/write_journal.py`，不带 `--digest-snapshot`。想法的新文件只走 `capture_thought.py`。消化清单只在 `write_journal.py` 成功之后写。讨论里已经写进 `📖 Resources/` 的卡片，周记只链，不再入库。

## 禁止当输入

- digest、周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`、周 digest
- `📋 Digests/cluster/`（归堆不是写周记的输入）
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

周四 `weekly-digest.yml` schedule 已停。周四快照只作归档，写周记不读、没有文件也不要生成。平日归堆是 `📋 Digests/cluster/YYYY-MM-DD.md`（多日 `YYYY-MM-DD_DD.md`），想法梳理落盘，不是本技能读的。周六才扫本周 cluster 主文件和已落盘的 `📝 Journal/{YYYY-MM-DD}*.md`。不接管历史 `📋 Digests/daily/`。takeaway 已 offline，本 PR 不另挂停排程。
