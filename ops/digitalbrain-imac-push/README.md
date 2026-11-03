# DigitalBrain 推送任务（常开那台 Mac 上唯一的推送方）

这个文件夹是 `com.jake.digitalbrain-imac-push` 的正本。2026-11-01 起它在 Jake 的 iMac 上每 10 分钟跑一次，是唯一从电脑往 GitHub 笔记仓推笔记的任务。整体分工（谁推、谁拉、出了问题怎么知道）见 `docs/digitalbrain-sync.md`。

这次只是把正在跑的东西放进仓库，iMac 上什么都没改。

## 它做什么

- 只读 iCloud 里的 Obsidian 笔记库，只看三个文件夹：「📥 Inbox/Snipd」「📥 Inbox/WeRead」「📚 Books」。
- 有改动的文件，抄进自己的一份 Git 克隆（放在 iCloud 外面），做一个提交，推到 GitHub 的 main。提交说明以「imac: sync Snipd WeRead Books」开头。
- 每 10 分钟一次，开机也跑一次。低优先级运行，每轮最多 2 分钟。
- 规矩都写在代码里，测试一条条盯着：
  - 三个文件夹以外的路径一律不推；只加具体文件路径，不用 `git add -A`。
  - 不强推，不变基，不合并。推送被拒就丢掉自己克隆里那个提交，下一轮再来。
  - 本地删掉的文件，GitHub 上不删。
  - 跳过：iCloud 还没下载的占位文件、「xxx 2.md」冲突副本、3 分钟内刚改过的文件、两次读之间变了的文件、两边都改过的文件。
  - 绝不写笔记库，也不在笔记库里跑 Git。脚本开头装了一道守门：任何往笔记库写、删、改名、建文件夹，或在笔记库里跑命令的动作，立刻中止整个进程。
  - 拉取（Obsidian Git）没跟上 GitHub 时，这一轮整轮不推；落后超过 10 分钟，状态文件里标「要人看」。
  - 推完以后，只有在推上去的每一篇都和笔记库逐字节一样时，才顺手更新拉取那份 Git 的记账；不一样就留到下一轮。
  - 避开交易任务和备份任务的时段（按上海时间写在 `QUIET_WINDOWS` 里）。
- 告警只写两处：日志 `<推送目录>/logs/push.log` 和状态文件 `<推送目录>/state/status.json`。不发消息，不开 GitHub 议题。
- 只用 Python 标准库。

## 文件

| 文件 | 是什么 |
| --- | --- |
| `bin/push_from_icloud.py` | 推送脚本。和 iMac 上正在跑的那份逐字节一样，sha256 `c12a6af32bc1fc8518d544d0712ed5ee99ee73c2ac6d7cb0f1ad1da738d74b49` |
| `launchd/com.jake.digitalbrain-imac-push.plist` | 正式任务模板：每 600 秒一次，开机也跑 |
| `launchd/com.jake.digitalbrain-imac-push.dryrun.plist` | 演练模板：只跑一次，做提交但不推（带 `--dry-run --probe-push`），只处理一份路径清单里的文件 |
| `launchd/com.jake.digitalbrain-imac-push.cutover.plist` | 切换模板：只跑一次，只推一份路径清单里的文件（2026-11-01 切换当天用过） |
| `bin/render_launchd.py` | 把模板里的占位符换成本机的值，写到一个输出文件夹，并打印每个文件的 sha256。只生成文件，不安装、不启动 |
| `deploy.example.env` | 本机部署示例：Jake 那台 iMac 的实际值 |
| `tests/test_push_from_icloud.py` | 推送脚本的 19 项测试，用假仓库、假笔记库，每项前后都核对假笔记库没被改过 |
| `tests/test_render_launchd.py` | 6 项测试：用示例值填出来的三份模板，和 iMac 上装的三份逐字节一样；脚本指纹没变；模板里没有个人路径；少值、多值都报错 |

模板里的占位符：

| 占位符 | 意思 |
| --- | --- |
| `__HOME__` | 运行这个任务的用户的主目录 |
| `__PUSHER_ROOT__` | 推送目录：放 `bin/`、`repo/`（推送专用克隆）、`state/`、`logs/` |
| `__PUSH_PYTHON__` | 跑脚本用的 Python。它要能读 iCloud 笔记库（有完全磁盘访问权限）。Jake 那台用的是备份任务那份专用 Python |
| `__VAULT__` | iCloud 里的 Obsidian 笔记库 |
| `__PULL_GITDIR__` | 拉取那份 Git 资料（Obsidian Git 用的那份，推送地址是无效地址） |

演练和切换模板都读 `__PUSHER_ROOT__/state/cutover-5-paths.txt`：一行一个仓库里的具体路径。这份清单是一次性的，内容是个人笔记的路径，不放进仓库，要用时在那台 Mac 上现写。

## 测试

在仓库根目录：

```bash
python3 -m pytest -q ops/digitalbrain-imac-push/tests
```

应该是 25 项全过（19 ＋ 6）。也可以单独跑 `python3 ops/digitalbrain-imac-push/tests/test_push_from_icloud.py`。

## 怎么部署

Jake 的 iMac 2026-11-01 已经装好、在跑，**不用重装**。下面是换一台电脑，或者以后改了脚本要重新装时的步骤。每一步改动都单独弹批准卡，避开交易时段（美东 9:30–16:00，以及 `QUIET_WINDOWS` 里那几段）。

