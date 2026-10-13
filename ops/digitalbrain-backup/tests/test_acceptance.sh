#!/bin/bash
# Syntax-check the shell entrypoints and run the two manual demos.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for script in "$ROOT"/bin/*.sh; do
  bash -n "$script"
done
if grep -n launchctl "$ROOT"/bin/* "$ROOT"/digitalbrain_backup.py "$ROOT"/launchd/*; then
  echo "launchctl must stay out of the program, scripts, and plist" >&2
  exit 1
fi
if grep -n obsidian-vault-sync "$ROOT"/bin/* "$ROOT"/digitalbrain_backup.py "$ROOT"/launchd/*; then
  echo "obsidian-vault-sync must stay out of the program, scripts, and plist" >&2
  exit 1
fi
bash "$ROOT/bin/demo-unmounted.sh"
bash "$ROOT/bin/demo-failure.sh"
