# 本机切换清单

现有 Mac 从「脚本里写死的个人默认路径」改成显式配置。先在本 PR 分支上配好并干跑，通过后再合。合之前不要把真实路径、账号、邮箱写进仓库。

本文件只写占位符。vault 路径填你已经在用的那一个绝对路径。

## 1. `config.json` 放哪

读取顺序以 `scripts/infoflow_config.py` 的 `require_setting` 和 `resolve_config_path` 为准：

1. 命令行已经给出的**值**。`daily_digest.py`、`weekly_rollup.py`、`youtube_likes.py`、`sync_digitalbrain_skills.py` 的 `--vault` 覆盖 `vault_root`。
2. 环境变量（有非空值才用）：
   - `vault_root` → `INFOFLOW_VAULT_ROOT`
   - `git_remote` → `INFOFLOW_GIT_REMOTE`
   - `git_branch` → `INFOFLOW_GIT_BRANCH`
   - `storage_mode` → `INFOFLOW_STORAGE_MODE`
3. 配置文件。选文件的顺序：
   - 调用时传了 `--config`，用那个路径
   - 否则用 `INFOFLOW_CONFIG`（非空）
   - 否则，若代码仓根目录（`scripts/` 的上一级）已经有 `config.json`，用它
   - 这一层的文件不存在就跳过，不会新建
4. 还是没有：非 0 退出。没有内置路径。

`infoflow_config.py get` 的选文件参数是 `--config`。例子：

```bash
python3 scripts/infoflow_config.py get vault_root --config /ABSOLUTE/PATH/config.json
```

scaffold 写入时的默认文件不同：没传 `--config` 时，有 `INFOFLOW_CONFIG` 就写那里，否则写代码仓根的 `config.json`（文件可以事先不存在）。

仓库根 `.gitignore` 的 `/config.json` 只忽略仓库根这一份。填好的文件不要提交。`INFOFLOW_CONFIG` 指到仓外时，那份文件本来就不在这个 git 里。

## 2. 字段

从 `config.example.json` 复制后再改占位符。含 `REPLACE_WITH_` 的值会被拒绝。

```json
{
  "vault_root": "REPLACE_WITH_VAULT_ROOT",
  "storage_mode": "A",
  "git_remote": "REPLACE_WITH_GIT_REMOTE",
  "git_branch": "main",
  "enabled_sources": []
}
```

| 字段 | 填什么 | 谁会读 |
| --- | --- | --- |
| `vault_root` | 你现有 vault 的绝对路径 | 没传 `--vault`、也没设 `INFOFLOW_VAULT_ROOT` 时，intake / sync / `run_digest_jobs.sh` |
| `storage_mode` | `A`（私有 git vault）或 `B`（本地目录） | scaffold 写入。日常 intake 脚本不读 |
| `git_remote` | 数据仓 remote。占位符 `REPLACE_WITH_GIT_REMOTE` | `push_intake_sources.sh` 在 `INTAKE_SOURCE_REMOTE` 为空时读取；也可用 `INFOFLOW_GIT_REMOTE` |
| `git_branch` | scaffold 模式 A 的分支，示例是 `main` | scaffold。`push_intake_sources.sh` 仍推 `main`，不读这个字段 |
| `enabled_sources` | 可选数组，示例留空 | 当前脚本不读 |

Git 身份**不在** `config.json` 里。`push_intake_sources.sh` 只要环境变量：

- `INTAKE_GIT_USER_NAME`：填 `REPLACE_WITH_GIT_USER_NAME`（你在该数据仓上已经使用的提交名）
- `INTAKE_GIT_USER_EMAIL`：填 `REPLACE_WITH_GIT_USER_EMAIL`（对应邮箱）

YouTube 密钥也不进 `config.json`。见下一节。

`push_intake_sources.sh` 还有两个可选变量，不设就用脚本里的非个人默认：`INTAKE_SOURCE_WORKTREE`（默认是插件仓下的 `state/digitalbrain-main`）、`INTAKE_SOURCE_ICLOUD_WAIT`（默认 `45`，秒）。

## 3. YouTube 环境变量

| 变量 | 指向 |
| --- | --- |
| `YOUTUBE_CLIENT_FILE` | OAuth client JSON。文件里要有 `installed` 或 `web`，以及 `client_id` / `client_secret` |
| `YOUTUBE_TOKEN_FILE` | token JSON。`youtube_oauth.py` 会把它写出来，里面要有 `refresh_token` |

两个文件都放在 vault 外面，也放在 information-flow 代码仓外面。

