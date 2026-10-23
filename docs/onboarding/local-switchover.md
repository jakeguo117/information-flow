# 本机切换清单

现有 Mac 的插件检出在分支 `cursor/cognition-v1.1`。把它改回合并后的 `main` 之前，先放好显式配置并按第 6 节验证。合之前不要把真实路径、账号、邮箱写进仓库。

本文件只写占位符。`vault_root` 填你已经在用的那一个绝对路径。

## 1. `config.json` 放哪

本机 launchd 会跑到的那份是 **插件检出根上的 `config.json`**。检出就是已安装 plist 里 `ProgramArguments` 指向的 information-flow 工作副本，目录名是 `plugins/information-flow`，里面有 `scripts/push_intake_sources.sh`。

也可以不把文件放在检出根，改设 `INFOFLOW_CONFIG` 为绝对路径。

读取顺序以 `scripts/infoflow_config.py` 的 `require_setting` 和 `resolve_config_path` 为准：

1. 命令行已经给出的**值**。`daily_digest.py`、`weekly_rollup.py`、`youtube_likes.py`、`sync_digitalbrain_skills.py` 的 `--vault` 覆盖 `vault_root`。`infoflow_config.py get` 没有值参数，只有 `--config`。
2. 环境变量（有非空值才用，并且盖过配置文件）：
   - `vault_root` → `INFOFLOW_VAULT_ROOT`
   - `git_remote` → `INFOFLOW_GIT_REMOTE`
   - `git_branch` → `INFOFLOW_GIT_BRANCH`
   - `storage_mode` → `INFOFLOW_STORAGE_MODE`
   - `git_user_name` → `INTAKE_GIT_USER_NAME`
   - `git_user_email` → `INTAKE_GIT_USER_EMAIL`
3. 配置文件。选文件的顺序：
   - 调用时传了 `--config`，用那个路径
   - 否则用 `INFOFLOW_CONFIG`（非空）
   - 否则，若插件检出根（`scripts/` 的上一级，也就是上面的 `plugins/information-flow`）已经有 `config.json`，用它
   - 这一层的文件不存在就跳过，不会新建
4. 还是没有：非 0 退出。没有内置路径。

例子：

```bash
python3 scripts/infoflow_config.py get vault_root --config /ABSOLUTE/PATH/config.json
```

scaffold 写入时的默认文件不同：没传 `--config` 时，有 `INFOFLOW_CONFIG` 就写那里，否则写检出根的 `config.json`（文件可以事先不存在）。scaffold 只写 `vault_root`、`storage_mode`，模式 A 再写 `git_remote` 和 `git_branch`。`git_user_name` 和 `git_user_email` 要自己补上。

仓库根 `.gitignore` 的 `/config.json` 只忽略检出根这一份。填好的文件不要提交。`INFOFLOW_CONFIG` 指到仓外时，那份文件本来就不在这个 git 里。

## 2. 字段

从 `config.example.json` 复制后再改占位符。含 `REPLACE_WITH_` 的值会被拒绝。

```json
{
  "vault_root": "REPLACE_WITH_VAULT_ROOT",
  "storage_mode": "A",
  "git_remote": "REPLACE_WITH_GIT_REMOTE",
  "git_branch": "main",
  "git_user_name": "REPLACE_WITH_GIT_USER_NAME",
  "git_user_email": "REPLACE_WITH_GIT_USER_EMAIL",
  "enabled_sources": []
}
```

