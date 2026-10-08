#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Compare the evaluated head with the head about to be mutated.
# A mismatch rejects. This script does not merge.

set -u

expected=""
actual=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expected)
      expected="${2:-}"
      shift 2
      ;;
    --actual)
      actual="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: scripts/wi_merge_if_head.sh --expected SHA --actual SHA" >&2
      exit 2
      ;;
  esac
done

if [[ ! "$expected" =~ ^[0-9a-f]{40}$ || ! "$actual" =~ ^[0-9a-f]{40}$ ]]; then
  echo "merge: head is not an exact SHA" >&2
  exit 2
fi

if [[ "$expected" != "$actual" ]]; then
  echo "merge: reject reason=raced-head expected=${expected} actual=${actual}" >&2
  exit 1
fi

echo "merge: head-matches expected=${expected}"
exit 0
