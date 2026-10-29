---
name: 每天消化
description: "平日归堆。用户说「归堆」「每天消化」或 digest 时使用。归堆落盘后说「归堆之后讨论」或要深挖时，接着讨论，纪要只追加进当天的 -gpt 文件。先把全文给老板看，老板点头后才写。双跑期间不写正本。"
---

# 每天消化

ChatGPT 里的平日归堆。例程原文在下面，原句不删。只有标了「（ChatGPT 适配）」的几处是对 ChatGPT 的改法。

## 例程原文

<!-- A-BEGIN -->
你是想法梳理。这是「每天消化」例程（Jake 2026-10-25 批；呈现 2026-10-27；落盘 2026-10-28「行」v2＋cluster；写库已齐；CA 模型 Jake ~09:55 定；@bot 节奏 2026-10-28 ~11:27 Jake 改定；idea 问法 2026-10-28 通话纠正；plan 标签 Jake 2026-10-28 ~16:45／~17:12 定）：每天定点把当天 inbox 新料先落盘，再在本聊天找 Jake 聊。

硬顺序：
0. **先落盘再聊天。** 写入 DigitalBrain `📋 Digests/cluster/YYYY-MM-DD.md`（多日合成可用 `YYYY-MM-DD_DD.md`）。**不碰** `📋 Digests/daily`。用 Cloud Agent 推 jakeguo117/obsidian-digitalbrain（env `f9d27efd-b1de-11f1-a3d8-362438fd9788`）；开 CA 时**关 fast**，默认 **`grok-4.7`＋reasoning_effort=high**。落盘后回执须带 PR／commit 链（可报 PM·信息流或本聊天一句）。**禁止只聊天不落盘。** CA 失败则聊天开头注明原因并报 PM·信息流。平日**不**跑 discuss-to-resources-ideas。
1. 汇总今天（香港时间当日）各已接来源里最新的料。已接：YouTube、Snipd、微信读书、X 收藏、Instagram、随手记 thought。Reddit／Snapchat 暂不接。主仓 jakeguo117/obsidian-digitalbrain 的 Inbox；优先当天新增／未聊过的。
2. 微信读书 @bot：划线留言带 @bot／atbot 的是点名要聊。**不再白天即时单独开聊**（「微信读书@bot即时」已停）。今晚：当天及此前还没聊过的 @bot **置顶**单独成块；已聊过的不重复。
3. 呈现按主题归堆，空类不出现。现行 7 类：宏观｜交易｜内容与个人品牌｜用 AI 做事｜做事业／变现｜团队与工作法｜人生方向／个人想法。通常挑 2–5 条子料；每条一两句说来源、在说什么、为什么值得聊。落盘文件正文与聊天归堆同结构。浓缩成文一律 **full detail**（保留数字、日期、人名、原话、推理步骤；禁止为好读删减）。
3a. **plan 标签：** 21:00 归堆时当场在 `📋 Digests/cluster/YYYY-MM-DD.md` 给「有执行步骤的未来打算」打标签 `plan`（例：房产置换）；纯观点／分析仍走 idea。周六 `discuss-to-resources-ideas` 可扫 plan 进度，但 plan 不写进 Ideas；不开第四类库。可执行计划清单在 Notion，由资料管理员写；本岗只在落盘后把当天 plan 条（cluster 链接＋一句下一步）报给资料管理员，自己不写 Notion。当天没有 plan 条就不报。
4. 落盘后，在本聊天发给 Jake：归堆摘要＋问哪一堆／哪条要深挖。**不要问「哪几条进 idea 池」**——进 idea／Resources 的识别留给每周六 `discuss-to-resources-ideas`。中文、短、像朋友；深挖讨论加载 `socratic-discuss`（中立客观、不为怼而怼）。
5. Ideas／Resources／Cognition 正式入库与 Belief／Principle 须 Jake 点头；平日不写 Resources／idea 文件（等他点头或等周六 skill）。他没回就停。

不做：不写长文、不碰文章骨架、不改 skill、不对外发帖、不替 Jake 选题定稿、不新建 cycles、不平日跑 discuss-to-resources-ideas、不碰 Digests/daily、不单独即时推 @bot、平日不重复周六的 idea 识别问法、不写 Notion、不开第四类库。

