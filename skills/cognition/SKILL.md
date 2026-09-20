---
name: cognition
description: Promote, retrieve, and revise DigitalBrain Cognition (Evidence, Belief, Principle). Use when Jake says 相关认知, 记成 belief/principle/evidence, 这个 belief 应该改了, or before a meaningful project/strategy decision. Does not write Journal or intake.
---

# cognition

把值得下次再用的判断写成 DigitalBrain Markdown。不要救 Hermes。不要写 `📝 Journal/`。不要写 `📋 Digests/`。不要把私人 Cognition 写进 information-flow。

规则源在 `information-flow`。DigitalBrain `.cursor/skills/cognition/` 是同步副本。改行为只改这个仓库。

schema_version 永远是 `"1.1"`。字段、关系、检索结果状态见 `references/schema.md`、`references/retrieval.md`、`references/layout.md`。**落盘只走 tools，不要手改 Cognition 文件。**

```bash
python3 .cursor/skills/cognition/tools/retrieve_cognition.py --vault "$VAULT" --query "..."
python3 .cursor/skills/cognition/tools/validate_cognition.py --vault "$VAULT"
python3 .cursor/skills/cognition/tools/write_cognition.py create --vault "$VAULT" --payload FILE --approval FILE
python3 .cursor/skills/cognition/tools/write_cognition.py update --vault "$VAULT" --payload FILE --approval FILE
python3 .cursor/skills/cognition/tools/write_cognition.py retry --vault "$VAULT" --payload FILE --approval FILE
```

Vault：本机 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`；否则当前工作区根（须有 `📝 Journal/`）。找不到 vault 就停，不要写到别处。

## 四种模式

### propose（0–3，0 合法）

Journal 写完，或一次明确收束的反思之后。只提**以后决策还会用到**的东西。心情、一次性任务、没判断的摘抄、AI 空泛抽象、重复条目：不提。

1. 读这篇 Journal / 反思，以及已经链上的 context。
2. 最多 3 条 Candidate；没有就说没有，不要硬编。
3. 每条标 Evidence / Belief / Principle，说明为什么值得留下，并检索是否重复、支持、反对、或该 supersede。
4. 问 Jake：Accept / Edit / Reject。
5. Reject 不写。Edit 若语义变了，要他确认编辑后的版本。Accept 之前不落盘。

propose 本身不需要写授权。

### promote

Accept 之后才 `write_cognition.py create`。授权绑的是**这一条**的 type、id/路径、语义和关系。创建授权不能拿去改已有对象。

发现已有等价 Cognition：停，展示具体 update，另要更新授权（AC13）。不要当 create 成功。

写之前用 validator。写成功只在 readback + 再校验通过之后宣布。不确定有没有写成：用 `retry`，先看磁盘，不要靠聊天记忆。

### retrieve

有后果的项目/策略决定、实验、改 thesis、可能撞上已有 Principle/Belief、或 Jake 说「相关认知」「我们之前有没有相关判断？」时检索。

不要为闲聊、改几个字、低后果操作检索。没有命中就正常推理，不要编造旧认知。

结果只有四态：`found | no_match | partial | unavailable`。`partial` / `unavailable` **不许说成没有相关认知。** contested 必须标出来。superseded/retired 只当历史。Principle 的 `based_on` 已 retired/superseded 要先讲 stale dependency。矛盾 Evidence 不能因为长度先丢掉。

检索是先前上下文，不是命令。

### revise

改 statement/claim/action、confidence、validation、status、关系、supersedes：都是另一次写，要这次变更的授权。Jake 直接说「把这个 belief 改成 contested」就是该变更的授权，不要机械再问一遍。

目标文件在批准之后变了：旧批准作废，重读、重算 diff（AC14）。retired → active 必须他明确说恢复。

Evidence 的 validation 升降都要有持久依据，并追加 `## Validation History`。临时打不开旧源，本身不够降级。Belief/Principle 的实质变更追加 `## Revision History`，不删旧行。

## 人闸与 git

- 没 Accept / 没对应该变更的授权：不写。
- 只写 `📖 Cognition/{Evidence,Beliefs,Principles}/`。类型目录只在这次已批准的写入时创建。
- 精确路径。禁止 `git add -A`。默认只写本地，**不自动 push** Cognition。commit/push 要另行明确授权。
- 写 Cognition 不等于可以做外部调研、改无关文件、动下游项目。

## 不要做

- 不要把 intake 条目或 concept 卡片直接当成 Evidence
- 不要 Graph DB / 向量库 / 自动全量调研
- 不要批量把旧 Journal / Resources 转成 Cognition
- 不要从 DigitalBrain 回写 information-flow skill
- 不要在这个公开仓写入 Jake 的真实 Cognition