1. 准备值：

   ```bash
   cd ops/digitalbrain-imac-push
   cp deploy.example.env deploy.env   # deploy.env 不进仓库
   # 按那台电脑改 deploy.env 里的五个值
   python3 bin/render_launchd.py --env deploy.env --out rendered/
   ```

   会打印三份生成好的设置文件和各自的 sha256。

2. 在那台 Mac 上建推送目录，把脚本放进去：`<推送目录>/bin/push_from_icloud.py`，再建 `logs/` 和 `state/`，三个目录权限 700。拷完核对脚本 sha256。

3. 建推送专用克隆 `<推送目录>/repo`：放在 iCloud 外面；只检出那三个文件夹（稀疏检出）；推送凭证用本机已登录的 `gh`（存在钥匙串里，仓库里不放任何令牌）；关掉钩子；不取标签。

4. 先演练：在 `state/cutover-5-paths.txt` 写几条要试的路径，把 `rendered/com.jake.digitalbrain-imac-push.dryrun.plist` 放进 `~/Library/LaunchAgents/`，`launchctl bootstrap gui/$(id -u) <那个文件>`。看 `logs/push.log` 和 `state/status-dryrun.json`，结果应是 `dry_run_ok`，GitHub 上不会多任何提交。看完 `launchctl bootout gui/$(id -u)/com.jake.digitalbrain-imac-push.dryrun`，把这个文件挪走。

5. 第一次要推一批积压的改动时，可以用切换模板，只推清单里那几篇，做法同第 4 步。跑完同样卸掉。没有积压就跳过。

6. 装正式任务：把 `rendered/com.jake.digitalbrain-imac-push.plist` 放进 `~/Library/LaunchAgents/`，核对 sha256，然后：

   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jake.digitalbrain-imac-push.plist
   ```

   等第一轮跑完，看 `logs/push.log` 和 `state/status.json`：没有「要人看」、没有错误。

7. 装之前和装之后都核对交易任务的状态和文件指纹，确认没被碰过。

## 怎么回退

停掉推送，不删任何东西：

```bash
launchctl bootout gui/$(id -u)/com.jake.digitalbrain-imac-push
mkdir -p ~/Library/LaunchAgents/disabled
mv ~/Library/LaunchAgents/com.jake.digitalbrain-imac-push.plist \
   ~/Library/LaunchAgents/disabled/com.jake.digitalbrain-imac-push.plist.disabled-$(date +%Y%m%d)
launchctl list | grep digitalbrain-imac-push || echo 已经停了
```

- 停了以后，那三个文件夹里的新内容就不会上 GitHub，直到重新装上。笔记库本身不受影响，拉取照常。
- 推送目录（脚本、克隆、日志、状态）留着不动，方便恢复和查原因。
- 恢复：把文件挪回 `~/Library/LaunchAgents/com.jake.digitalbrain-imac-push.plist`，再跑一次第 6 步的 `launchctl bootstrap`。
- 回退时**不要**把 MacBook 上的旧任务装回去（见下一节）。

## MacBook 上的旧任务保持停用

- MacBook 上的 `com.jake.intake-source-push` 和 `com.jake.digitalbrain-reconcile` 2026-11-01 已停掉，设置文件在 MacBook 的 `~/Library/LaunchAgents/disabled/`。它们保持停用，不要挪回去，也不要拿它们当这个任务的备用。
- 原因：同时有两台电脑往笔记库或 GitHub 写，会生成「xxx 2」副本、互相挡住快进。现在的前提是「只有一台推」。
- 仓库里的 `launchd/com.jake.intake-source-push.plist` 和 `scripts/push_intake_sources.sh` 也已标了「停用，留作备份，不要再装」。

## 故意没放进来的

- `pull_to_icloud.py`（没用上的后台拉取脚本）和 `b1.py`（10-31 装拉取时的一次性脚本）：都没在跑，放进来会让人误会该装。
- MacBook 上 10-09 没提交的那批代码：对应的任务都停了，不进 main，只另做一份存档。
- 切换用的路径清单：内容是个人笔记的路径，只在那台 Mac 上。

## 本机部署示例（Jake 的机器）

下面这些只适用于 Jake 自己那套机器，换人部署按自己的改：

- 推送方是 iMac（HermesdeiMac），用户 `hermes`。各占位符的实际值见 `deploy.example.env`。
- 推送目录 `/Users/hermes/digitalbrain-pusher`；日志 `/Users/hermes/digitalbrain-pusher/logs/push.log`；状态文件 `/Users/hermes/digitalbrain-pusher/state/status.json`。
- 跑脚本的 Python 是备份任务那份专用 Python（`com.jake.digitalbrain-backup.python`，自签），完全磁盘访问权限只给了它。
- 推送凭证：iMac 上的 `gh` 以 `jakeguo117` 登录，存在钥匙串里。
- 笔记仓是 `jakeguo117/obsidian-digitalbrain` 的 main。提交作者是 `Jake (iMac pusher)`，邮箱用这个 GitHub 账号的 noreply 地址。这两个值目前写在脚本开头的 `COMMIT_NAME`、`COMMIT_EMAIL` 里；为了让仓库里这份和 iMac 上正在跑的逐字节一样，这次没改。以后改脚本时再把它们挪成参数。
- 装好的三份设置文件的 sha256（用 `deploy.example.env` 填模板可以原样得到）：
  - 正式 `8c500cc1f6ebf8c2366756e362efc08447731e1759b0ee187dfa93b0381045b0`
  - 演练 `6bc8071a96986c658d70822298faeec2b36cb7a96045e2ab8cbaf7eba5e06c2f`
  - 切换 `7ab711bf81856bd1a414627ec9a9e9c4ae590f7718c1c8b9fd4261babff68c50`
