---
name: content-x
description: "写 X。必须先加载 content-core。中文长文 800–1500 字，口语，交 X Articles 阅读页：5:2 封面，正文 1–3 张全宽真图。短帖可以不配图。不代发。"
---

# content-x

写 X。这里只写平台版式和写法。敏感、逻辑链、禁 Journal 原话、图源、一次交齐、不代发，都在 content-core，不在这里复述。

## 第一步

必须先加载 `skills/content-core/SKILL.md`。未加载 core，不得写，不得交卡。

X 样例只按本技能写。不用小红书或公众号稿改写成 X 样例。

## 参考

下面两处只作写法指引，不把外部仓库拷进本库。

- [news-article-writer](https://github.com/ur-grue/autopunk-media-skills/blob/main/skills/writing/articles/news-article-writer/SKILL.md)：事实优先，结构可裁切，不发明事实。
- [journalism-core](https://github.com/jamditis/claude-skills-journalism)：用其中的 ai-writing-detox、newsroom-style、fact-check。去 AI 腔，归因，句子要能核验。

## 交卡用的正文

交进发布包的 X 版是中文长文，800–1500 字。交卡目标是 X Articles 阅读页：5:2 封面、标题、短钩子、可扫读短节（Heading 与短段），正文内 1–3 张服务逻辑链的全宽真图，版式仿真实发布界面。白底 PDF、通用文章预览和示意性图位占位都不是交付物；节点测试可以交 Articles 界面 mock，不交微信 PDF，也不交小红书卡片。

短帖可以另附，不能代替这版长文。短帖可以没有配图。

## 怎么写

长文用口语，像真人在说话：少正式，禁止 formative 腔、论文腔和模板腔。逻辑链仍按 content-core，这里不复述。

事实放在前面。每个事实有来源链接和日期，规则见 content-core。不发明事实，不把模型补的判断写成他的口气。

小标题要能裁切：只读某一节，也能看出这一步在论证什么。

段落顺序就是 content-core 的逻辑链：Fact，推论（写出假设），机制，结论。一段只走一步。

去 AI 腔：不写空泛起势，不堆「不仅…更…」，不把结论写成口号。收束用 content-core 要求的结论句。

## 配图

长文默认 1–3 张全宽正文图，插进 Articles 正文。每张图服务逻辑链上的一步（这一步的数据、推论或机制），不用来装饰，也不用示意性图位占位。

短帖可以不配图。

不要求小红书式多图卡片，也不按卡片页码排 X。

图从哪来、何时在文内标明「配图/示意」，只按 content-core 的图源。换图 revision 加一，见 content-core。

## 放进哪一栏

本版写入同一张发布包的 X 段（`channels.x.body`）。小红书版和公众号版未齐，不得交卡。
