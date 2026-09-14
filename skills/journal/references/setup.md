# Setup / Goals

只给 Jake。信息流每天进，周末写成周记。

## 最终闭环

```
每天 21:00  intake
  Snipd / WeRead / YouTube 点赞
        ↓
  📋 Digests/{日期}-Digest.md
  📊 Journal Briefs/{YYYY}-W{nn}.md

写周记  journal skill
  读：旧周记 + 本周 Digest + Journal Brief
  聊：先把这周的事说完；说完后再对划线/点赞
  确认 → 📝 Journal/{日期} {中文标题}.md
```

不代写。不把 Digest 原文糊进周记。不自动 git push vault。Follow Builders 不做。Daily Briefing / Weekly Synthesis 不在这个 plugin 里。

## 现在（2026-09-14）

| 块 | 实际状态 |
|---|---|
| Plugin | `~/plugins/information-flow` → private GitHub `information-flow` |
| intake | launchd 21:00 跑 `run_digest_jobs.sh` |
| journal | Grok skill；2026-09-13 已跑通一场 |
| 手机 | 文档已探，真机未试。消费级 Grok App 不能写 vault；候选 Grok Bot iPhone + Local Computer |

## 完成

1. 电脑能写周记 — 已验收（2026-09-13）
2. intake 每天 Digest + Journal Brief — 本机已接
3. 手机 — 未真机验收