| 字段 | 填什么 | 谁会读 |
| --- | --- | --- |
| `vault_root` | 你现有 vault 的绝对路径 | 没传 `--vault`、也没设 `INFOFLOW_VAULT_ROOT` 时，intake / sync / `run_digest_jobs.sh` |
| `storage_mode` | `A`（私有 git vault）或 `B`（本地目录） | scaffold 写入。日常 intake 脚本不读 |
| `git_remote` | 数据仓 remote。占位符 `REPLACE_WITH_GIT_REMOTE` | `push_intake_sources.sh` 在 `INTAKE_SOURCE_REMOTE` 为空时读取；也可用 `INFOFLOW_GIT_REMOTE` |
| `git_branch` | scaffold 模式 A 的分支，示例是 `main` | scaffold。`push_intake_sources.sh` 仍推 `main`，不读这个字段 |
| `git_user_name` | 该数据仓上已经在用的提交名。占位符 `REPLACE_WITH_GIT_USER_NAME` | `push_intake_sources.sh`。`INTAKE_GIT_USER_NAME` 非空时盖过它 |
| `git_user_email` | 对应邮箱。占位符 `REPLACE_WITH_GIT_USER_EMAIL` | `push_intake_sources.sh`。`INTAKE_GIT_USER_EMAIL` 非空时盖过它 |
| `enabled_sources` | 可选数组，示例留空 | 当前脚本不读 |

已安装的 intake plist 只带 `HOME` 和 `PATH` 时，身份靠这两个配置字段。环境变量留空就行。需要临时盖过时再导出 `INTAKE_GIT_USER_NAME` 和 `INTAKE_GIT_USER_EMAIL`。

YouTube 密钥不进 `config.json`。见下一节。

`push_intake_sources.sh` 还有两个可选变量，不设就用脚本里的非个人默认：`INTAKE_SOURCE_WORKTREE`（默认是插件仓下的 `state/digitalbrain-main`）、`INTAKE_SOURCE_ICLOUD_WAIT`（默认 `45`，秒）。

## 3. YouTube 环境变量

| 变量 | 指向 |
| --- | --- |
| `YOUTUBE_CLIENT_FILE` | OAuth client JSON。文件里要有 `installed` 或 `web`，以及 `client_id` / `client_secret` |
| `YOUTUBE_TOKEN_FILE` | token JSON。`youtube_oauth.py` 会把它写出来，里面要有 `refresh_token` |

两个文件都放在 vault 外面，也放在 information-flow 代码仓外面。

交互 shell 可以写进你自己的 shell 启动文件。launchd **不会**读那个文件。要给某个 job 用，写进**那个 job 已安装 plist** 的 `EnvironmentVariables`。intake 的 AppleScript 会把进程上已有的这两个名字转发进 `do shell script`。`com.jake.intake-source-push` 不跑 YouTube，可以不设。仓里没有 `run_digest_jobs.sh` 的 plist；若本机另挂了会跑 `youtube_likes.py` 的 job，那份 plist 要有这两个变量。

`INFOFLOW_VAULT_ROOT` 可以代替 `config.json` 里的 `vault_root`。它不代替 YouTube 的两个文件变量，也不代替 git 身份字段。

只准备 OAuth、还不跑同步时：

```bash
python3 scripts/youtube_oauth.py
```

它读 `YOUTUBE_CLIENT_FILE`，把 token 写到 `YOUTUBE_TOKEN_FILE`。

## 4. launchd

改的是 `~/Library/LaunchAgents/` 里**已安装**的副本。只改仓库里的 plist 不会改正在跑的 job。

| 已安装 label | 仓内文件 | 这次怎么处理 |
| --- | --- | --- |
| `com.jake.intake-source-push` | `launchd/com.jake.intake-source-push.plist` | 要改环境或重载。见下文 |
| `com.jake.digitalbrain-reconcile` | 仓内没有这份 plist | 见第 4.1 节。不要删 |
| `com.jake.journal-daily-digest` | 仓内没有 plist。`docs/plan-weekly-intake.md` 写明保持卸载 | 不要 load |
| `com.jake.digitalbrain-backup` | `ops/digitalbrain-backup/launchd/com.jake.digitalbrain-backup.plist` | 不读 `infoflow_config.py`。这次不要动 |

`com.jake.intake-source-push`：