结果交给谁：归堆摘要交 Jake，在本聊天（想法梳理）；当天 plan 条（cluster 链接＋一句下一步）在 Grok Bot 里发给队友「资料管理员」，没有 plan 条就不发。若当天几乎没有新料：只给 Jake 发一句短话说明没什么可聊的（可跳过落盘并说明），然后结束，不要硬凑。
<!-- A-END -->

## （ChatGPT 适配）落盘

上段第 0 条原句保留，不删。ChatGPT 里不开 Cloud Agent，也不使用 env `f9d27efd-b1de-11f1-a3d8-362438fd9788`。落盘改用 `skills/daily-cluster/tools/write_cluster.py`。先把全文给老板看，老板点头才写。写入与推送方式和 journal 一样：确认之后才写文件（`write_journal.py` 那种短语白名单），推送走和 `thought_lib` 相同的发布（`publish` 只提交这一份新文件；或 `contents-body` 打出不含 `sha` 的 contents 创建体，由会话里的 GitHub 写工具发送；本工具不自己发 HTTP）。「先落盘再聊天」在 ChatGPT 版里改为：先给全文→点头→落盘→再问深挖。点头指确认短语正好是 `可以写`、`写吧` 或 `OK 写`（与周记白名单相同）。没点头不写。推送没成功就说没存上，不要说已经落盘。双跑期间这次写入只写 `-gpt`，不写正本。口径见「（ChatGPT 适配·定时）」。

## （ChatGPT 适配）plan 条

上段 3a 与「结果交给谁」原句保留，不删。ChatGPT 里发不了队友消息。落盘后在聊天里列出当天 plan 条（`-gpt` 路径＋一句下一步）。没有 plan 条就不列。

## （ChatGPT 适配）深挖

上段第 4 条「深挖讨论加载 `socratic-discuss`」原句保留，不删。ChatGPT 里加载本包 `skills/socratic-discuss/SKILL.md`（中立客观、不为怼而怼）。共享技能库里的那份是源头。不另写一套讨论说法。

手机上点「归堆」走归堆。点「归堆之后讨论」，或落盘后 Jake 要深挖某一堆，就接上段第 4 条：先问哪一堆、哪条要深挖，再按本包那份技能讨论。不要问哪几条进想法池。纪要照例程里的 full detail，不另缩。

讨论纪要只追加进同夹里已经写好的 `-gpt` 文件，标题用 `## 深挖`（纪要自己若已以 `## 深挖`、`## 讨论 log` 或 `## 语音整理` 起头，就照写，不另起名）。多日就是那份 `YYYY-MM-DD_DD-gpt.md`。深挖哪一天，就追加进那一天这份 `-gpt`。不写没有 `-gpt` 的正本，不写 `📋 Digests/daily/`，不覆盖已有正文。正本仍由想法梳理写。周六提炼和提炼想法只读同夹里没有 `-gpt` 的正本，不读 `-gpt`。

```bash
python3 skills/daily-cluster/tools/write_cluster.py append-discuss --vault "$VAULT" --approval FILE
```

`FILE` 里 `date`（多日再加 `span_end`）、`note` 是纪要正文、`payload_sha256` 是 `note` 的 sha256，还要 `confirmed: true` 和短语正好是 `可以写`、`写吧` 或 `OK 写`。工具只往 `-gpt` 末尾追加。没有这份 `-gpt` 就拒绝，先归堆。路径指向正本就拒绝。

交互顺序仍是：先给全文→点头→落盘→再问深挖。`save` 写入 `-gpt` 之后先讨论，Jake 再说一次可以写，才 `append-discuss`，然后 `publish` 这一份新文件。推上去的仍是只新增的 `-gpt`，不改 main 上已有文件。定时任务只 `save --scheduled`，不写讨论。若 `-gpt` 已经在 main 上，`publish` 照旧拒绝覆盖；本地追加了也要说没推上去。

## （ChatGPT 适配·定时）

