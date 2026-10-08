#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Read-only check. This script does not create branches, commits, or pull requests.
# Exit 0: repository, cleanliness, and PROJECT_STATE identity checks passed.
# Exit 1: the detected repository is not the repository declared by PROJECT_STATE.md.
# Exit 2: working tree is dirty.
# Exit 3: PROJECT_STATE.md is missing a required identity field.
# Exit 4: recorded implementation SHA is not an ancestor of HEAD.
# Exit 5: the captured requirements spec is missing a WI-REQ id from 001 through 030.
# Exit 6: an active change has a missing handoff field or a SHA that does not match.
# Exit 7: an active change id cannot be looked up.
# Exit 10: the authority graph is missing a required binding.
# Exit 11: an authority observation names the wrong identity.
# Exit 12: a pinned external authority revision does not match.
# Exit 14: a required authority stayed NOT_VERIFIED.

set -u

unset GIT_DIR GIT_WORK_TREE

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_preflight.sh --check"
  exit 0
fi

if [[ "${1:-}" != "--check" ]]; then
  echo "preflight: only --check is supported" >&2
  exit 3
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  echo "preflight: not a git repository" >&2
  exit 1
fi
cd "$ROOT"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTOCOL_ROOT="${WI_PROTOCOL_ROOT:-$(cd "${script_dir}/.." && pwd)}"

