#!/bin/bash
# Run one DigitalBrain backup or restore-test. Does not load a LaunchAgent.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
if [[ -n "${DIGITALBRAIN_BACKUP_PYTHON:-}" ]]; then
  PY="$DIGITALBRAIN_BACKUP_PYTHON"
elif [[ -x "$HOME/Library/Application Support/digitalbrain-backup/python3-digitalbrain-backup" ]]; then
  PY="$HOME/Library/Application Support/digitalbrain-backup/python3-digitalbrain-backup"
elif [[ -x /usr/bin/python3 ]]; then
  PY=/usr/bin/python3
else
  PY="$(command -v python3)"
fi
if [[ $# -eq 0 ]]; then
  set -- backup
fi
exec "$PY" "$ROOT/digitalbrain_backup.py" --config "${DIGITALBRAIN_BACKUP_CONFIG:-$ROOT/config.json}" "$@"
