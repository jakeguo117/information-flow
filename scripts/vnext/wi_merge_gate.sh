#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Refuse a merge when review or verification does not name the exact head.
# A later head makes an older pass stale. This script does not merge.

set -u

field() {
  awk -F': ' -v key="$2" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$1"
}

sha40() {
  printf '%s\n' "$1" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true
}

# Canonical results are PASS and VERIFIED.
# Historical lowercase pass and verified are the same results.
# CHANGES_REQUESTED, FAILED, and MATERIAL_STOP do not pass the gate.
canon() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_merge_gate.sh --check <review.md> <verification.md> <head-sha>"
  exit 0
fi

if [[ "${1:-}" == "--predicate" ]]; then
  dir="${2:-}"
  head_sha="${3:-}"
  if [[ -z "$dir" || ! "$head_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Usage: scripts/wi_merge_gate.sh --predicate <dir> <head-sha>" >&2
    exit 2
  fi
  reject() {
    echo "merge gate: reject reason=$1" >&2
    exit 1
  }
  need() {
    if [[ ! -f "$dir/$1" ]]; then
      reject "missing-$2"
    fi
  }
  need review.md review
  need verification.md verification
  need change.md approval
  need ci.md ci
  need ownership.md ownership
  need readback.md readback
  need identity.md identity
  review_sha="$(sha40 "$(field "$dir/review.md" sha)")"
  review_result="$(field "$dir/review.md" result)"
  review_role="$(field "$dir/review.md" role)"
  verification_sha="$(sha40 "$(field "$dir/verification.md" sha)")"
  verification_result="$(field "$dir/verification.md" result)"
  verification_role="$(field "$dir/verification.md" role)"
  decision="$(field "$dir/change.md" "Jake decision")"
  content="$(sha40 "$(field "$dir/change.md" "Approved content")")"
  ci_sha="$(sha40 "$(field "$dir/ci.md" sha)")"
  ci_result="$(field "$dir/ci.md" result)"
  ownership_result="$(field "$dir/ownership.md" result)"
  readback="$(sha40 "$(field "$dir/readback.md" remote_sha)")"
  repository="$(field "$dir/identity.md" repository)"
  change_id="$(field "$dir/identity.md" change_id)"
  target_branch="$(field "$dir/identity.md" target_branch)"
  protocol_commit="$(sha40 "$(field "$dir/identity.md" protocol_commit)")"
  if [[ "$review_sha" != "$head_sha" ]]; then
    reject stale-review
  fi
  if [[ "$(canon "$review_result")" != "pass" || "$review_role" != "reviewer" ]]; then
    reject review-result
  fi
  if [[ "$verification_sha" != "$head_sha" ]]; then
    reject stale-verification
  fi
  if [[ "$(canon "$verification_result")" != "verified" || "$verification_role" != "verifier" ]]; then
    reject verification-result
  fi
  if [[ "$review_role" == "$verification_role" ]]; then
    reject same-role
  fi
  if [[ -z "$decision" || "$decision" == "none" || -z "$content" ]]; then
    reject approval-decision
  fi
  if [[ "$ci_sha" != "$head_sha" || "$ci_result" != "pass" ]]; then
    reject ci-result
  fi
  if [[ "$ownership_result" != "pass" ]]; then
    reject ownership
  fi
  if [[ "$readback" != "$head_sha" ]]; then
    reject stale-readback
  fi
  if [[ -z "$repository" || -z "$change_id" || -z "$target_branch" || ! "$protocol_commit" =~ ^[0-9a-f]{40}$ ]]; then
    reject identity
  fi
  echo "merge gate: ok repository=${repository} change=${change_id} head=${head_sha} approval=${content} review=${review_sha} verification=${verification_sha} ci=${ci_sha} readback=${readback}"
  exit 0
fi

if [[ "${1:-}" != "--check" || -z "${2:-}" || -z "${3:-}" || -z "${4:-}" ]]; then
  echo "Usage: scripts/wi_merge_gate.sh --check <review.md> <verification.md> <head-sha>" >&2
  exit 2
fi

review="$2"
verification="$3"
head_sha="$4"

if [[ ! "$head_sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "merge gate: head is not an exact SHA" >&2
  exit 1
fi

review_sha="$(sha40 "$(field "$review" sha)")"
review_result="$(field "$review" result)"
verification_sha="$(sha40 "$(field "$verification" sha)")"
verification_result="$(field "$verification" result)"

if [[ "$review_sha" != "$head_sha" || "$verification_sha" != "$head_sha" ]]; then
  echo "merge gate: stale evidence review=${review_sha:-missing} verification=${verification_sha:-missing} head=${head_sha}" >&2
  exit 1
fi

if [[ "$(canon "$review_result")" != "pass" || "$(canon "$verification_result")" != "verified" ]]; then
  echo "merge gate: current head is not passing review=${review_result:-missing} verification=${verification_result:-missing}" >&2
  exit 1
fi

echo "merge gate: ok head=${head_sha}"
exit 0
