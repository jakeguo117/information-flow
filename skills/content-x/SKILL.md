---
name: content-x
description: "写 X。必须先加载 content-core。出图前加载 canvas-design。中文长文 800–1500 字，口语，交 X Articles 阅读页：5:2 封面，正文 1–3 张全宽真图。短帖可以不配图。不代发。"
---

# content-x

写 X。这里只写平台版式和写法。敏感、逻辑链、禁 Journal 原话、图源、一次交齐、不代发，都在 content-core，不在这里复述。

## 第一步

必须先加载 `skills/content-core/SKILL.md`。未加载 core，不得写，不得交卡。

出封面或配图之前，再加载并遵守 `skills/canvas-design/SKILL.md`。未加载不得出图。本技能只补 5:2、中文字体和安全区，不另写审美，也不另写一套正文骨架。

X 样例只按本技能写。不用小红书或公众号稿改写成 X 样例。

## 参考

下面两处只作写法参考，不覆盖 content-core，也不把这两处仓库拷进本库。

- [news-article-writer](https://github.com/ur-grue/autopunk-media-skills/blob/main/skills/writing/articles/news-article-writer/SKILL.md)：结构可裁切，不发明事实。是否引用 Fact 按 content-core。
- [journalism-core](https://github.com/jamditis/claude-skills-journalism)：用其中的 ai-writing-detox、newsroom-style、fact-check。去 AI 腔，归因，句子要能核验。

## 交卡用的正文

交进发布包的 X 版是中文长文，800–1500 字。交卡目标是 X Articles 阅读页：5:2 封面、标题、短钩子、可扫读短节（Heading 与短段），正文内 1–3 张服务逻辑链的全宽真图，版式仿真实发布界面。白底 PDF、通用文章预览和示意性图位占位都不是交付物；节点测试可以交 Articles 界面 mock，不交微信 PDF，也不交小红书卡片。

短帖可以另附，不能代替这版长文。短帖可以没有配图。

## 怎么写

长文用口语，像真人在说话：少正式，禁止 formative 腔、论文腔和模板腔。主线和逻辑链按 content-core，这里不复述。行文的 anti-AI-slop 和 deeper thought 按 content-core「foundation 硬规则」。入口可以是痛点或结果预告，接着给可带走的物。骨架是否使用，按 content-core。

事实怎么引用、开头怎么起，按 content-core。每个用到的事实有来源链接和日期。不发明事实，不把模型补的判断写成他的口气。

小标题要能裁切：只读某一节，也能看出这一步在论证什么。小标题用判断句。不要把中心思想、Fact、我们的看法、结论写成标题，也不要写成 01、02、03。

主线、交卡逻辑链和可选骨架都在 content-core，这里不复述，也不印成目录。

去 AI 腔：不写空泛起势，不堆「不仅…更…」，不把结论写成口号。收束用 content-core 要求的结论句。

## 配图

长文默认 1–3 张全宽正文图，插进 Articles 正文。每张图服务 content-core 逻辑链上的一步，不用来装饰，也不用示意性图位占位。

短帖可以不配图。

不要求小红书式多图卡片，也不按卡片页码排 X。

图从哪来、何时在文内标明「配图/示意」，只按 content-core 的图源。换图 revision 加一，见 content-core。

canvas-design 没有 5:2，也没有中文字体。本仓库不附带 `canvas-fonts/`。需要拉丁展示字体时按 `skills/canvas-design/SOURCE.md` 的同一 SHA 另取，不拿来排中文。

- 画幅：封面和全宽正文图用 5:2。
- 中文：Noto Sans CJK、Source Han Sans，或系统里已有的 CJK。
- 安全区：字和图离开四边；标题放在画面中部，不靠会被裁掉的两端。
- 协调：画面、背景、字体是同一套；背景不必是蓝。三者不协调就重做。

交图前勾选：

- [ ] 已加载 canvas-design，画幅是 5:2
- [ ] 中文用 Noto Sans CJK、Source Han 或系统 CJK，没有缺字
- [ ] 文字在安全区内
- [ ] 画面、背景、字体协调，背景不必是蓝

## 放进哪一栏

本版写入同一张发布包的 X 段（`channels.x.body`）。小红书版和公众号版未齐，不得交卡。
