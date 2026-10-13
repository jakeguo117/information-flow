#!/bin/bash
# Remove the LaunchAgent plist only. Backups and the dedicated interpreter stay.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
if [[ -n "${DIGITALBRAIN_BACKUP_PYTHON:-}" ]]; then
  PY="$DIGITALBRAIN_BACKUP_PYTHON"
elif [[ -x /usr/bin/python3 ]]; then
  PY=/usr/bin/python3
else
  PY="$(command -v python3)"
fi
exec "$PY" "$ROOT/digitalbrain_backup.py" uninstall "$@"
