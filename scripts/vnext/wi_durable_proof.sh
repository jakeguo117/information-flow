#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Merge proof comes from persisted records for the declared project.
# Caller-supplied workflow inputs are not proof.

set -u

root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$root" || ! -f "$root/PROJECT_STATE.md" ]]; then
  echo "durable proof: project state is missing" >&2
  exit 1
fi

change_field="$(awk -F': ' '$1 == "Active Change" { print substr($0, index($0, ": ") + 2); exit }' "$root/PROJECT_STATE.md")"
change_dir="${change_field%% *}"
change_dir="${change_dir%.}"
if [[ -z "$change_dir" || "$change_dir" == none ]]; then
  echo "durable proof: no active change" >&2
  exit 1
fi

head_sha="$(git -C "$root" rev-parse HEAD)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
review_token="$(bash "$here/wi_review_route.sh" review)"
verification_token="$(bash "$here/wi_review_route.sh" verification)"
if [[ "$review_token" == content_pass && "$verification_token" == content_verified ]]; then
  content_sha="$(awk -F': ' '$1 == "sha" { print substr($0, index($0, ": ") + 2); exit }' "$root/$change_dir/review.md")"
  echo "durable proof: evidence envelope content=${content_sha} head=${head_sha}" >&2
  echo "durable proof: reject reason=not-merge-head" >&2
  exit 1
fi
exec bash "$root/scripts/vnext/wi_merge_gate.sh" --predicate "$root/$change_dir" "$head_sha"