交互 shell 可以写进你自己的 shell 启动文件。launchd **不会**读那个文件。要给 launchd 用，写进已安装 plist 的 `EnvironmentVariables`，并靠下一节的 wrapper 转发。

`INFOFLOW_VAULT_ROOT` 可以代替 `config.json` 里的 `vault_root`。它不代替 YouTube 的两个文件变量。

只准备 OAuth、还不跑同步时：

```bash
python3 scripts/youtube_oauth.py
```

它读 `YOUTUBE_CLIENT_FILE`，把 token 写到 `YOUTUBE_TOKEN_FILE`。

## 4. launchd

仓内和这次切换有关的 job 只有 `launchd/com.jake.intake-source-push.plist`。

- Label：`com.jake.intake-source-push`
- 登录时跑，之后每 14400 秒
- `ProgramArguments` 调 `osascript`，脚本是 `scripts/run_intake_source_push.applescript`
- 该 AppleScript 用 `do shell script` 执行 `scripts/push_intake_sources.sh`

`do shell script` 不继承 launchd 的环境。本分支的 AppleScript 用 `system attribute` 把进程上已有的这些名字抄进命令（空的不抄）：

`INTAKE_VAULT`、`INTAKE_SOURCE_REMOTE`、`INTAKE_GIT_USER_NAME`、`INTAKE_GIT_USER_EMAIL`、`INTAKE_SOURCE_WORKTREE`、`INTAKE_SOURCE_ICLOUD_WAIT`、`PLUGIN_ROOT`、`PYTHON3`、`INFOFLOW_CONFIG`、`INFOFLOW_VAULT_ROOT`、`INFOFLOW_GIT_REMOTE`、`INFOFLOW_GIT_BRANCH`、`INFOFLOW_STORAGE_MODE`、`YOUTUBE_CLIENT_FILE`、`YOUTUBE_TOKEN_FILE`。

已加载的 agent 用的是本机 `~/Library/LaunchAgents/` 里的副本。只改仓库里的 plist 不会改正在跑的 job。在**已安装**的那份 plist 的 `EnvironmentVariables` 里加上这个 job 需要的键。这个 job 不跑 YouTube，可以不设 `YOUTUBE_*`。

`push_intake_sources.sh` 实际需要：

- vault：`INTAKE_VAULT`，否则按第 1 节读 `vault_root`
- remote：`INTAKE_SOURCE_REMOTE`，否则按第 1 节读 `git_remote`
- `INTAKE_GIT_USER_NAME` 和 `INTAKE_GIT_USER_EMAIL`：必填，没有配置字段

plist 里已有的 `HOME` 留着。wrapper 在 `HOME` 为空时仍有硬编码兜底；不要靠那个兜底。

`run_digest_jobs.sh` 在仓里没有 plist。`docs/plan-weekly-intake.md` 写明本机 digest 的 launchd 保持卸载。它若被另挂，会依次跑：

1. `scripts/youtube_likes.py --vault <vault_root>`，因此还要 `YOUTUBE_CLIENT_FILE` 和 `YOUTUBE_TOKEN_FILE`
2. `scripts/daily_digest.py --vault <vault_root>`
3. `scripts/weekly_rollup.py --vault <vault_root>`

它不需要 git 身份。`youtube_oauth.py` 只手动跑。

文档里还出现、但本仓没有 plist 的名字：`com.jake.journal-daily-digest`（保持卸载）、`com.jake.digitalbrain-reconcile`。`ops/digitalbrain-backup` 的 backup job 不读 `infoflow_config.py`，这次不用改。

