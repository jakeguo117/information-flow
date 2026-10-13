#!/bin/bash
# Show that an unmounted volume is not written, and one alert is sent.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

VOL="$WORK/Volumes/Disk"
mkdir -p "$VOL"
echo decoy > "$VOL/do-not-touch.txt"
HOMELOG="$WORK/home.log"
HERMES_LOG="$WORK/hermes.log"
touch "$HERMES_LOG"
: > "$WORK/mounts"

cat > "$WORK/diskutil" << 'EOF'
#!/bin/bash
if [[ "${1:-}" != "info" ]]; then exit 2; fi
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

VAULT="$WORK/vault"
mkdir -p "$VAULT"
export VOL HOMELOG HERMES_LOG WORK VAULT
export DISKUTIL="$WORK/diskutil"
export HERMES="$WORK/hermes"
export CFG="$WORK/config.json"
python3 - << 'PY'
import json, os
cfg = {
    "volume": os.environ["VOL"],
    "backup_folder": "DigitalBrain-Backups",
    "github_repo": "jakeguo117/obsidian-digitalbrain",
    "github_remote": "https://github.com/jakeguo117/obsidian-digitalbrain.git",
    "git_branch": "main",
    "vault_path": os.environ["VAULT"],
    "retention": {"daily": 14, "weekly": 8, "monthly": 12},
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

set +e
python3 "$ROOT/digitalbrain_backup.py" --config "$CFG" backup
rc=$?
set -e
[[ "$rc" -ne 0 ]]
[[ "$(ls -A "$VOL")" == "do-not-touch.txt" ]]
[[ ! -e "$VOL/DigitalBrain-Backups" ]]
[[ ! -e "$VOL/status.json" ]]
grep -q "backup target unavailable" "$HOMELOG"
[[ "$(grep -c . "$HERMES_LOG")" -eq 1 ]]
grep -q send "$HERMES_LOG"
grep -q 'discord:' "$HERMES_LOG"
echo "PASS unmounted volume was not written"
