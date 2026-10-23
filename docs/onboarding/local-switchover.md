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

plist 改完先检查再重载。kickstart 和判定放在紧接着的通过标准里，不要只看 `tail`：

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl bootout "gui/$(id -u)/com.jake.intake-source-push"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
```

仓库模板里的 `StandardErrorPath` 文件名是插件检出下的 `state/intake-source-push.err.log`。

通过标准（intake 和 reconcile 每次 kickstart 之后都用这一套）：

1. `launchctl print "gui/$(id -u)/<label>"` 里这一次运行的 `last exit code = 0`。kickstart 返回时 job 可能还在跑；`runs` 要比 kickstart 之前大 1，并且 `state` 不再是 running，再读 `last exit code`。
2. 该 plist 的 `StandardErrorPath` 里，这一次新写的行没有 `error:`，没有 `missing`，也没有 `is still a placeholder`。配置缺失打印的是 `missing …` 或 `… is still a placeholder`，不是 `error:`。

```bash
label=com.jake.intake-source-push
plist="$HOME/Library/LaunchAgents/${label}.plist"
ERR=$(plutil -extract StandardErrorPath raw "$plist")
before=$(wc -l < "$ERR" | tr -d ' ')
launchctl print "gui/$(id -u)/$label" | grep -E 'runs =|last exit code ='
launchctl kickstart -k "gui/$(id -u)/$label"
launchctl print "gui/$(id -u)/$label" | grep -E 'state =|runs =|last exit code ='
tail -n +"$((before + 1))" "$ERR" | grep -E 'error:|missing|is still a placeholder' && echo "stderr FAIL" || echo "stderr ok"
```

`last exit code = 0` 并且输出 `stderr ok` 才算通过。reconcile 把 `label` 换成 `com.jake.digitalbrain-reconcile`。

较旧的 launchctl：对同一个 plist 用 `launchctl unload`，再用 `launchctl load`。

这些命令放在第 6 节的读取和 `push_intake_sources.sh` 已经是 rc=0 之后。kickstart 时，intake plist 指向的检出必须已经是你正在验证的分支。

### 4.1 reconcile：本机正在跑的是本地提交加未提交改动

先做本节，并且工作区还是脏的时候做。做完再做第 6 节的备份提交，然后再 `git checkout`。不要删除这个 job 的 plist，不要 `rm` LaunchAgents 里的文件。

远端 `origin/cursor/cognition-v1.1` 上能看到的 `scripts/reconcile_live_vault_untracked.py` 来自提交 `7608291`，远端仓库里没有 reconcile AppleScript，也没有 `icloud_io.py`。本机正在跑的不是那份远端快照。本机插件检出在 `cursor/cognition-v1.1` 之上还有两笔未推送的本地提交 `9fdc2ec` 和 `4ca393e`，再加上 4 个未提交改动（其中有 `scripts/push_intake_sources.sh`）。正在跑的 reconcile 来自这些本地提交和未提交改动，不在远端仓库里。

本机有一份 reconcile AppleScript，只在这台 Mac 上，不在远端 git 里。它大约第 10 行的 `scriptPath` 把插件检出路径写死到 `reconcile_live_vault_untracked.py`。这份 .py 依赖同目录、未进 git 的 `icloud_io.py`，锁放在插件检出里的 `state/`。job 大约每 2 分钟跑一次，label 是 `com.jake.digitalbrain-reconcile`。`main` 和本 PR 都没有这份本地实现。本 PR 的 `push_intake_sources.sh` 也不再在结束时调用它。不要把整支 `cursor/cognition-v1.1` 合并进 `main` 来保留这个 job。

**默认是 (a)。** 这个 job 每 2 分钟都在跑。(a) 让它继续做同一件事，运行中的系统不被停掉。(b) 会停掉它。

**(a) 默认：三份文件一起拷到检出外面，job 继续跑**

```bash
launchctl print "gui/$(id -u)/com.jake.digitalbrain-reconcile" | grep -E 'state =|runs =|last exit code ='
plutil -extract ProgramArguments xml1 -o - "$HOME/Library/LaunchAgents/com.jake.digitalbrain-reconcile.plist"
mkdir -p "$HOME/infoflow-switchover-backup" "$HOME/infoflow-reconcile-runtime/state"
cp "$HOME/Library/LaunchAgents/com.jake.digitalbrain-reconcile.plist" \
  "$HOME/infoflow-switchover-backup/com.jake.digitalbrain-reconcile.plist"