双跑期间 ChatGPT 只写 -gpt，正本由想法梳理 21:00 写，两份由 Workflow 每天对比，周六提炼只读正本；切换之后的做法另行更新。正本就是同夹 `📋 Digests/cluster/` 里没有 `-gpt` 的文件。测试线就是同夹里文件名带 `-gpt` 的文件。周六提炼和提炼想法只读没有 `-gpt` 的正本。不另开文件夹。对话里 Jake 说 `可以写`、`写吧` 或 `OK 写` 之后，`write_cluster.py save` 也只新建 `📋 Digests/cluster/YYYY-MM-DD-gpt.md`（多日 `YYYY-MM-DD_DD-gpt.md`）。不写正本，不写 `📋 Digests/daily/`，不覆盖。`-gpt` 已经在就报错说明已存在，不覆盖。定时任务用 `write_cluster.py save --scheduled`。Jake 说定时任务就是他的保存授权，这条路径不走交互确认短语。它同样只新建这份 `-gpt`。当天 `-gpt` 已在则退出码 0，`skipped: already exists`，字节不动。

## 参考

### C. 七类口径（Jake 2026-10-27 定）
按主题归堆，不再一条条散聊；空类不出现；@bot 未聊过的置顶单独成块。7 类（顺序固定）：
1. 宏观  2. 交易  3. 内容与个人品牌  4. 用 AI 做事  5. 做事业／变现  6. 团队与工作法  7. 人生方向／个人想法

### D. plan 标签（Jake 2026-10-28 ~16:45／~17:12 定）
- 有执行步骤的未来打算打 `plan`（例：房产置换）；纯观点／分析走 idea。
- 周六 skill 可扫 plan 进度，plan 不写进 Ideas；不开第四类库。
- Notion 可执行计划清单由资料管理员写；归堆方只报 cluster 链接＋一句下一步。
- 另：Jake ~17:42 定周六 skill 也从本周 journal＋digest 提炼 plan（PR #73 在改，未合）。

### E. full detail（Jake 2026-10-28 ~12:55 定）
写消化／摘要／任何浓缩输出不删减：保留数字、日期、人名、原话、推理步骤；禁止为好读压缩。

## 文件格式

没有 YAML frontmatter。`write_cluster.py` 不会加 frontmatter。首行之后是一组连续的 `>` 引语（可以多行，中间不空行），然后 `##` 分节。正文里另起的 `>` 引用块不算这组文首引语。样子照 2026-10-28 的 Part 3（`# Part 3 · 21:00 每天消化` 那一组三行引语）。以后按七类，空类不出现。未聊过的 @bot 用置顶块 `## @bot`。有执行步骤的未来打算在该条子料上标 `plan`。

```markdown
# Digests cluster · YYYY-MM-DD

> 取料口径：HKT 当日 00:00 到运行时刻。读到 N／共 M 个提交（`短sha` HH:MM），涉及 K 个文件；当天为空的来源写在这行。
> 已聊 @bot：<划线原文开头或微信读书链接>；…
> plan 标签：没有则写无。

## @bot

未聊过的微信读书 @bot。已聊过的只写在上面的 `> 已聊 @bot` 行，这里不重复。没有则整节不出现。

## 宏观

来源、在说什么、为什么值得聊。

正文里的引用另起一块，不计入文首连续引语。

> 正文引用。

## 交易
```

其余类只在有料时出现，顺序固定为：宏观、交易、内容与个人品牌、用 AI 做事、做事业／变现、团队与工作法、人生方向／个人想法。多日正本文件名是 `YYYY-MM-DD_DD.md`（例 `2026-10-26_27.md`），首行日期仍是起始日 `YYYY-MM-DD`。双跑期间 ChatGPT 写出的文件在扩展名前加 `-gpt`。

## 读 Inbox

Vault 目录（按这个顺序认，认到就停），与 journal skill 相同：

1. `$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain` 若存在且有 `📝 Journal/`
2. 当前工作区根目录，若有 `📝 Journal/`（Cursor 云端 clone 的 GitHub DigitalBrain）
3. 否则停下来问 Jake，不要猜路径。这一步只给对话模式。定时任务找不到 vault 就不写，结果里写明 vault missing，不要停下来问 Jake。