- 登录时跑，之后每 14400 秒
- `ProgramArguments` 调 `osascript`，脚本是 `scripts/run_intake_source_push.applescript`
- 该 AppleScript 用 `do shell script` 执行 `scripts/push_intake_sources.sh`
- `do shell script` 不继承 launchd 的环境。本分支的 AppleScript 用 `system attribute` 把进程上已有的这些名字抄进命令（空的不抄）：`INTAKE_VAULT`、`INTAKE_SOURCE_REMOTE`、`INTAKE_GIT_USER_NAME`、`INTAKE_GIT_USER_EMAIL`、`INTAKE_SOURCE_WORKTREE`、`INTAKE_SOURCE_ICLOUD_WAIT`、`PLUGIN_ROOT`、`PYTHON3`、`INFOFLOW_CONFIG`、`INFOFLOW_VAULT_ROOT`、`INFOFLOW_GIT_REMOTE`、`INFOFLOW_GIT_BRANCH`、`INFOFLOW_STORAGE_MODE`、`YOUTUBE_CLIENT_FILE`、`YOUTUBE_TOKEN_FILE`

`push_intake_sources.sh` 需要：

- vault：`INTAKE_VAULT`，否则按第 1 节读 `vault_root`
- remote：`INTAKE_SOURCE_REMOTE`，否则按第 1 节读 `git_remote`
- git 身份：按第 1 节读 `git_user_name` / `git_user_email`。`INTAKE_GIT_USER_NAME` 和 `INTAKE_GIT_USER_EMAIL` 非空时盖过配置文件

检出根已经有填好的 `config.json` 时，已安装 plist 可以继续只放 `HOME` 和 `PATH`。身份不必再写进 `EnvironmentVariables`。`HOME` 留着。wrapper 在 `HOME` 为空时仍有硬编码兜底；plist 里继续写上 `HOME`。

`run_digest_jobs.sh` 在仓里没有 plist。它若被另挂，会依次跑：

1. `scripts/youtube_likes.py --vault <vault_root>`，因此还要 `YOUTUBE_CLIENT_FILE` 和 `YOUTUBE_TOKEN_FILE`
2. `scripts/daily_digest.py --vault <vault_root>`
3. `scripts/weekly_rollup.py --vault <vault_root>`

它不需要 git 身份。`youtube_oauth.py` 只手动跑。

