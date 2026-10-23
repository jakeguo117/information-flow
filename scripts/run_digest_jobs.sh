#!/bin/sh
# Intake only: likes + weekly intake.md append + Briefing refresh. Does not run journal.
# Vault comes from INFOFLOW_VAULT_ROOT or config.json. No personal default path.
set -eu
PY="${PYTHON3:-python3}"
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
VAULT=$("$PY" "$DIR/infoflow_config.py" get vault_root)
"$PY" "$DIR/youtube_likes.py" --vault "$VAULT"
"$PY" "$DIR/daily_digest.py" --vault "$VAULT"
"$PY" "$DIR/weekly_rollup.py" --vault "$VAULT"
