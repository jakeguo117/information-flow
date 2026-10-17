#!/bin/bash
# Force a placeholder failure: one alert, and older snapshots stay put.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export GIT_TERMINAL_PROMPT=0
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

VOL="$WORK/mnt"
BACKUP="$VOL/DigitalBrain-Backups"
mkdir -p "$BACKUP/vault/daily/1999-01-01" "$BACKUP/git/daily"
echo keep-me > "$BACKUP/vault/daily/1999-01-01/keep.txt"
echo old-bundle > "$BACKUP/git/daily/1999-01-01.bundle"
printf '%s\n' digitalbrain-backup-target > "$BACKUP/.backup-target"

VAULT="$WORK/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
mkdir -p "$VAULT/notes"
echo note > "$VAULT/notes/hello.md"
echo stub > "$VAULT/notes/stub.md.icloud"

SRC="$WORK/src"
git init -b main "$SRC"
git -C "$SRC" config user.email test@example.com
git -C "$SRC" config user.name test
echo hello > "$SRC/hello.txt"
git -C "$SRC" add hello.txt
git -C "$SRC" commit -m init
git clone --bare "$SRC" "$WORK/origin.git"

HOMELOG="$WORK/home.log"
HERMES_LOG="$WORK/hermes.log"
touch "$HERMES_LOG"
printf '/dev/disk3s1 %s apfs rw\n' "$VOL" > "$WORK/mounts"
cat > "$WORK/diskutil" << EOF
#!/bin/bash
if [[ "\${1:-}" != "info" ]]; then exit 2; fi
if [[ "\${2:-}" == "$VOL" ]]; then
  printf 'Volume Name: Disk\nMount Point: %s\nMounted: Yes\n' "\$2"
  exit 0
fi
echo "Mounted: No"
echo "Mount Point: Not applicable"
exit 1
EOF
cat > "$WORK/hermes" << EOF
#!/bin/bash
printf '%s\n' "\$*" >> "$HERMES_LOG"
exit 0
EOF
chmod +x "$WORK/diskutil" "$WORK/hermes"

export VOL VAULT HOMELOG WORK
export BARE="$WORK/origin.git"
export DISKUTIL="$WORK/diskutil"
export HERMES="$WORK/hermes"
export CFG="$WORK/config.json"
python3 - << 'PY'
import json, os
cfg = {
    "volume": os.environ["VOL"],
    "backup_folder": "DigitalBrain-Backups",
    "github_repo": "jakeguo117/obsidian-digitalbrain",
    "github_remote": os.environ["BARE"],
    "git_branch": "main",
    "vault_path": os.environ["VAULT"],
    "retention": {"weekly": 8, "monthly": 12},
    "discord_channel_id": "123",
    "hermes_command": [
        os.environ["HERMES"], "send", "--to", "discord:{channel_id}",
        "--quiet", "--subject", "{subject}", "{message}",
    ],
    "disk_log_name": "digitalbrain-backup.log",
    "home_log": os.environ["HOMELOG"],
    "timezone": "Asia/Shanghai",
    "read_timeout_seconds": 30,
    "mount_table": os.environ["WORK"] + "/mounts",
    "diskutil_bin": os.environ["DISKUTIL"],
}
open(os.environ["CFG"], "w").write(json.dumps(cfg))
PY

export DIGITALBRAIN_BACKUP_NOW="2026-10-13T03:30:00+08:00"
set +e
python3 "$ROOT/digitalbrain_backup.py" --config "$CFG" backup
rc=$?
set -e
[[ "$rc" -ne 0 ]]
python3 - "$BACKUP/status.json" << 'PY'
import json, sys
status = json.load(open(sys.argv[1]))
assert status["result"] == "failed"
for key in ("time", "result", "sizes", "head_sha", "errors"):
    assert key in status
assert status["errors"]
assert any("placeholder" in item or "icloud" in item or "stub.md.icloud" in item for item in status["errors"])
assert status["prune"]["ran"] is False
PY
[[ "$(grep -c . "$HERMES_LOG")" -eq 1 ]]
grep -q send "$HERMES_LOG"
grep -q 'discord:' "$HERMES_LOG"
[[ "$(cat "$BACKUP/vault/daily/1999-01-01/keep.txt")" == "keep-me" ]]
[[ "$(cat "$BACKUP/git/daily/1999-01-01.bundle")" == "old-bundle" ]]
[[ ! -e "$BACKUP/vault/daily/2026-10-13" ]]
echo "PASS failure alert sent once and nothing was pruned"
