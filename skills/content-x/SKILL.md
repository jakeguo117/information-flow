---
name: content-x
description: "X 运营写 X 长文母稿（X、X Article、X 长文或 X 短帖）。必须先加载 content-core，再只加载本技能。出图前加载 canvas-design。同一写作上下文禁止 Skill load content-xhs 或 content-wechat。内容写手和公众号编辑不写母稿、不加载本技能。中文长文约 3000 字，口语叙事，交 X Articles 阅读页：5:2 封面，正文 1–3 张全宽真图。短帖可以不配图。不代发。"
---

# content-x

写 X、X Article、X 长文或 X 短帖。这里只写平台版式和写法。敏感、逻辑链、禁 Journal 原话、图源、不代发，都在 content-core，不在这里复述。一次交齐三版的适用范围在 content-core：只要 X 时不适用。

谁加载：X 运营，写 X 长文母稿。与 content-core 一起用，再只加载本技能。内容写手和公众号编辑不写母稿，不加载本技能。X 配图仍由内容视觉按 content-visual。运营五条另见 content-x-ops，可与写长文分线程，一次只做一类。

## 第一步

任务是写 X、X Article、X 长文或 X 短帖时，由 X 运营加载。加载顺序只有：`skills/content-core/SKILL.md` →（要出封面或配图才加载 `skills/canvas-design/SKILL.md`）→ 本技能。禁止在这一轮、这一写作上下文里 Skill load `content-xhs` 或 `content-wechat`。内容写手和公众号编辑不进入这一轮。

必须先加载 `skills/content-core/SKILL.md`。未加载 core，不得写，不得交卡。

出封面或配图之前，再加载并遵守 `skills/canvas-design/SKILL.md`。未加载不得出图。本技能只补 5:2、中文字体和安全区，不另写审美，也不另写一套正文骨架。

X 样例只按本技能写。不用小红书或公众号稿改写成 X 样例。X 样例同样禁止加载 content-xhs 或 content-wechat。

整周多渠道发布包，或他明确要三版交齐：那不是上面这条只要 X 的加载。X 这一版仍只加载 content-core 和本技能，不加载 content-xhs 或 content-wechat。小红书由内容写手加载 content-xhs。公众号由公众号编辑按 content-wechat 从本岗的 X 母稿转换。本技能仍只负责 X 版式。

出图规则在 `skills/content-visual/SKILL.md`（内容视觉）。出图前仍先加载 canvas-design。运营骨架在 `skills/content-x-ops/SKILL.md`（也是 X 运营；写长文和跑运营可以分线程，一次只做一类）。这两处都不是 content-xhs，也不是 content-wechat。

## 写法

Jake 2026-10-22 已点选的写法。写 X、X Article、X 长文或 X 短帖时以本节为准。目标是写好文章。平台数据也重要。

content-core 里和本节冲突的旧排版不是硬门槛，不拿来退掉下面这些条。冲突包括：编号清单只放在最小动作、不用编号列表、段长不限、小标题密度不限、收束写成目录或只留一句结论、用「空悬念」删掉标题里的好奇。敏感五类、禁 Journal 原话、不代发、中心思想仍在 content-core。

- 标题：具体 + 勾好奇 + 承诺价值。三者都要有。正文要兑现这个价值。
- 首句钩住读者：从方向卡上的真实开场场景写起。
- 一段最多 2–4 行。
- 每 3–5 段一个小标题。小标题是判断句。不把中心思想、Fact、我们的看法、结论写成小标题，也不用 01、02、03 把全文印成目录。
- 一段一事，口语。叙事用「我」；对读者说话时才用「你」，不对读者讲课。
- 每个论点后面马上跟证据。
- 可嵌本人已发帖当证据，附链接。不编造他没发过的帖。
- 用可核验文件/数据做分析。文件或数据要能核对：链接和日期，或点名的文件。不发明数字。
- 论证靠段落推进，段与段是因为／所以／但是／于是（见 content-core 生成流程第 5 步）。列表只放并列的数据或操作步骤，全文最多一处；不拿列表代替论证，也不在文末附可以照抄的清单。
- 几乎每节加粗关键洞察。
- 结尾给 takeaway + 一两句收束。不要目录式总结。
- 写手交稿前轻检查：去填充、大声读。不定死砍 20–30%。

