#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Read-only projection check.
# Linear is a human projection. This script does not update Linear and does not change Git.

set -u

if [[ "${1:-}" != "--check" || -z "${2:-}" ]]; then
  echo "Usage: scripts/wi_projection_check.sh --check <projection.md>" >&2
  exit 2
fi

file="$2"
if [[ ! -f "$file" ]]; then
  echo "projection: missing ${file}" >&2
  exit 1
fi

first="$(awk 'NF { print; exit }' "$file")"
if printf '%s\n' "$first" | grep -qE '^[0-9a-f]{40}$'; then
  echo "projection: the headline is a SHA" >&2
  exit 1
fi

for label in "Objective:" "Phase:" "Completed:" "Blocker:" "Next action:" "Jake decision needed:"; do
  if ! grep -q "^${label}" "$file"; then
    echo "projection: missing ${label}" >&2
    exit 1
  fi
done

echo "projection: ok"
exit 0
