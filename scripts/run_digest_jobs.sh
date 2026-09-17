#!/bin/sh
# Intake only: likes + weekly intake.md append + Briefing refresh. Does not run journal.
set -e
PY="${PYTHON3:-python3}"
DIR="${HOME}/plugins/information-flow/scripts"
"$PY" "$DIR/youtube_likes.py"
"$PY" "$DIR/daily_digest.py"
"$PY" "$DIR/weekly_rollup.py"
