#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Record a material stop without changing the approved requirement file.

set -u

if [[ "${1:-}" != "--record" || -z "${2:-}" || -z "${3:-}" ]]; then
  echo "Usage: scripts/wi_material_stop.sh --record <directory> <approved-file>" >&2
  exit 2
fi

directory="$2"
approved="$3"
if [[ ! -d "$directory" || ! -f "$approved" ]]; then
  echo "material: directory or approved file is missing" >&2
  exit 2
fi

before="$(cksum "$approved")"
cat >"${directory}/material-stop.md" <<EOF
result: STOP — JAKE DECISION REQUIRED
approved_file: ${approved}
note: The approved requirement was not changed.
EOF
after="$(cksum "$approved")"
if [[ "$before" != "$after" ]]; then
  echo "material: approved file changed" >&2
  exit 1
fi

echo "STOP — JAKE DECISION REQUIRED"
exit 16
