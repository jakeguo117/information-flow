---
name: content-xhs
description: "内容写手只写小红书。必须先加载 content-core。出图前加载 canvas-design。不写 X 长文，不写公众号，不加载 content-x 或 content-wechat。短 caption 加 3:4 纸纹衬线页码卡片。文案是同一条逻辑链的压缩版。不代发。"
---

# content-xhs

写小红书。这里只写卡片和短文案。敏感、逻辑链、禁 Journal 原话、图源、一次交齐、不代发，都在 content-core。

谁加载：内容写手。只小红书。先 content-core，再本技能。不写 X 长文，不写公众号，不加载 content-x 或 content-wechat。

只写 X、X Article、X 长文或 X 短帖的那一轮不加载本技能。

## 第一步

必须先加载 `skills/content-core/SKILL.md`。未加载 core，不得写，不得交卡。

出封面或卡片之前，再加载并遵守 `skills/canvas-design/SKILL.md`。未加载不得出图。本技能只补 3:4、中文字体和安全区。

小红书样例只按本技能写。不用 X 或公众号稿改写成小红书样例。

visual aid / explanation 按 content-core「foundation 硬规则」：必须有解释性配图，禁止只交纯字卡。选题和标题里的具体要求见 content-core。分页沿 content-core 的主线。

## 参考

按短内容、卡片编辑来写。不另引外部仓库。逻辑链的定义见 content-core；caption 做同一条逻辑链的压缩版。分页按 content-core 的主线。

## 文案

`caption` 是一句到一段短文案，压缩 content-core 的同一条逻辑链，只是更短。不在这里重写链上有哪些行，也不把那些词写成页标题。

卡片文案按 content-core 的主线分页，不是另写浅白口号，也不是看图写话。

禁止把卡片写成标签堆砌或小学生说明文。深度底线见 content-core。

## 卡片

交实际卡片图，不只写配图说明。

- 纸纹底
- 衬线字
- 有信息量的小标题
- 页码 `n/N`
- 封面可以用竖排标题

背景、颜色、字体可以变，封面也可以变。纸纹、衬线、页码保持。

一页只走 content-core 主线上的一步，或把一步里的一个数据拆开。页与页是因果或时间，不是定义 1/2/3。不为了凑页数加空页，也不把一句口号铺成多页。

小红书靠图。张数等于卡片页数。图源、无真人、标明「配图/示意」、不用付费图工具，见 content-core。换图 revision 加一。

canvas-design 没有 3:4，也没有中文字体。本仓库不附带 `canvas-fonts/`。

- 画幅：卡片用 3:4。
- 中文：Noto Sans CJK、Source Han，或系统里已有的 CJK。要衬线时优先 Source Han Serif 或 Noto Serif CJK。不要缺字。
- 安全区：封面第一行和页码避开上下边缘；正文不贴左右边。字号以远看仍可读为准。
- 协调：画面、背景、字体是同一套；背景不必是蓝。纸纹、衬线、页码保持。三者不协调就重做。

交图前勾选：

- [ ] 已加载 canvas-design，画幅是 3:4
- [ ] 中文用 Noto Sans CJK、Source Han 或系统 CJK，没有缺字
- [ ] 封面第一行和页码在安全区内
- [ ] 画面、背景、字体协调，背景不必是蓝

## 放进哪一栏

本版写入同一张发布包的小红书段：`caption`，以及按页序的 `cards`（每项含页码 n/N）。卡片图和发布包放在同一个 Drive 文件夹，卡上附链接。

整周包或三版交齐时：三张卡（一渠道一张）同一批交统一出口；X 版或公众号版未齐，这一批先不交。
