<!-- information-flow:digest-route:start -->
## 今天 Digest / 周记（硬路由）

规则源在 `information-flow`。DigitalBrain 这份是同步副本。改行为去那边，不要只改 vault。

用户说「今天 Digest」「今日digest」「讨论 Digest」「今天摄入」「跑 Digest」或 `/digest`：

1. 用 Asia/Shanghai 的昨天，打开 `📋 Digests/daily/YYYY-MM-DD.md`。文件不在 `main` 上就停，说明当天摘要还没有。不要自己编条目，不要改去打开按周累积的旧入口。
2. 从这份摘要提出最多两个概念。一个概念可以挂上多条原文。Jake 接受之前不写 Resource。
3. 接受之后写成 `📖 Resources/` 已有领域目录下的一页。`sources` 指回 Inbox 原文，更新 `index.md` 和 `log.md`，每页至少两个链接。不改类型。
4. 不改 `📝 Journal/`。这条不写 Cognition。Agent 发起的受管文件变更遵循当前 Global Governance / project policy：使用 task branch，精确路径暂存，禁止 `git add -A`，不直接 push protected `main`。PR 与 merge 服从当前授权和治理 gate。

用户说「想法」「听完播客的一些感想」「先记一下」「追加到周记」，或明确收尾这类讨论：

- 使用 `.cursor/skills/journal/SKILL.md` 的素材流程，读取 `📝 Journal/素材/同步约定.md`。有有效持续授权时，将本次素材追加到上海事件日期对应的 `📝 Journal/素材/YYYY-Www.md`，精确提交并同步授权的 main，读回确认；不重复要 push 批准。
- 没有本机 vault 时可核验已获授权的 GitHub DigitalBrain 仓库后经连接读写。相同事件不重复追加；冲突先核对，不强推。私人正文不进入 information-flow。
- 素材不占周记编号；正式周记时先读当周及未整合素材，留待对话找呼应。用户临时说不保存／不推送时，以该指示为准。

用户说「写周记」「周记」或 `/journal`：

- 自己认周，先用旧周记和已经挂上的老项目找呼应，再对已勾选 intake。未勾选即使相关也不进入周记材料。
- 客户说「可以写 / 写吧 / OK 写」之前，不要写正式周记篇章；素材按上面的独立流程。持久写入只走 `.cursor/skills/journal/tools/write_journal.py`。不写 Cognition。正式周记不默认自动 push；想法素材的持续同步授权单独适用。

详见 `.cursor/skills/digest/SKILL.md` 与 `.cursor/skills/journal/SKILL.md`。云端不要跑 YouTube / Digest 脚本，也不要把 token 写进 vault。

用户说「相关认知」「看看之前相关认知」「我们之前有没有相关判断？」「记成 belief / principle / evidence」，或要做有后果的项目 / 策略决定：

1. 先用 `.cursor/skills/cognition/` 做 retrieve。结果只有 found / no_match / partial / unavailable。partial / unavailable 不许说成「没有相关认知」。
2. 不要每句闲聊都检索。小事、改字、低后果操作不走 Cognition。
3. 写 Cognition 只用 cognition tools；Journal / intake 不直接落盘。没 Accept、没有对应该变更的授权之前不写。
4. 详见 `.cursor/skills/cognition/SKILL.md`。私人 Cognition 只留在 DigitalBrain，不写进 information-flow。
<!-- information-flow:digest-route:end -->
