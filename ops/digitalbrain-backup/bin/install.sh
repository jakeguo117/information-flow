#!/bin/bash
# Install the dedicated interpreter, marker, and LaunchAgent plist.
# Does not load the agent.
# DIGITALBRAIN_BACKUP_PYTHON is required. /usr/bin/python3 is a macOS
# xcode-select launcher shim and must not be copied for Full Disk Access.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
if [[ -z "${DIGITALBRAIN_BACKUP_PYTHON:-}" ]]; then
  echo "digitalbrain-backup install: set DIGITALBRAIN_BACKUP_PYTHON to a standalone Python. /usr/bin/python3 is a macOS launcher shim and is refused." >&2
  exit 1
fi
if [[ "$DIGITALBRAIN_BACKUP_PYTHON" == "/usr/bin/python3" || "$DIGITALBRAIN_BACKUP_PYTHON" == "/usr/bin/python3/" ]]; then
  echo "digitalbrain-backup install: refusing /usr/bin/python3; it is a launcher shim." >&2
  exit 1
fi
exec "$DIGITALBRAIN_BACKUP_PYTHON" "$ROOT/digitalbrain_backup.py" --config "${DIGITALBRAIN_BACKUP_CONFIG:-$ROOT/config.json}" install "$@"
