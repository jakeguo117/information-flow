---
name: intake
description: 只做收集，不讨论。Input 是一次收藏、划线、snip 或随手记。字段见 references/inbox-schema.md。用户说「看本周汇总」「本周 digest」或 /digest 时改用 digest skill（归档里的周四快照；周四自动跑已停），不要用本技能讨论，也不要跑周六提炼。
---

# intake

只做收集，不讨论。

Input 是一条输入记录：一次收藏、划线、snip 或随手记。字段以本技能旁的 `references/inbox-schema.md` 为准。仓库里是 `skills/intake/references/inbox-schema.md`，DigitalBrain 副本是 `.cursor/skills/intake/references/inbox-schema.md`。

Inbox 原文不改。机器索引在 `📥 Inbox/_index/`，一行一条，只追加。每条 Input 有 `process_state`（`pending`、`processing`、`completed`、`failed`、`retry_pending`）。收集阶段不填 `topics`，也不填摘要（`summary_ref`）。

用户说「看本周汇总」「本周 digest」或 `/digest`：用 digest skill。周四 `weekly-digest.yml` schedule 已停；有归档才读 `📋 Digests/cycles/{cycle_id}/r{n}.md`，不要生成新 cycle。每周 Resources／Ideas／Cognition 提炼是周六 `discuss-to-resources-ideas`，扫 `📋 Digests/cluster/` 与已落盘 Journal，不在收集当下跑。不要用本技能讨论。不接管 `📋 Digests/daily/`。

当周 `📋 Digests/{YYYY-Wnn}/intake.md` 历史停用：不再追加，也不再作为讨论入口。

不改 `📝 Journal/`。不写 `📖 Cognition/`。不写来源卡。

入库 / Intake 记录不是 Evidence，不自动成为 Evidence。
