#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Read-only converge checklist.
# speckit.converge only appends tasks. It does not record a new baseline.
# The header may change only after this checklist exits 0.

set -u

if [[ "${1:-}" != "--check" || -z "${2:-}" ]]; then
  echo "Usage: scripts/wi_converge_check.sh --check <record-directory>" >&2
  exit 2
fi

dir="$2"
review="$dir/review.md"
verification="$dir/verification.md"
convergence="$dir/convergence.md"

field() {
  local file="$1"
  local key="$2"
  awk -F': ' -v key="$key" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$file"
}

sha40() {
  printf '%s\n' "$1" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true
}

for file in "$review" "$verification" "$convergence"; do
  if [[ ! -f "$file" ]]; then
    echo "converge: missing ${file}" >&2
    echo "header update blocked" >&2
    exit 1
  fi
done

review_sha="$(sha40 "$(field "$review" sha)")"
verification_sha="$(sha40 "$(field "$verification" sha)")"
remote_sha="$(sha40 "$(field "$convergence" remote_sha)")"
convergence_review="$(sha40 "$(field "$convergence" review_sha)")"
convergence_verification="$(sha40 "$(field "$convergence" verification_sha)")"

if [[ -z "$review_sha" || -z "$verification_sha" || "$review_sha" != "$verification_sha" ]]; then
  echo "converge: review SHA ${review_sha:-missing} does not match verification SHA ${verification_sha:-missing}" >&2
  echo "header update blocked" >&2
  exit 1
fi

if [[ -z "$remote_sha" ]]; then
  echo "converge: convergence.md has no remote SHA" >&2
  echo "header update blocked" >&2
  exit 1
fi

if [[ "$convergence_review" != "$review_sha" || "$convergence_verification" != "$verification_sha" ]]; then
  echo "converge: convergence.md SHAs do not match the review and verification records" >&2
  echo "header update blocked" >&2
  exit 1
fi

if grep -q '^intent:' "$convergence"; then
  intent="$(field "$convergence" intent)"
  if [[ -z "$intent" || "$intent" == none ]]; then
    echo "converge: approved intent is missing" >&2
    echo "header update blocked" >&2
    exit 1
  fi
fi

ancestry="$(field "$convergence" ancestry_tip)"
if [[ -n "$ancestry" ]]; then
  if ! git merge-base --is-ancestor "$remote_sha" "$ancestry" >/dev/null 2>&1; then
    echo "converge: remote SHA is not an ancestor of ${ancestry}" >&2
    echo "header update blocked" >&2
    exit 1
  fi
fi

echo "converge: ok remote_sha=${remote_sha} review_sha=${review_sha}"
echo "speckit.converge appends tasks only"
echo "header update allowed"
exit 0
