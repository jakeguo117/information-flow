#!/bin/bash
# Install the dedicated interpreter, marker, and LaunchAgent plist.
# Does not load the agent.
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
exec "$PY" "$ROOT/digitalbrain_backup.py" --config "${DIGITALBRAIN_BACKUP_CONFIG:-$ROOT/config.json}" install "$@"