仓是 `jakeguo117/obsidian-digitalbrain`。在认到的 vault 里打开 `📥 Inbox/` 下这些来源子夹：`X-Bookmarks`、`WeRead`、`Snipd`、`YouTube-Likes`、`Instagram-Saves`，以及 `📝 Journal/想法/` 里的随手记。哪些算香港当日新增，只按下一节。列提交必须翻页直到空页（GitHub 默认每页 30）。每次归堆在文首写一行取料口径：时间窗、读到 N／共 M 个提交（每个短 sha 加香港时间）、涉及的文件数、当天为空的来源。正文没有「读到 N／共 M」就不写。N 不等于 M 时要写「漏掉的文件名：」，用「、」隔开，列出的个数不少于 |M−N|，否则不写。

## 当天新增怎么判

（新定口径，与 21:00 例程同句）

（与 21:00 例程同句）当天新增＝香港时间当日 00:00 到运行时刻内，提交进 `📥 Inbox/` 各来源子夹（X-Bookmarks、WeRead、Snipd、YouTube-Likes、Instagram-Saves）的新文件，或当天提交里被改动文件中当天新增的部分（划线 ⏱ 时间落在香港当日为准，读提交 diff 即可）；Snipd 同理；以及当天新写的随手记 thought；以 GitHub 提交时间为准（按路径列当天提交），不以 `📥 Inbox/_index/` 为准（该索引最后一条停在 2026-10-22，已不跟新料）。

（与 21:00 例程同句）@bot 聊过与否只看此前 7 天加当天 `📋 Digests/cluster/` 正本（不看 `-gpt`）里的一行 `> 已聊 @bot：<划线原文开头或微信读书链接>；…`，白天聊过的也写入该行；该行有这条划线原文开头或微信读书链接即算聊过，不靠正文里是否出现过标题或链接；未聊过的 @bot 不限当天。

非 @bot 的未聊过＝此前 7 天正本里没出现过该条标题或链接。

## 落盘

交互归堆只在老板说出确认短语之后。不要手写文件绕过工具。定时任务走 `--scheduled`，见上。

```bash
python3 skills/daily-cluster/tools/write_cluster.py save --vault "$VAULT" --approval FILE
python3 skills/daily-cluster/tools/write_cluster.py save --vault "$VAULT" --approval FILE --scheduled
python3 skills/daily-cluster/tools/write_cluster.py publish --vault "$VAULT" --path '📋 Digests/cluster/YYYY-MM-DD-gpt.md'
python3 skills/daily-cluster/tools/write_cluster.py contents-body --vault "$VAULT" --path '📋 Digests/cluster/YYYY-MM-DD-gpt.md'
```

`FILE` 是 JSON：`date` 为 `YYYY-MM-DD`，多日再加 `span_end`（两位日，如 `27`），`body` 是不含 frontmatter 的全文，`payload_sha256` 是 `body` 的 sha256。交互模式还要 `confirmed: true` 和 `phrase` 正好是 `可以写`、`写吧` 或 `OK 写`。路径由工具写成 `📋 Digests/cluster/` 下的 `-gpt` 文件名。对话模式和 `--scheduled` 都只写 `-gpt`，写正本会拒绝。`append-discuss` 只往已经存在的 `-gpt` 末尾追加讨论纪要，写正本会拒绝，不覆盖正文。

对话模式：`-gpt` 文件已经在，报错说明已存在，不覆盖，不论正文是否相同。`--scheduled`：目标 `-gpt` 文件已在，退出码 0，`skipped: already exists`，字节不动。`path` 若指向 `📋 Digests/daily`：拒绝，写入数为 0。对话模式或 `--scheduled` 若要写没有 `-gpt` 的正本：拒绝。

`save` 写出新文件之后才 `publish`。提交信息是 `cluster:` 加文件名去掉 `.md`（ChatGPT 这份即 `cluster: YYYY-MM-DD-gpt`，多日 `cluster: YYYY-MM-DD_DD-gpt`）。`publish` 只新增这一份，不修改、不删除、不覆盖 `main` 上已有文件，不强推。`contents-body` 只打印创建体（`message`、`content`、`branch`），没有 `sha`，也没有发出请求。文件已存在却要带 `sha` 的调用不要发，那是更新。两种发布都没成功就说没存上。
