#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Persist repair identity and stop at the earlier approved bound.
# Two consecutive equivalent failures stop. The total budget also stops.
# This script does not ask Jake to carry the failure.

set -u

if [[ "${1:-}" != "--record" || -z "${2:-}" || -z "${3:-}" ]]; then
  echo "Usage: scripts/wi_retry_budget.sh --record <handoff.md> <failure-id>" >&2
  exit 2
fi

file="$2"
failure="$3"
if [[ ! -f "$file" || -z "$failure" ]]; then
  echo "retry: handoff or failure id is missing" >&2
  exit 2
fi

field() {
  awk -F': ' -v key="$2" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$1"
}

budget="$(field "$file" repair_budget)"
count="$(field "$file" repair_count)"
identity="$(field "$file" failure_identity)"
streak="$(field "$file" failure_streak)"
budget="${budget:-3}"
count="${count:-0}"
streak="${streak:-0}"

if [[ "$identity" == "$failure" ]]; then
  streak=$((streak + 1))
else
  identity="$failure"
  streak=1
fi
count=$((count + 1))

update() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}: " "$file"; then
    awk -v key="$key" -v value="$value" '
      BEGIN { FS = OFS = "" }
      index($0, key ": ") == 1 { print key ": " value; next }
      { print }
    ' "$file" >"${file}.tmp"
    mv "${file}.tmp" "$file"
  else
    printf '%s: %s\n' "$key" "$value" >>"$file"
  fi
}

update repair_count "$count"
update failure_identity "$identity"
update failure_streak "$streak"
update repair_budget "$budget"

if [[ "$streak" -ge 2 || "$count" -ge "$budget" ]]; then
  echo "STOP — JAKE DECISION REQUIRED"
  echo "retry: reject reason=budget-exhausted count=${count} streak=${streak} identity=${identity}" >&2
  exit 16
fi

echo "retry: ok count=${count} streak=${streak} identity=${identity}"
exit 0
