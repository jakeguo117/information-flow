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

## 现在（2026-09-15）

| 块 | 实际状态 |
|---|---|
| Plugin | `~/plugins/information-flow` → private GitHub `information-flow` |
| Cursor 私人 skill | `~/.cursor/skills/{journal,intake}`（云端要你打开 Sync Skills for Cloud Agents） |
| intake | launchd 21:00 跑 `run_digest_jobs.sh` |
| journal | 电脑已跑通 2026-09-13；Cursor 手机待真机 |
| 公开 journal-skill | 删除 |

手机入口是 **Cursor App**，不是 Grok Bot。Mac 开着用 Remote Control；Mac 关着用 Cloud + GitHub DigitalBrain。

## 完成

1. 电脑能写周记 — 已验收（2026-09-13）
2. intake 每天 Digest + Journal Brief — 本机已接
3. 手机 — Cursor skill 已接上，真机未试
