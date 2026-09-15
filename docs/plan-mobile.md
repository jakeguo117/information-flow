# 手机验收：DigitalBrain 有两份，电脑关了也能写周记

保存位置（重启后接着看这份）：
- 本会话：`~/.grok/sessions/%2FUsers%2Fjake/01a095a5-1181-74a3-a69e-bf20480309be/plan.md`
- 项目副本：`~/plugins/information-flow/docs/plan-mobile.md`

还没执行：没拷 `~/.cursor/skills/`，没删公开 journal-skill。重启后说「按 plan-mobile 继续」即可。


不是「必须用 iCloud 这个服务」。是 vault 在这台 Mac 上的位置正好是 Obsidian 的 iCloud 文件夹：

`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain`

Obsidian、launchd、本机 Cursor 都写这里。同时它又是 git 仓库，远程是 GitHub `obsidian-digitalbrain`。所以有两份：

| 份 | 谁在看 | 电脑关了还有吗 |
|---|---|---|
| 本机文件夹（你平时打开的 DigitalBrain） | Mac Obsidian、21:00 intake | 没有。Mac 睡着，Remote Control 动不了它 |
| GitHub 上那份 | Cursor 云 Agent、手机 Obsidian Git pull | **有。** 电脑关着也能写周记 |

之前说 iCloud，指的是本机这一份，容易误解。下面改口叫 **本机 DigitalBrain** vs **GitHub DigitalBrain**。

## 电脑关了行不行

**写周记：行。** 手机 Cursor 选仓库 `obsidian-digitalbrain` → Cloud → `写周记`。Agent 在云 VM 里改 git 里的 `📝 Journal/`，开 PR 或 push。你手机 Obsidian 再 Git pull。不经过开机的 Mac。

**看「今天刚生成、还没 git 的 Digest」：不行。** 那份只在本机。电脑关了，云端只有已经 push 的（现在 W37 已在 main）。

**跑 YouTube/Whisper/当天 intake：不行。** 那些脚本要本机路径和 token。电脑关了就靠前一天 21:00 已经写下并（若已备份）push 的文件。

日常：电脑开着时用 Remote Control，本机 Digests 是活的。出门电脑合上就走 Cloud + GitHub 写周记。

## 电脑先做

**不是把整个 plugin 复制进 DigitalBrain 仓库。** DigitalBrain 只放笔记。YouTube 脚本、Whisper 模型、token 都留在 `~/plugins/information-flow`，不进 vault。

Cursor 云端要能用 journal/intake，只拷那两份 **SKILL.md**（说明怎么聊、怎么写），有两条路：

| 路 | 放哪 | 云端怎么拿到 |
|---|---|---|
| **A. 私人 skill（推荐）** | `~/.cursor/skills/journal` 和 `intake` | 你打开 **Sync Skills for Cloud Agents**。不进 DigitalBrain git |
| B. 仓库 skill | DigitalBrain 里 `.cursor/skills/` | clone 仓库就带上。vault 多两个说明文件，没有脚本 |

已选定 **A**：先走私人 skill（`~/.cursor/skills/` + Sync）。不把 plugin 塞进 DigitalBrain。plugin 本体仍是 private 仓 `information-flow`。

然后再：删公开 `jakeguo117/journal-skill`。

## 手机

Cursor App（不是 Grok Bot）。**选 DigitalBrain 仓库 ≠ 自动装上 information-flow。** 云端默认只看到仓库里的 markdown。要用 journal / intake，必须先做上面「电脑先做」第 1–2 步：skill 进 `~/.cursor/skills/` 并打开 Sync。之后手机才能 `/journal`、`/intake`，或说「写周记」「今天 Digest」。

- Mac 开着：电脑 `/remote-control` → 手机 inbox 接着聊（本机 Digests + 本机写 Journal）
- Mac 关着：选仓库 `obsidian-digitalbrain` → Cloud → `/journal` 或 `写周记`（只改 GitHub 那份 DigitalBrain）

用的就是 **information-flow** 里那两个 skill（journal、intake），不是 4 月公开的 journal-skill，也不是 Cursor 商店里另一个插件。

## 我做

拷 skill、删公开仓、改 setup、盯 GitHub/本机 Journal。Sync 开关你自己点。

## 不做

- 不把 token 放进云
- 这次不自动每天 push Digest
- 不测 Grok Bot