plist 改完先检查，再重载，再用 kickstart 跑一次：

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl bootout "gui/$(id -u)/com.jake.intake-source-push"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl kickstart -k "gui/$(id -u)/com.jake.intake-source-push"
launchctl print "gui/$(id -u)/com.jake.intake-source-push"
ERR=$(plutil -extract StandardErrorPath raw "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist")
tail -n 50 "$ERR"
```

仓库模板里的 `StandardErrorPath` 文件名是插件检出下的 `state/intake-source-push.err.log`。kickstart 之后，这次新写进该文件的行里不要有 `error:`。

较旧的 launchctl：对同一个 plist 用 `launchctl unload`，再用 `launchctl load`。

这些命令放在第 6 节的读取和 `push_intake_sources.sh` 已经是 rc=0 之后。kickstart 时，plist 指向的检出必须已经是你正在验证的分支。

### 4.1 从 `cursor/cognition-v1.1` 回到 `main`，以及 reconcile

先在仍停在 `cursor/cognition-v1.1` 的检出上做完本节，再 `git checkout` 离开这个分支。离开之后工作区里就没有 reconcile 脚本了。

查过 `origin/cursor/cognition-v1.1` 和 `origin/main`：

- `scripts/reconcile_live_vault_untracked.py` 只在 `cursor/cognition-v1.1`（提交 `7608291`）。`main` 和本 PR 都没有这个文件。该分支的 `push_intake_sources.sh` 在结束时会调用它。本 PR 的 `push_intake_sources.sh` 不再调用它。
- 该分支上的脚本仍带内置 vault 路径。本 PR 不把那份脚本抄进来。
- 仓库历史里没有单独的 reconcile AppleScript。该分支和 `main` 上都有的 AppleScript 只有 `scripts/run_intake_source_push.applescript`，它只跑 intake push。`main` 的 README 写了 label `com.jake.digitalbrain-reconcile`（登录以及大约每 2 分钟），两支分支的 git 树里都没有这份 plist。
- `cursor/cognition-v1.1` 比 `main` 旧，上面的 Cognition 提交已经被 `main` 上后来的技能取代。不要为了 reconcile 去合并整个 `cursor/cognition-v1.1`。

若本机装过这个 job，它的 plist 和它指向的 AppleScript 只在本机 `~/Library/LaunchAgents/` 或 plist 的 `ProgramArguments` 里。不要删除 plist，不要删除它指向的脚本，不要 `rm` LaunchAgents 里的文件。

还在 `cursor/cognition-v1.1` 上时：

```bash
launchctl print "gui/$(id -u)/com.jake.digitalbrain-reconcile" || true
ls "$HOME/Library/LaunchAgents" | grep -i reconcile || true
```

label 在，或者 LaunchAgents 里有对应 plist：

1. 用 `plutil -extract ProgramArguments xml1 -o -` 看已安装 plist 的参数。把参数里的每一个脚本（Python，以及若有的 AppleScript）复制到插件检出**外面**的目录。
2. 改已安装 plist 的 `ProgramArguments`，让它们指向这些副本。
3. 只重载这个 label，job 继续跑：

```bash
launchctl bootout "gui/$(id -u)/com.jake.digitalbrain-reconcile"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.digitalbrain-reconcile.plist"
launchctl print "gui/$(id -u)/com.jake.digitalbrain-reconcile"
```

plist 文件名以你机器上 `ls` 看到的为准。上面的文件名是 README 里的 label 加上 `.plist`。对不上就用 `ls` 的结果。

若要先停掉、等以后 `main` 上有不带个人默认路径的脚本再开：只执行 `launchctl bootout "gui/$(id -u)/com.jake.digitalbrain-reconcile"`。plist 文件留在 `~/Library/LaunchAgents/`。不要删除。脚本在离开分支前先复制出去，或接受这个 job 保持停止。`main` 上出现脚本之后再 `bootstrap`。

切到本 PR 或合并后的 `main` 之后，每 4 小时的 intake push 不再顺带 reconcile。2 分钟那次若已指向检出外的副本，仍由那份副本负责。

## 5. GitHub Actions

对过 `.github/workflows/` 里这三份文件。它们的命令都带 `--vault digitalbrain`（runner 上 checkout 出来的目录），不读已删除的个人 vault 默认，也不读本机 `config.json`。

| workflow | 和这次默认值的关系 | 要不要改 |
| --- | --- | --- |
| `daily-intake.yml` | 用已有 secrets `YOUTUBE_TOKEN`、`YOUTUBE_CLIENT` 写成 runner 上的文件，再 export `YOUTUBE_TOKEN_FILE`、`YOUTUBE_CLIENT_FILE`，然后 `youtube_likes.py --vault digitalbrain`。接着 `sync_digitalbrain_skills.py --vault digitalbrain`。vault checkout 仍用已有的 `DIGITALBRAIN_TOKEN` | 不用改。合并后不会因为去掉本机默认而失败 |
| `sync-digitalbrain-skills.yml` | `sync_digitalbrain_skills.py --vault digitalbrain`，以及在数据仓目录里 `--vault .`。密钥仍是 `DIGITALBRAIN_TOKEN` | 不用改 |
| `weekly-digest.yml` | `process_batch.py` 和 `build_digest_v2.py` 本来就要求 `--vault digitalbrain`。不读 YouTube 文件变量，也不读 git 身份 | 不用改 |

本 PR 不改这三份 workflow。

## 6. 先配好并验证，再合并，最后才切到 `main`

1. 检出还在 `cursor/cognition-v1.1` 时，先做完第 4.1 节。
2. 记下当前 `main`，回滚要用：

```bash
git fetch origin
git rev-parse origin/main
```

3. 在 plist 指向的那个 `plugins/information-flow` 检出里，先检出**本 PR 分支**（含本文件的 `cursor/empty-vault-onboarding-6aee`）。先不要 `git checkout main`。
4. `cp config.example.json config.json`。把 `vault_root` 换成你现有 vault 的绝对路径，把 `git_remote` 换成数据仓 remote，`storage_mode` 填 `A` 或 `B`，`git_branch` 保持你要用的分支（示例 `main`），`git_user_name` 和 `git_user_email` 换成该数据仓上已经在用的提交身份。每个 `REPLACE_WITH_` 都要换掉。
5. 在这个 shell 里导出 `YOUTUBE_CLIENT_FILE` 和 `YOUTUBE_TOKEN_FILE`，供下面的密钥检查。要验证 launchd 那种「plist 只有 HOME/PATH」的路径，就不要导出 `INTAKE_GIT_USER_NAME` 和 `INTAKE_GIT_USER_EMAIL`。若 `config.json` 不在检出根，再导出 `INFOFLOW_CONFIG`。
6. 验证命令：

```bash
python3 scripts/infoflow_config.py get vault_root
python3 scripts/infoflow_config.py get git_remote
python3 scripts/infoflow_config.py get git_branch
python3 scripts/infoflow_config.py get git_user_name
python3 scripts/infoflow_config.py get git_user_email
test -d "$(python3 scripts/infoflow_config.py get vault_root)"
/bin/sh scripts/push_intake_sources.sh
echo "push_intake_sources rc=$?"
```

`push_intake_sources rc` 必须是 `0`。脚本默认先等 45 秒，然后只在 Snipd / WeRead 有差异时提交并 push 这两棵树。日志里是 `no source changes` 时退出码也是 0。树已经在本地、想跳过等待时，可以在同一条命令前加 `INTAKE_SOURCE_ICLOUD_WAIT=0`，通过标准仍是 rc=0。

不要跑 `run_digest_jobs.sh`：它会调 YouTube API 并写 vault。

7. 按第 4 节 `bootout` / `bootstrap`，然后：

```bash
launchctl kickstart -k "gui/$(id -u)/com.jake.intake-source-push"
ERR=$(plutil -extract StandardErrorPath raw "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist")
tail -n 50 "$ERR"
```

这次写进 err log 的行里不要有 `error:`。

8. 上面都通过，再合 PR。
9. 合完以后，在同一个插件检出：

```bash
git checkout main
git pull origin main
git rev-parse HEAD
```

确认 HEAD 是合并提交。`config.json` 被 gitignore，会留在检出根。然后再按第 4 节 `bootout` / `bootstrap` / `kickstart` 一次，并再看一遍 err log。这次 job 跑的是合并后的 `main`。

## 7. 一步回滚

合并若是 squash，在 `main` 上 revert 那一个 squash 提交并 push。插件检出 `git pull`。

不 revert 远端时，把插件工作副本钉回第 6 节记下的合并前 SHA：

```bash
git checkout <合并前 origin/main 的 SHA>
```

然后重载并踢一次 intake job：

```bash
launchctl bootout "gui/$(id -u)/com.jake.intake-source-push"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl kickstart -k "gui/$(id -u)/com.jake.intake-source-push"
```

plist 里多出来的环境变量可以留着，旧脚本不读它们。`config.json` 里多出来的 `git_user_name` / `git_user_email` 也可以留着。第 4.1 节放到检出外的 reconcile 副本和它的 plist 留在原地，不要删。若当时只做了 `bootout`、plist 还在，这个 job 保持停止；要让它再跑，检出得回到 `cursor/cognition-v1.1`，或者 plist 已经指向检出外的副本。

确认已经回到旧行为：

```bash
git rev-parse HEAD
git grep -n DEFAULT_VAULT -- scripts/daily_digest.py
launchctl print "gui/$(id -u)/com.jake.intake-source-push"
ERR=$(plutil -extract StandardErrorPath raw "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist")
tail -n 30 "$ERR"
```

`git rev-parse HEAD` 等于合并前记下的 SHA（钉工作副本时），或等于 revert 之后的新 `main`（走 revert 时）。`git grep` 能看到 `DEFAULT_VAULT`。`launchctl print` 里 intake 这个 label 仍在。kickstart 之后的 err log 里不应再出现缺 `git_user_name` 的报错。reconcile 若按第 4.1 节留着，`launchctl print "gui/$(id -u)/com.jake.digitalbrain-reconcile"` 的程序路径仍是检出外的副本，或仍是你没有删除的那份 plist。
