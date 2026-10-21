# Setup / Goals

只给 Jake。V2.0 闭环是：平时收集 → 周四整理（process）→ 周四汇总（digest r{n}）→ 周五周记 → Ideas / 认知 / 内容。

当周 `intake.md` 不再追加，也不是讨论入口。

## 闭环

```
平时收集
  → GitHub Actions daily-intake，07:30 Asia/Hong_Kong，只收集 YouTube-Likes
  → 写入 📥 Inbox/YouTube-Likes/，不写日摘要
  → Snipd / WeRead 仍由本机插件落到 iCloud vault
  → 开机/登录后 com.jake.intake-source-push 只推 📥 Inbox/Snipd/ 与 Inbox/WeRead 上 main
  → 电脑关着时这两路不会自己上 GitHub

周四整理（process）
  → 周四 08:00 Asia/Hong_Kong，process_batch.py
  → 写入 📋 Digests/cycles/{cycle_id}/batch.json
  → cycle_id 是当天 cy-YYYYMMDD（必须是周四）
  → 索引目录不在，或 inputs.jsonl 缺失/为空：跳过，不编批次

周四汇总（digest r{n}）
  → 周四 20:00 Asia/Hong_Kong，build_digest_v2.py
  → 写入 📋 Digests/cycles/{cycle_id}/r{n}.md
  → 同一 cycle 里 n 递增；已有修订的字节不改
  → 索引未建时同样跳过，不编快照
  → 直接 push obsidian-digitalbrain main（不经过 PR）

周五周记
  → Jake 说「写周记」「周记」或 /journal。没有周五定时任务
  → 后台先读最近 2–3 篇旧周记。旧周记里的状态不能当作本周事实
  → 第一段列出这份周四快照的全部 D- 条目，含待归类。一行一条
  → 不把整份汇总贴进周记。没有这份快照就说还没有，不改开别的路径
  → 客户说「可以写 / 写吧 / OK 写」之前不落盘
  → 持久写入只走 skills/journal/tools/write_journal.py
  → 本周快照实际打开时：save / retry --digest-snapshot <digest_id>@r<n>
  → 没有快照时不带这个参数
  → 📝 Journal/ 周记正文不自动 git push
  → 落盘后如有可复用判断，交给 cognition propose；周记自己不写 Cognition

Ideas / 认知 / 内容
  → 「看本周汇总」或 /digest：读最新周四快照。Jake 接受之前不写来源卡以外的东西；接受之后写 📖 Resources/ concept 页。不写 Journal / Cognition
  → 「提炼想法」走 ideas 入口。仓库尚无 ideas/SKILL.md，规则源在 information-flow
  → 「相关认知」走 cognition retrieve。partial / unavailable 不许说成没有相关认知
  → 「记成事实」走 facts 入口。仓库尚无 facts/SKILL.md，规则源在 information-flow 的 skills/facts/
  → 来源卡、认知、事实都不是周记正文

随手记
  → 触发只有「记一下：」「想法：」/thought。普通聊天不记
  → 原话原样写入 📝 Journal/想法/{YYYY}-W{nn}/thought-YYYYMMDD-HHmm[-n].md
  → 新文件。不改、不删旧文件。同一个 id 不写第二次
  → capture_thought.py publish 只把这一个新路径做成只新增的提交并推到 main。修改、删除、重命名不推，不强推
  → 本地 main 只是落后、且没有已跟踪文件的修改时，先 fast-forward，并且不覆盖被忽略的本地文件。远端也前进时，已有的只新增想法或消化清单提交会重放到 origin/main 再一起推；修改、删除或路径已在 origin 上则拒绝，不强推
  → 失败要告诉 Jake「没存上」，说明原因，并把他的原话原样念回去
  → 周记正文仍不自动 push
  → write_journal.py 成功之后才写消化清单。每条是「展开」或「看过未展开」，并链到那篇周记
  → 清单也是新文件，按同一条规则推送。周记文件还没提交时，不要把周记和清单打进同一个提交
  → 未消化 = 全部想法文件减去任何清单里的 id。看过未展开不再捞
  → 不写 Cognition，不进 Ideas / Experiments
```

手机 = Cursor Cloud + GitHub `obsidian-digitalbrain` 的 `main`。周四快照必须已经在 `main`。没有 `📋 Digests/cycles/{cycle_id}/r{n}.md` 就停，不要改去日摘要或旧周路径。

Daily Briefing / Weekly Synthesis / Journal Briefs 不再作为输出。不硬凑空段。不自动 git push 周记。聊天里的 agent 不跑 YouTube / process / digest 脚本，也不把 token 写进 vault。

## 现在（V2.0）

| 块 | 状态 |
|---|---|
| Plugin | `information-flow` private GitHub |
| 规则源 | `information-flow/skills/{journal,intake,digest,cognition}`。ideas / facts 尚无 SKILL.md，规则仍在本仓库 |
| 仓库 skill（手机 Cloud） | DigitalBrain `.cursor/skills/{intake,digest,journal,cognition}/`，由 Actions 覆盖 |
| AGENTS 硬路由 | DigitalBrain `AGENTS.md` 里 `information-flow:digest-route` 段，由 Actions 覆盖 |
| 主文件 | 周四快照 `📋 Digests/cycles/{cycle_id}/r{n}.md`。周记在有快照时由工具写入 `digest_id` / `snapshot_revision` / `input_ids_sha256`。`📋 Digests/daily/` 与旧的 `📋 Digests/{YYYY-Wnn}/digest.md` 不是主文件 |
| Actions | daily-intake 只收集 YouTube-Likes（07:30 Asia/Hong_Kong）。周四 08:00 process、20:00 digest 写 `📋 Digests/cycles/`。skill 变更另走 sync-digitalbrain-skills |
| 本机 source push | `com.jake.intake-source-push`：登录 + 每 4 小时，只推 `📥 Inbox/Snipd/` 与 `Inbox/WeRead` |
| Obsidian Git | `disablePush: true`，不整仓 push |
| 日摘要文件 | 历史留盘，不是主流程，不再生成 |
| 公开 journal-skill | 已 private |

information-flow 改 skill 后，合进 main 就会覆盖 DigitalBrain 副本；已写成的笔记不重写。