```

plist 文件名以 `ls "$HOME/Library/LaunchAgents" | grep -i reconcile` 为准。把下面三份**当前工作区里的文件**（含未提交内容）拷进 `$HOME/infoflow-reconcile-runtime/`，放在同一目录：

- plist 的 `ProgramArguments` 指向的那份 AppleScript
- 检出里的 `scripts/reconcile_live_vault_untracked.py`
- 它旁边的 `icloud_io.py`

然后：

1. 在副本目录保留刚建的 `state/`。打开副本 .py，若锁路径仍指向插件检出里的 `state/`，只改副本里的这一处，指到 `$HOME/infoflow-reconcile-runtime/state`。检出里的原文件先留着，交给第 6 节备份。
2. 打开副本 AppleScript，把大约第 10 行的 `scriptPath` 改成副本 .py 的绝对路径。
3. 改已安装 plist 的 `ProgramArguments`，让它指向这份副本 AppleScript。

重载并按本节上面的通过标准查一次（切换分支之前）：

```bash
label=com.jake.digitalbrain-reconcile
plist="$HOME/Library/LaunchAgents/${label}.plist"
plutil -lint "$plist"
ERR=$(plutil -extract StandardErrorPath raw "$plist")
before=$(wc -l < "$ERR" | tr -d ' ')
launchctl print "gui/$(id -u)/$label" | grep -E 'runs =|last exit code ='
launchctl bootout "gui/$(id -u)/$label"
launchctl bootstrap "gui/$(id -u)" "$plist"
launchctl kickstart -k "gui/$(id -u)/$label"
launchctl print "gui/$(id -u)/$label" | grep -E 'state =|runs =|last exit code ='
tail -n +"$((before + 1))" "$ERR" | grep -E 'error:|missing|is still a placeholder' && echo "stderr FAIL" || echo "stderr ok"
```

`runs` 增加 1，`last exit code = 0`，并且输出 `stderr ok`。这次通过之后再切换分支。切到合并后的 `main` 之后，用同一组命令再查一次。两遍都要通过。副本在检出外面，所以换分支之后它仍每 2 分钟跑。不要删除 plist。

**(b) 停掉 label，plist 文件留着**

只在你接受下面的后果时用。不要删除 plist。

```bash
launchctl bootout "gui/$(id -u)/com.jake.digitalbrain-reconcile"
launchctl print "gui/$(id -u)/com.jake.digitalbrain-reconcile" || true
ls "$HOME/Library/LaunchAgents" | grep -i reconcile
```

`print` 找不到 label，`ls` 仍能看到 plist 文件。停着的这段时间里，这个 job 不再做的事是：清掉 vault 里与即将拉下来的版本字节相同的未跟踪副本，好让 Obsidian Git 的 pull 能快进；内容不同的文件本来就会留在原地。已提交的笔记不会被删。后果是 pull 会继续被这些未跟踪副本挡住，新落到 vault 里的未跟踪文件也会一直挡着，直到以后再 `bootstrap` 这份 plist。检出里的 `state/` 锁不再被这个 job 更新。

## 5. GitHub Actions

对过 `.github/workflows/` 里这三份文件。它们的命令都带 `--vault digitalbrain`（runner 上 checkout 出来的目录），不读已删除的个人 vault 默认，也不读本机 `config.json`。

| workflow | 和这次默认值的关系 | 要不要改 |
| --- | --- | --- |
| `daily-intake.yml` | 用已有 secrets `YOUTUBE_TOKEN`、`YOUTUBE_CLIENT` 写成 runner 上的文件，再 export `YOUTUBE_TOKEN_FILE`、`YOUTUBE_CLIENT_FILE`，然后 `youtube_likes.py --vault digitalbrain`。接着 `sync_digitalbrain_skills.py --vault digitalbrain`。vault checkout 仍用已有的 `DIGITALBRAIN_TOKEN` | 不用改。合并后不会因为去掉本机默认而失败 |
| `sync-digitalbrain-skills.yml` | `sync_digitalbrain_skills.py --vault digitalbrain`，以及在数据仓目录里 `--vault .`。密钥仍是 `DIGITALBRAIN_TOKEN` | 不用改 |
| `weekly-digest.yml` | `process_batch.py` 和 `build_digest_v2.py` 本来就要求 `--vault digitalbrain`。不读 YouTube 文件变量，也不读 git 身份 | 不用改 |

本 PR 不改这三份 workflow。

## 6. 先保住本机状态，再验证，再合并，最后才切到 `main`

当前检出在 `cursor/cognition-v1.1` 上，上面有未推送的 `9fdc2ec` 和 `4ca393e`，工作区还有 4 个未提交改动（含 `scripts/push_intake_sources.sh`）。带着这些脏文件去 `git checkout` 会被拒绝。先拷 reconcile（第 4.1 节，默认 (a)），再做下面的备份，然后再换分支。

1. 工作区还脏着时做完第 4.1 节默认 (a)，并且切换前的那一次 reconcile 已经是 `last exit code = 0` 且 `stderr ok`。
2. **默认用本地备份分支**把当前 HEAD 和未提交改动都留下。日期换成当天。备份分支只留在这台 Mac 上。

```bash
set -e
mkdir -p "$HOME/infoflow-switchover-backup"
cd "$HOME/plugins/information-flow"
git branch --show-current
git rev-parse HEAD | tee "$HOME/infoflow-switchover-backup/pre-switch-head.txt"
git merge-base --is-ancestor 9fdc2ec HEAD
git merge-base --is-ancestor 4ca393e HEAD
git status --short | tee "$HOME/infoflow-switchover-backup/status-before.txt"
git branch backup/pre-switchover-2026-10-23
git stash push -u -m "pre-switchover-2026-10-23"
git checkout backup/pre-switchover-2026-10-23
git stash pop
# stash pop 若停在冲突，先解决完再提交；不要在冲突未解决时 checkout 本 PR 分支。
git add -A
git commit -m "backup: uncommitted Mac state before switchover"
git checkout cursor/cognition-v1.1
git status --short
git merge-base --is-ancestor 9fdc2ec HEAD
git merge-base --is-ancestor 4ca393e HEAD
git merge-base --is-ancestor "$(cat "$HOME/infoflow-switchover-backup/pre-switch-head.txt")" backup/pre-switchover-2026-10-23
git diff --stat "$(cat "$HOME/infoflow-switchover-backup/pre-switch-head.txt")" backup/pre-switchover-2026-10-23
```

`git branch --show-current` 先是 `cursor/cognition-v1.1`。两个 `merge-base --is-ancestor` 的退出码都是 0，说明 `9fdc2ec` 和 `4ca393e` 都在当前 HEAD 里。`status-before.txt` 里要有 `scripts/push_intake_sources.sh`。提交之后回到 `cursor/cognition-v1.1`，`git status --short` 为空，HEAD 仍等于 `pre-switch-head.txt`。`git diff --stat` 里能看到刚才那 4 个未提交路径，包括 `scripts/push_intake_sources.sh`。

另一种是只 `git stash push -u -m "pre-switchover-2026-10-23"`，不建分支。回滚命令按第 7 节的备份分支来。默认走备份分支。

3. 记下远端 `main`，给远端 squash 回滚用：

```bash
git fetch origin
git rev-parse origin/main | tee "$HOME/infoflow-switchover-backup/origin-main-before.txt"
```

4. 在这个 `plugins/information-flow` 检出里检出本 PR 分支（含本文件的 `cursor/empty-vault-onboarding-6aee`）。先不要 `git checkout main`。
5. `cp config.example.json config.json`。把 `vault_root` 换成你现有 vault 的绝对路径，把 `git_remote` 换成数据仓 remote，`storage_mode` 填 `A` 或 `B`，`git_branch` 保持你要用的分支（示例 `main`），`git_user_name` 和 `git_user_email` 换成该数据仓上已经在用的提交身份。每个 `REPLACE_WITH_` 都要换掉。
6. 在这个 shell 里导出 `YOUTUBE_CLIENT_FILE` 和 `YOUTUBE_TOKEN_FILE`，供下面的密钥检查。要验证 launchd 那种「plist 只有 HOME/PATH」的路径，就不要导出 `INTAKE_GIT_USER_NAME` 和 `INTAKE_GIT_USER_EMAIL`。若 `config.json` 不在检出根，再导出 `INFOFLOW_CONFIG`。
7. 验证命令：

```bash
python3 scripts/infoflow_config.py get vault_root
python3 scripts/infoflow_config.py get git_remote
python3 scripts/infoflow_config.py get git_branch
python3 scripts/infoflow_config.py get git_user_name
python3 scripts/infoflow_config.py get git_user_email
test -d "$(python3 scripts/infoflow_config.py get vault_root)"
/bin/sh scripts/push_intake_sources.sh >"$HOME/infoflow-switchover-backup/push.out" 2>"$HOME/infoflow-switchover-backup/push.err"
echo "push_intake_sources rc=$?"
grep -E 'error:|missing|is still a placeholder' "$HOME/infoflow-switchover-backup/push.err" && echo "push stderr FAIL" || echo "push stderr ok"
```

`push_intake_sources rc` 必须是 `0`，并且输出 `push stderr ok`。stderr 里不能有 `error:`、`missing` 或 `is still a placeholder`。脚本默认先等 45 秒，然后只在 Snipd / WeRead 有差异时提交并 push 这两棵树。日志里是 `no source changes` 时退出码也是 0。树已经在本地、想跳过等待时，可以在同一条命令前加 `INTAKE_SOURCE_ICLOUD_WAIT=0`，通过标准仍是 rc=0 且 `push stderr ok`。

不要跑 `run_digest_jobs.sh`：它会调 YouTube API 并写 vault。

8. 按第 4 节重载 intake，并用那里的通过标准。`label` 用 `com.jake.intake-source-push`。`last exit code = 0`，`runs` 比 kickstart 前大 1，新的 stderr 行输出 `stderr ok`。
9. 上面都通过，再合 PR。
10. 合完以后，在同一个插件检出：

```bash
git checkout main
git pull origin main
git rev-parse HEAD
```

确认 HEAD 是合并提交。`config.json` 被 gitignore，会留在检出根。再对 `com.jake.intake-source-push` 做一次第 4 节的 bootout / bootstrap / kickstart，通过标准仍是 `last exit code = 0` 且 `stderr ok`。这次 intake 跑的是合并后的 `main`。然后对 `com.jake.digitalbrain-reconcile` 再做一次第 4.1 节的同一组检查（切换到 `main` 之后的那一次）。两遍 reconcile（切换前、切到 `main` 后）和两遍 intake（PR 分支上、切到 `main` 后）都要满足这个标准。

## 7. 一步回滚

回滚这台 Mac 的插件检出：回到 `cursor/cognition-v1.1` 在备份时的那一点（HEAD 含 `9fdc2ec` 和 `4ca393e`），把未提交改动放回工作区，然后重载 launchd。

```bash
set -e
cd "$HOME/plugins/information-flow"
git checkout cursor/cognition-v1.1
test "$(git rev-parse HEAD)" = "$(cat "$HOME/infoflow-switchover-backup/pre-switch-head.txt")"
git merge-base --is-ancestor 9fdc2ec HEAD
git merge-base --is-ancestor 4ca393e HEAD
git restore --source=backup/pre-switchover-2026-10-23 --worktree --staged .
git reset
git status --short | tee "$HOME/infoflow-switchover-backup/status-after-rollback.txt"
diff -u "$HOME/infoflow-switchover-backup/status-before.txt" "$HOME/infoflow-switchover-backup/status-after-rollback.txt"
cp "$HOME/infoflow-switchover-backup/com.jake.digitalbrain-reconcile.plist" \
  "$HOME/Library/LaunchAgents/com.jake.digitalbrain-reconcile.plist"