改完先检查，再重载：

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl bootout "gui/$(id -u)/com.jake.intake-source-push"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
launchctl print "gui/$(id -u)/com.jake.intake-source-push"
```

较旧的 launchctl：对同一个 plist 用 `launchctl unload`，再用 `launchctl load`。

重载放在第 6 节的干跑通过、并且插件目录已经是合并后的 `main` 之后。干跑期间让已加载的 agent 继续跑合并前的代码。

## 5. GitHub Actions

对过 `.github/workflows/` 里这三份文件。它们的命令都带 `--vault digitalbrain`（runner 上 checkout 出来的目录），不读已删除的个人 vault 默认，也不读本机 `config.json`。

| workflow | 和这次默认值的关系 | 要不要改 |
| --- | --- | --- |
| `daily-intake.yml` | 用已有 secrets `YOUTUBE_TOKEN`、`YOUTUBE_CLIENT` 写成 runner 上的文件，再 export `YOUTUBE_TOKEN_FILE`、`YOUTUBE_CLIENT_FILE`，然后 `youtube_likes.py --vault digitalbrain`。接着 `sync_digitalbrain_skills.py --vault digitalbrain`。vault checkout 仍用已有的 `DIGITALBRAIN_TOKEN` | 不用改。合并后不会因为去掉本机默认而失败 |
| `sync-digitalbrain-skills.yml` | `sync_digitalbrain_skills.py --vault digitalbrain`，以及在数据仓目录里 `--vault .`。密钥仍是 `DIGITALBRAIN_TOKEN` | 不用改 |
| `weekly-digest.yml` | `process_batch.py` 和 `build_digest_v2.py` 本来就要求 `--vault digitalbrain`。不读 YouTube 文件变量 | 不用改 |

本 PR 不改这三份 workflow。

## 6. 先干跑，再合并

在合并前记下当前 `main`，回滚要用：

```bash
git fetch origin
git rev-parse origin/main
```

在**本 PR 分支**的插件检出里做下面的事。不要先合。

1. `cp config.example.json config.json`，把 `vault_root` 换成你现有 vault 的绝对路径，把 `git_remote` 换成数据仓 remote，`storage_mode` 填 `A` 或 `B`。
2. 在同一个 shell 里导出 `INTAKE_GIT_USER_NAME`、`INTAKE_GIT_USER_EMAIL`、`YOUTUBE_CLIENT_FILE`、`YOUTUBE_TOKEN_FILE`。若 `config.json` 不在仓库根，再导出 `INFOFLOW_CONFIG`。
3. 只跑读取，不跑会 push 或会打 YouTube API 的成功路径：

```bash
python3 scripts/infoflow_config.py get vault_root
python3 scripts/infoflow_config.py get git_remote
python3 scripts/infoflow_config.py get git_branch
test -d "$(python3 scripts/infoflow_config.py get vault_root)"
test -n "$INTAKE_GIT_USER_NAME"
test -n "$INTAKE_GIT_USER_EMAIL"
python3 - << 'PY'
import sys
sys.path.insert(0, "scripts")
from youtube_likes import client_path, token_path
for path in (client_path(), token_path()):
    if not path.is_file():
        raise SystemExit("missing secrets file: " + path.name)
    print("ok " + path.name)
PY
env -u INTAKE_GIT_USER_NAME -u INTAKE_GIT_USER_EMAIL \
  INTAKE_SOURCE_ICLOUD_WAIT=0 \
  /bin/sh scripts/push_intake_sources.sh
```

最后一条必须马上以退出码 1 结束，stderr 含 `INTAKE_GIT_USER_NAME and INTAKE_GIT_USER_EMAIL are required`。若输出里出现 `waiting` 或 `cloning`，停，不要再跑。那表示脚本已经越过身份检查。

不要把 `push_intake_sources.sh` 在身份齐全时跑一遍当干跑：它会提交并 push。不要跑 `run_digest_jobs.sh`：它会调 YouTube API 并写 vault。

4. `plutil -lint` 已安装的 plist。先不要 `bootstrap`，除非这个插件目录已经是你验证过的分支，并且你接受 agent 开始用新脚本。
5. 上面都通过，再合 PR。
6. 合完以后在插件目录：

```bash
git checkout main
git pull origin main
git rev-parse HEAD
```

确认 HEAD 是合并提交，然后按第 4 节 `bootout` / `bootstrap`。

## 7. 一步回滚

合并若是 squash，在 `main` 上 revert 那一个 squash 提交并 push。插件目录 `git pull`，再按第 4 节重载 launchd。plist 里多出来的环境变量可以留着，旧脚本不读它们。

不 revert 远端时，把插件工作副本钉回第 6 节记下的合并前 SHA：

```bash
git checkout <合并前 origin/main 的 SHA>
launchctl bootout "gui/$(id -u)/com.jake.intake-source-push"
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.jake.intake-source-push.plist"
```

确认已经回到旧行为：

```bash
git rev-parse HEAD
git grep -n DEFAULT_VAULT -- scripts/daily_digest.py
launchctl print "gui/$(id -u)/com.jake.intake-source-push"
```

`git rev-parse HEAD` 等于合并前记下的 SHA（钉工作副本时），或等于 revert 之后的新 `main`（走 revert 时）。`git grep` 能看到 `DEFAULT_VAULT`。`launchctl print` 里这个 label 仍在。下一次该 job 的日志里不应再出现缺 `INTAKE_GIT_USER_NAME` 的报错。
