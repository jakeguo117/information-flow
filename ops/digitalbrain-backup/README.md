# DigitalBrain weekly backup

Weekly copy of the DigitalBrain vault onto the iMac external disk. launchd runs it on Sundays at 03:30 Asia/Shanghai.

Two sources:

- Git is primary. The GitHub repo `jakeguo117/obsidian-digitalbrain` is cloned and fetched into `<volume>/DigitalBrain-Backups/git/mirror.git`. That mirror is outside iCloud. This program never runs git against the vault and never reads the vault `.git` entry. On the iCloud copy that entry is a not-downloaded gitdir pointer, and reading it hangs.
- The Obsidian vault folder is copied as files. The default path is `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain` (often `/Users/jake/...`). Confirm `vault_path` on the iMac before the first real run.

The disk is not encrypted. The default volume is `/Volumes/Disk` and the folder is `DigitalBrain-Backups`. Both are config keys. Retention of record is 8 weekly and 12 monthly snapshots. Each run also publishes one dated snapshot under `vault/daily` and `git/daily`. That daily copy is staging: after the weekly and monthly snapshots are built, only the newest daily snapshot is kept, because the Sunday restore-test reads it.

Each run writes `status.json` (time, result, sizes, HEAD sha, errors). Logs go to `DigitalBrain-Backups/digitalbrain-backup.log` on the backup disk and to `~/Library/Logs/digitalbrain-backup.log`. On failure, Hermes sends one Discord message. Hermes only notifies. The backup work is this program, started by launchd.

A failed run does not publish that run's snapshot and does not delete or rotate older ones. An unreadable vault, an iCloud placeholder (`.icloud` or dataless), or a vault read that exceeds `read_timeout_seconds` is a failure (`result` is `failed`), alerts, and leaves old snapshots in place. Before any source file is opened, the run checks the macOS dataless flag (`st_flags` `SF_DATALESS`, `0x40000000`) and fails with an alert that names the path. The log line `debug opening <path>` is written first.

The whole run has a watchdog, `run_timeout_seconds` (default 60 minutes). The parent process enforces that deadline and `SIGKILL`s the backup child, including child git processes, even when the child is blocked inside `open()`. `result` is `timeout`, and Hermes alerts even when that overall deadline is what stops the run. Disk status and logs are written only after the volume is mounted and the marker file is valid. External-disk reads, writes, the mount check, the marker, the lock file, git mirror setup, the vault copy's incoming directory, manifest write and read-back, and the restore-test snapshot copy each run through one timeout (`disk_io_timeout_seconds`, default 30 seconds). Publishing snapshots and pruning them use a separate longer timeout (`snapshot_timeout_seconds`, default 3600 seconds). A failed or timed-out disk write, including when `status.json` cannot be replaced, still sends the alert and writes `digitalbrain-backup-timeout-status.json` next to the home log. Nothing is created on an unmounted volume.

The Sunday 03:30 run restores the latest bundle and vault snapshot into a temp directory and checks `git fsck`, HEAD, and the sha256 manifest.

## Schedule

`launchd/com.jake.digitalbrain-backup.plist` uses `StartCalendarInterval` with `Weekday` 0 (Sunday), `Hour` 3, and `Minute` 30. The job runs on Sundays only. That clock is local time. launchd has no timezone field, so the iMac timezone must be Asia/Shanghai. The plist ships with placeholders. `install` fills them. Install does not load the agent.

## Full Disk Access

launchd on the iMac gets `Operation not permitted` when it reads `~/Library/Mobile Documents/iCloud~md~obsidian/...`. macOS privacy (TCC) blocks that read until the program that opens the files has Full Disk Access.

Grant it only to the backup's dedicated interpreter:

`~/Library/Application Support/digitalbrain-backup/python3-digitalbrain-backup`

Jake clicks this on the iMac himself:

1. System Settings → Privacy & Security → Full Disk Access.
2. Click `+`. If the file picker hides `~/Library`, press Cmd-Shift-G and paste the path above.
3. Enable only `python3-digitalbrain-backup`.

The LaunchAgent's first program argument is that binary. The vault reader is a child of the same binary (`sys.executable`), so the grant covers the backup and nothing else.

Do not grant Full Disk Access to `/usr/bin/python3`, `/bin/bash`, Terminal, or anything used by `com.jake.obsidian-vault-sync`. This package does not change that job, and its binary must not be this dedicated interpreter.