detect_repo() {
  if [[ -n "${WI_PREFLIGHT_REPOSITORY_DETECTED:-}" ]]; then
    printf '%s\n' "$WI_PREFLIGHT_REPOSITORY_DETECTED"
    return
  fi
  local url
  url="$(git remote get-url origin 2>/dev/null || true)"
  url="${url%.git}"
  if [[ -n "$url" ]]; then
    if [[ "$url" == git@github.com:* ]]; then
      url="${url#git@github.com:}"
    elif [[ "$url" == *github.com/* ]]; then
      url="${url#*github.com/}"
    fi
    printf '%s\n' "$url"
    return
  fi
  if [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
    printf '%s\n' "$GITHUB_REPOSITORY"
    return
  fi
  printf '\n'
}

ACTUAL_REPO="$(detect_repo)"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "preflight: dirty tree" >&2
  exit 2
fi

STATE_FILE="$ROOT/PROJECT_STATE.md"
if [[ ! -f "$STATE_FILE" ]]; then
  echo "preflight: PROJECT_STATE.md missing" >&2
  exit 3
fi

field() {
  awk -F': ' -v key="$1" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$STATE_FILE"
}

declared_repo="$(field Repository)"
if [[ -z "$declared_repo" || "$ACTUAL_REPO" != "$declared_repo" ]]; then
  echo "preflight: repository mismatch: expected ${declared_repo:-missing} got ${ACTUAL_REPO}" >&2
  exit 1
fi
if [[ -z "$(field "Target Branch")" ]]; then
  echo "preflight: Target Branch is missing" >&2
  exit 3
fi
if [[ "$(field "VNext Protocol Version")" != "v0.3.0" || "$(field "VNext Contract Version")" != "1" ]]; then
  echo "preflight: unsupported protocol contract" >&2
  exit 3
fi
protocol_commit="$(printf '%s\n' "$(field "VNext Protocol Commit")" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true)"
if [[ ! "$protocol_commit" =~ ^[0-9a-f]{40}$ ]]; then
  echo "preflight: protocol commit is missing" >&2
  exit 3
fi
if ! git -C "$PROTOCOL_ROOT" cat-file -e "${protocol_commit}:scripts/wi_bootstrap.sh" >/dev/null 2>&1; then
  echo "preflight: protocol commit does not contain the contract" >&2
  exit 3
fi
if ! git -C "$PROTOCOL_ROOT" merge-base --is-ancestor "$protocol_commit" HEAD; then
  echo "preflight: protocol commit ${protocol_commit} is not an ancestor of the protocol checkout" >&2
  exit 4
fi

phase="$(awk -F': ' '/^Project Phase: / { print $2; exit }' "$STATE_FILE")"
baseline="$(awk -F': ' '/^Current Project Baseline: / { print $2; exit }' "$STATE_FILE")"
change_id="$(awk -F': ' '/^Active Change ID: / { print $2; exit }' "$STATE_FILE")"
next_action="$(awk -F': ' '/^Next Action: / { print $2; exit }' "$STATE_FILE")"
baseline_identity="$(awk -F': ' '/^Implementation Baseline \/ Git SHA: / { print $2; exit }' "$STATE_FILE")"
sha="$(printf '%s\n' "$baseline_identity" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true)"

if [[ ! "$phase" =~ ^Phase[[:space:]]+-?[0-9]+$ ]]; then
  echo "preflight: Project Phase is missing or not a phase name" >&2
  exit 3
fi
if [[ "$baseline" == "none" ]]; then
  baseline_unenrolled=1
else
  baseline_unenrolled=0
  if [[ ! "$baseline" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "preflight: Current Project Baseline is missing or not SemVer" >&2
    exit 3
  fi
fi
if [[ "$change_id" != "none" && ! "$change_id" =~ ^WI-CHG-[0-9]{4}$ ]]; then
  echo "preflight: Active Change ID is missing" >&2
  exit 3
fi
if [[ -z "$next_action" ]]; then
  echo "preflight: Next Action is missing" >&2
  exit 3
fi
if [[ "$baseline_unenrolled" -eq 0 && ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "preflight: implementation SHA is missing" >&2
  exit 3
fi

# Phase, project baseline, change id, and SHA are different facts.
if [[ "$baseline" != none && ( "$phase" == "$baseline" || "$baseline" == "$change_id" || "$baseline" == "$sha" ) ]]; then
  echo "preflight: phase, baseline, change id, and SHA are not distinct" >&2
  exit 3
fi
if [[ "$change_id" != none && ( "$phase" == "$change_id" || "$change_id" == "$sha" ) ]]; then
  echo "preflight: phase, baseline, change id, and SHA are not distinct" >&2
  exit 3
fi
if [[ -n "$sha" && "$phase" == "$sha" ]]; then
  echo "preflight: phase, baseline, change id, and SHA are not distinct" >&2
  exit 3
fi

if [[ "$baseline_unenrolled" -eq 0 ]] && ! git merge-base --is-ancestor "$sha" HEAD; then
  echo "preflight: recorded SHA ${sha} is not an ancestor of HEAD" >&2
  exit 4
fi

spec_field="$(field "Current Approved Spec")"
workflow_state="$(field "Workflow State")"
if [[ "$spec_field" == none || "$spec_field" == none\ * ]]; then
  if [[ "$workflow_state" == "Implement" || "$baseline_unenrolled" -eq 0 ]]; then
    echo "preflight: implementation blocked until an approved spec exists" >&2
    exit 3
  fi
  SPEC_FILE=""
else
  SPEC_FILE="$ROOT/${spec_field%% *}"
fi
if [[ -n "$SPEC_FILE" && ! -f "$SPEC_FILE" ]]; then
  echo "preflight: requirements spec missing" >&2
  exit 5
fi
if [[ -n "$SPEC_FILE" ]]; then
  spec_missing=0
  req_n=1
  while [[ "$req_n" -le 30 ]]; do
    req_id="$(printf 'WI-REQ-%03d' "$req_n")"
    if ! grep -q "$req_id" "$SPEC_FILE"; then
      echo "preflight: missing ${req_id}" >&2
      spec_missing=1
    fi
    req_n=$((req_n + 1))
  done
  if [[ "$spec_missing" -ne 0 ]]; then
    exit 5
  fi
fi

if [[ "$change_id" != "none" ]]; then
  handoff_file=""
  while IFS= read -r candidate; do
    if grep -q "^change_id: ${change_id}$" "$candidate"; then
      handoff_file="$candidate"
      break
    fi
  done < <(find "$ROOT/specs" -name handoff.md -type f | sort)
  if [[ -z "$handoff_file" ]]; then
    echo "preflight: active change ${change_id} has no handoff" >&2
    exit 6
  fi
  for field in change_id workflow_state owner_role base_approved_version expected_remote_sha branch pr_url workflow_run_id completed_action evidence next_bounded_action expected_proof stop_condition idempotency_keys last_verified_at; do
    field_value="$(awk -F': ' -v key="$field" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$handoff_file")"
    if [[ -z "$field_value" ]]; then
      echo "preflight: handoff missing ${field}" >&2
      exit 6
    fi
  done
  handoff_sha="$(awk -F': ' '$1 == "expected_remote_sha" { print substr($0, index($0, ": ") + 2); exit }' "$handoff_file" | grep -oE '[0-9a-f]{40}' | tail -n 1 || true)"
  if [[ "$handoff_sha" != "$sha" ]]; then
    echo "preflight: handoff SHA ${handoff_sha:-missing} does not match expected ${sha}" >&2
    exit 6
  fi
  lookup="$(bash "${script_dir}/wi_pr_lookup.sh" "$change_id")" || exit 7
  printf '%s\n' "$lookup"
fi

bash "${script_dir}/wi_ownership_check.sh" --check || exit 8
bash "${script_dir}/wi_secret_check.sh" --check "$ROOT" || exit 9
graph_field="$(awk -F': ' '$1 == "Authority graph" { print substr($0, index($0, ": ") + 2); exit }' "$STATE_FILE")"
if [[ -z "$graph_field" || "$graph_field" == none ]]; then
  if [[ "$workflow_state" == "Implement" ]]; then
    echo "preflight: implementation blocked until an authority graph exists" >&2
    exit 3
  fi
else
  bash "${script_dir}/wi_authority_check.sh" --check || exit $?
fi

echo "preflight: ok repo=${ACTUAL_REPO} phase=${phase} baseline=${baseline} change=${change_id} sha=${sha}"
exit 0