```

`test` 通过，两个 `merge-base --is-ancestor` 退出码都是 0，`diff -u` 没有输出。`status-after-rollback.txt` 里再次出现 `scripts/push_intake_sources.sh`。若当时走的是 (b)、plist 没改过，就跳过最后一条 `cp`。不要删除 plist。

然后重载并踢两个 job，通过标准与第 4 节相同（`last exit code = 0`，新 stderr 没有 `error:` / `missing` / `is still a placeholder`）：

```bash
for label in com.jake.intake-source-push com.jake.digitalbrain-reconcile; do
  plist="$HOME/Library/LaunchAgents/${label}.plist"
  ERR=$(plutil -extract StandardErrorPath raw "$plist")
  before=$(wc -l < "$ERR" | tr -d ' ')
  launchctl bootout "gui/$(id -u)/$label" || true
  launchctl bootstrap "gui/$(id -u)" "$plist"
  launchctl kickstart -k "gui/$(id -u)/$label"
  launchctl print "gui/$(id -u)/$label" | grep -E 'state =|runs =|last exit code ='
  tail -n +"$((before + 1))" "$ERR" | grep -E 'error:|missing|is still a placeholder' && echo "$label stderr FAIL" || echo "$label stderr ok"
done
git grep -n DEFAULT_VAULT -- scripts/daily_digest.py
```

两个 label 都是 `last exit code = 0` 和 `stderr ok`。`git grep` 能看到 `DEFAULT_VAULT`，说明检出已回到带旧默认路径的 `cursor/cognition-v1.1`。若 (b) 当时把 reconcile bootout 了，这次 `bootstrap` 会把它装回去；plist 文件一直还在。

远端 `main` 若已经 squash 合并了本 PR，在 `main` 上再 revert 那一个 squash 并 push。这一步只动远端。Mac 上的 job 以本节把检出放回 `cursor/cognition-v1.1` 为准，不是 `git pull` 之后停在 revert 后的 `main`。