`DIGITALBRAIN_BACKUP_PYTHON` is required. There is no default. The binary that works when copied is a Homebrew Cellar framework `python3.x`, for example `/opt/homebrew/Cellar/python@3.12/3.12.x/Frameworks/Python.framework/Versions/3.12/bin/python3.12`. Copies of python-build-standalone crash. `/usr/bin/python3` on macOS is an xcode-select launcher shim: a copy may not run, or it may re-exec another Python, so Full Disk Access would be granted to the wrong binary. Install refuses that path and any launcher whose `sys.executable` does not match the file you named. After copying, install runs the copy and aborts unless `sys.executable` equals the copied path. On macOS it ad-hoc signs that copy with identifier `com.jake.digitalbrain-backup.python`. Grant Full Disk Access to the copy, not to the original system Python. If `brew upgrade` or `brew cleanup` removes that Cellar version, the copy breaks: run install again and re-grant Full Disk Access to the new `python3-digitalbrain-backup`.

## Install

From this directory, on the iMac, with `/Volumes/Disk` mounted:

```bash
cp config.example.json config.json
# Edit vault_path and discord_channel_id. Confirm the Mac timezone is Asia/Shanghai.
# hermes must be on PATH for the agent (the plist PATH includes ~/.local/bin and Homebrew).
# Homebrew Cellar framework python3.x. Not /usr/bin/python3, and not a
# python-build-standalone build (those copies crash).
export DIGITALBRAIN_BACKUP_PYTHON=/opt/homebrew/Cellar/python@3.12/3.12.x/Frameworks/Python.framework/Versions/3.12/bin/python3.12
bin/install.sh
```

`install.sh` copies that interpreter, checks the copy reports itself as `sys.executable`, writes `DigitalBrain-Backups/.backup-target` after the volume is proven mounted, and writes `~/Library/LaunchAgents/com.jake.digitalbrain-backup.plist`. It does not load the agent. If `DIGITALBRAIN_BACKUP_PYTHON` is unset, names `/usr/bin/python3`, names a launcher shim, or the copy's `sys.executable` is not the copied path, install aborts and does not write the plist.

After Full Disk Access is on that interpreter only, load it yourself:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jake.digitalbrain-backup.plist
```

Remove the plist only (backups and the interpreter stay):

```bash
bin/uninstall.sh
```

## Config

`config.example.json` lists every key. `discord_channel_id` is still `REPLACE_WITH_DISCORD_CHANNEL_ID` until you set the existing Discord channel. `hermes_command` is an argv list, not a shell string. `{channel_id}`, `{subject}`, and `{message}` are replaced without a shell.

`run_timeout_seconds` defaults to 3600. `disk_io_timeout_seconds` defaults to 30. `snapshot_timeout_seconds` defaults to 3600 and applies to snapshot publish and prune. Optional test keys, not in the example: `mount_table`, `diskutil_bin`, `stat_bin`, `ls_bin`.

## First real backup and restore

```bash
bin/backup.sh
bin/backup.sh restore-test
```

`backup.sh` defaults to `backup`. `restore-test` restores the latest dated bundle and vault snapshot, prints the raw `git fsck`, `git bundle verify`, HEAD, and manifest output, and does not rewrite `status.json` when the check passes.

## Manual demos

Unmounted disk (acceptance: write nothing, alert once):

```bash
bin/demo-unmounted.sh
```

Failure (acceptance: one alert, old snapshots kept):

```bash
bin/demo-failure.sh
```

## What a run checks

- The volume is a real mount. `diskutil info` saying it is not mounted is a veto. A path directly under `/Volumes` that is not a mount point is refused even if other checks are positive. The marker file `DigitalBrain-Backups/.backup-target` must already exist (install creates it). The backup never creates the volume directory.
- Git clone, fetch, fsck, bundle, ls-remote, and rev-parse run only against the mirror on the backup disk or a restore temp dir. Backed-up HEAD must equal GitHub `main`. The bundle must pass `git bundle verify`.
- Vault file bytes are hashed with sha256 and checked after the copy.
- Pruning deletes only inside `DigitalBrain-Backups`, and only after a fully successful run, including the Sunday restore test. Weekly and monthly retention follow the config. The dated daily snapshot is staging and only the newest one is kept. Symlinks and `..` are refused. A sibling such as `DigitalBrain-Backups-evil` is not a backup root.
- A run still going after `run_timeout_seconds` is killed. `diskutil` exiting non-zero, timing out, or omitting `Mounted: Yes` means the volume is not mounted, and nothing is written on it.