不要：

- 结尾提问求回复
- 结尾求转发/分享
- 标题百分比式钩子

## 参考

下面两处只作写法参考，不覆盖 content-core，也不把这两处仓库拷进本库。

- [news-article-writer](https://github.com/ur-grue/autopunk-media-skills/blob/main/skills/writing/articles/news-article-writer/SKILL.md)：结构可裁切，不发明事实。是否引用 Fact 按 content-core。
- [journalism-core](https://github.com/jamditis/claude-skills-journalism)：用其中的 ai-writing-detox、newsroom-style、fact-check。去 AI 腔，归因，句子要能核验。

## 交卡用的正文

交进发布包的 X 版是中文长文，约 3000 字（只数正文中文字，不含标题、配图说明和出处；2500–3500 都算），不为凑字注水。交卡目标是 X Articles 阅读页：5:2 封面、标题、短钩子、小标题加短段，正文内 1–3 张服务逻辑链的全宽真图，版式仿真实发布界面。白底 PDF、通用文章预览和示意性图位占位都不是交付物；节点测试可以交 Articles 界面 mock，不交微信 PDF，也不交小红书卡片。

短帖可以另附，不能代替这版长文。短帖可以没有配图。

## 怎么写

长文用口语，像真人在讲自己经历过的事：日记式叙事，有文学感；少正式，禁止 formative 腔、论文腔、模板腔、讲课腔和清单腔。标题、首句、段落、小标题、证据、列表、加粗和收束按上一节「写法」。主线和逻辑链按 content-core，这里不复述。行文的 anti-AI-slop 和 deeper thought 按 content-core「foundation 硬规则」。骨架是否使用，按 content-core，且不压过「写法」。

不发明事实，不把模型补的判断写成他的口气。证据按「写法」：论点后面马上跟上，可以是可核验文件或数据，也可以是他已经发出的帖。

主线、交卡逻辑链和可选骨架都在 content-core，这里不复述，也不印成目录。去 AI 腔：不写空泛起势，不堆「不仅…更…」，不把结论写成口号。收束按「写法」：takeaway 加一两句，不要目录式总结，也不提问求回复，也不求转发或分享。

## 配图

长文默认 1–3 张全宽正文图，插进 Articles 正文。每张图服务 content-core 逻辑链上的一步，不用来装饰，也不用示意性图位占位。

短帖可以不配图。

不要求小红书式多图卡片，也不按卡片页码排 X。

图从哪来、何时在文内标明「配图/示意」，只按 content-core 的图源。换图 revision 加一，见 content-core。

canvas-design 没有 5:2，也没有中文字体。本仓库不附带 `canvas-fonts/`。需要拉丁展示字体时按 `skills/canvas-design/SOURCE.md` 的同一 SHA 另取，不拿来排中文。

- 画幅：交付的封面和全宽正文图是 5:2。生成前先定画幅。工具没有 5:2 时，可以先出 16:9，再裁成 5:2。五层 prompt、安全区和其余出图条见 `skills/content-visual/SKILL.md`。
- 中文：Noto Sans CJK、Source Han Sans，或系统里已有的 CJK。
- 安全区：字和图离开四边；标题放在画面中部，不靠会被裁掉的两端。
- 协调：画面、背景、字体是同一套；背景不必是蓝。三者不协调就重做。

交图前勾选：

- [ ] 已加载 canvas-design。交付画幅是 5:2；无 5:2 时先 16:9 再裁，裁切按 content-visual 留出标题安全区
- [ ] 中文用 Noto Sans CJK、Source Han 或系统 CJK，没有缺字
- [ ] 文字在安全区内
- [ ] 画面、背景、字体协调，背景不必是蓝

## 放进哪一栏

本版写入同一张发布包的 X 段（`channels.x.body`）。

本轮只要 X：只交 X。小红书版或公众号版未写，不得因此拦住这张卡，也不得为了补那两版去加载 `content-xhs` 或 `content-wechat`。

整周多渠道包或明确三版交齐：小红书版和公众号版未齐，不得交卡。
