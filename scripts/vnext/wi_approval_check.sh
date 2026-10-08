#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Block a requirement-semantic change whose Jake decision is blank.
# A modified line that starts with none, and a repair record, do not require a new decision.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_approval_check.sh --check <change.md>"
  exit 0
fi

if [[ "${1:-}" != "--check" || -z "${2:-}" || ! -f "${2:-}" ]]; then
  echo "Usage: scripts/wi_approval_check.sh --check <change.md>" >&2
  exit 2
fi

file="$2"
added="$(awk -F': ' '$1 == "ADDED" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
modified="$(awk -F': ' '$1 == "MODIFIED" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
removed="$(awk -F': ' '$1 == "REMOVED" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
decision="$(awk -F': ' '$1 == "Jake decision" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
status="$(awk -F': ' '$1 == "Status" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
content="$(awk -F': ' '$1 == "Approved content" { print substr($0, index($0, ": ") + 2); exit }' "$file")"

if [[ "$status" == *"Repair"* ]]; then
  echo "approval: ok routine-or-empty"
  exit 0
fi

material=0
[[ -z "$added" || "$added" == none* ]] || material=1
[[ -z "$modified" || "$modified" == none* ]] || material=1
[[ -z "$removed" || "$removed" == none* ]] || material=1
if [[ "$material" -eq 0 ]]; then
  echo "approval: ok routine-or-empty"
  exit 0
fi

if [[ -z "$decision" || "$decision" == *"blank until decided"* || "$decision" == "none" ]]; then
  echo "approval: requirement change is blocked until Jake decides" >&2
  exit 1
fi

if [[ "$material" -eq 1 && ! "$content" =~ [0-9a-f]{40} ]]; then
  echo "approval: material change needs an approved content SHA" >&2
  exit 1
fi

echo "approval: ok decision-recorded"
exit 0
