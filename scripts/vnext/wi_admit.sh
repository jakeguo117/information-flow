#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Admit implementation only from persisted approval, scope, and base identity.
# Chat text alone is not approval. This script does not implement.

set -u

if [[ "${1:-}" != "--check" || -z "${2:-}" || -z "${3:-}" ]]; then
  echo "Usage: scripts/wi_admit.sh --check <change-dir> <PROJECT_STATE.md>" >&2
  exit 2
fi

change_dir="$2"
state_file="$3"
change_file="${change_dir}/change.md"
plan_file="${change_dir}/plan.md"
tasks_file="${change_dir}/tasks.md"
handoff_file="${change_dir}/handoff.md"

field() {
  awk -F': ' -v key="$2" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$1"
}

sha40() {
  printf '%s\n' "$1" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true
}

for required in "$change_file" "$plan_file" "$tasks_file" "$handoff_file" "$state_file"; do
  if [[ ! -s "$required" ]]; then
    echo "admit: reject reason=missing-record file=${required}" >&2
    exit 1
  fi
done

decision="$(field "$change_file" "Jake decision")"
content="$(sha40 "$(field "$change_file" "Approved content")")"
if [[ "$decision" == *chat* && -z "$content" ]]; then
  echo "admit: reject reason=chat-only" >&2
  exit 1
fi

if ! bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wi_approval_check.sh" --check "$change_file"; then
  echo "admit: reject reason=approval" >&2
  exit 1
fi
if [[ ! "$content" =~ ^[0-9a-f]{40}$ ]]; then
  echo "admit: reject reason=approval-identity" >&2
  exit 1
fi

spec_record="$(field "$change_file" "Spec path")"
if [[ -z "$spec_record" || "$spec_record" == none* ]]; then
  echo "admit: reject reason=wrong-delta" >&2
  exit 1
fi
if ! git cat-file -e "${content}:${spec_record}" >/dev/null 2>&1; then
  echo "admit: reject reason=wrong-delta" >&2
  exit 1
fi
if git show "${content}:${spec_record}" | grep -q 'Implementation: prohibited'; then
  echo "admit: reject reason=draft-prohibits-implementation" >&2
  exit 1
fi

base_expected="$(sha40 "$(field "$state_file" "Current Approved Spec")")"
base_recorded="$(sha40 "$(field "$change_file" "Base Current Approved Truth")")"
if [[ -z "$base_expected" || "$base_recorded" != "$base_expected" ]]; then
  echo "admit: reject reason=outdated-base" >&2
  exit 1
fi

permissions="$(field "$handoff_file" permissions)"
if [[ -z "$permissions" || "$permissions" == none* ]]; then
  echo "admit: reject reason=permissions" >&2
  exit 1
fi

echo "admit: ok content=${content} base=${base_recorded}"
exit 0
