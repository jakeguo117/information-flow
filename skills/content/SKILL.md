---
name: content
description: "已停用。做内容、选题、写帖、发布包或 /content 时，先加载 content-core；出图前加载 canvas-design。任务只要写 X、X Article、X 长文或 X 短帖时，由内容写手再加载 content-x 写 basement，禁止同轮 Skill load content-xhs 或 content-wechat。①②③走 content-x-process-topic、content-x-article-packaging、content-x-cta-loop。写手不写小红书。公众号由公众号编辑加载 content-wechat，从 X 定稿转换。发帖、引用再分发、沉睡号复活走 content-x-ops。配图由内容视觉按渠道裁。本技能不再生产正文。"
---

# content（已停用）

不要用本技能写帖。旧的「一个 content 技能出三版」已废止。

任务只要写 X、X Article、X 长文或 X 短帖：由内容写手加载，写 X 长文 basement。加载顺序是 content-core →（出图才）canvas-design → content-x。禁止同一写作上下文 Skill load content-xhs 或 content-wechat。只交 X。一次交齐三版不适用于这种任务。公众号编辑不写这一轮。①②③见 content-x-process-topic、content-x-article-packaging、content-x-cta-loop。

整周多渠道发布包，或他明确要三版交齐：同 topic 一次交齐 X、小红书、公众号三张审批卡。X 版由内容写手先过骨架闸门再写。写手不写小红书。公众号由公众号编辑从 X 定稿转换，加载 content-wechat。没有 X 定稿，不写另外两版。缺任一版不得交审批卡。发帖走 content-x-ops。

1. 先加载 `skills/content-core/SKILL.md`
2. 出封面、配图或卡片之前，加载并遵守 `skills/canvas-design/SKILL.md`。三渠道图由内容视觉按 content-visual 按渠道裁。
3. 只要 X：内容写手加载 `skills/content-x/SKILL.md` 写 basement。①②③另见 content-x-process-topic、content-x-article-packaging、content-x-cta-loop。到此停止，不加载下面两步。
4. 小红书：写手不写小红书正文。版式在 `skills/content-xhs/SKILL.md`。
5. 公众号：公众号编辑加载 `skills/content-wechat/SKILL.md`（从 X 定稿转换，或整周包 / 三版交齐里的公众号）

发帖、引用再分发、沉睡号复活由 X 运营加载 content-x-ops。写长文和跑运营可以分线程，一次只做一类。采访加载 `skills/interview/SKILL.md`。成稿编辑加载 `skills/editor/SKILL.md`（其中必加载 humanizer-zh）。编辑审稿仍是编辑（非作者），不写死 bot。

canvas-design 不是第四个内容主技能。平台技能只补画幅和中文回退。

「周记原话直接引用」已废止。敏感、逻辑链、图源、不代发和发布包路径见 content-core。

字段、指纹和批准形状仍见 `references/content-record.md`（`content-0.1`）。自检清单以 content-core 为准。只要 X 时，不按「三版都要有」去加载 content-xhs 或 content-wechat。
