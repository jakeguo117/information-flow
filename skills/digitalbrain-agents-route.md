<!-- information-flow:digest-route:start -->
## 今天 Digest / 周记（硬路由）

规则源在 `information-flow`。DigitalBrain 这份是同步副本。改行为去那边，不要只改 vault。

用户说「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」或 `/intake`：

1. **自己认周。不要问他是哪一周。** 用 Asia/Shanghai 当天算 ISO 周，打开 `📋 Digests/{YYYY-Wnn}/intake.md`。本周没有就用已有的最近一周。一个都没有：停，说明 GitHub `main` 还没有入口。不要自己编一份。
2. 先读最近 2–3 篇 `📝 Journal/`，以及旧周记里已经挂上的 `🚀 Projects/` / Resource 小线。intake 先不上场。
3. 没有画像就先问一句这周人在哪。不要甩本周清单，不要出文。
4. 再打开 **刚解析出的那一周** `intake.md`，只挑一条和旧线 / 画像呼应的未勾选来问（Yale 式，一次一问）。
5. 对不上的略过。禁止整周附录。禁止没讨论就出文。
6. Jake 说记下之后：只暂存该条 `intake.md` 勾选/reflection，以及有引用时的 `📖 Resources/concepts/` 卡片。精确路径 commit，**push origin main**。禁止 `git add -A`。禁止为 Digest 开 PR。
7. **客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`。** 周记不自动 push。

用户说「写周记」「周记」或 `/journal`：

- 自己认周，先用旧周记和已经挂上的老项目找呼应，再对已勾选 intake。
- 客户说 OK 之前不落盘周记。不自动 push 周记。

详见 `.cursor/skills/intake/SKILL.md` 与 `.cursor/skills/journal/SKILL.md`。云端不要跑 YouTube / Digest 脚本，也不要把 token 写进 vault。

用户说「相关认知」「看看之前相关认知」「我们之前有没有相关判断？」「记成 belief / principle / evidence」，或要做有后果的项目 / 策略决定：

1. 先用 `.cursor/skills/cognition/` 做 retrieve。结果只有 found / no_match / partial / unavailable。partial / unavailable 不许说成「没有相关认知」。
2. 不要每句闲聊都检索。小事、改字、低后果操作不走 Cognition。
3. 写 Cognition 只用 cognition tools；Journal / intake 不直接落盘。没 Accept、没有对应该变更的授权之前不写。
4. 详见 `.cursor/skills/cognition/SKILL.md`。私人 Cognition 只留在 DigitalBrain，不写进 information-flow。
<!-- information-flow:digest-route:end -->
