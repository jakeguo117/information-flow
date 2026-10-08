#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Print the review or verification route for this checkout.
# A record applies when its sha field equals HEAD.
# It also applies when HEAD is an evidence envelope of that sha.
# An envelope may change only project state, handoff, review,
# verification, and closure-report files. Any other path makes the
# record historical. pass and verified on an envelope print
# content_pass and content_verified. Those tokens do not authorize merge.
# Caller-supplied workflow inputs are ignored.
# This script does not delete historical records.

set -u

kind="${1:-}"
root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$root" || ! -f "$root/PROJECT_STATE.md" ]]; then
  echo unset
  exit 0
fi

if [[ "$kind" != "review" && "$kind" != "verification" ]]; then
  echo unset
  exit 0
fi

unavailable() {
  if [[ "$kind" == "review" ]]; then
    echo unreviewed
  else
    echo unverified
  fi
  exit 0
}

change_field="$(awk -F': ' '$1 == "Active Change" { print substr($0, index($0, ": ") + 2); exit }' "$root/PROJECT_STATE.md")"
change_dir="${change_field%% *}"
change_dir="${change_dir%.}"
if [[ "$kind" == "review" ]]; then
  file="$root/$change_dir/review.md"
else
  file="$root/$change_dir/verification.md"
fi

if [[ ! -f "$file" ]]; then
  unavailable
fi

recorded="$(awk -F': ' '$1 == "sha" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
head_sha="$(git -C "$root" rev-parse --verify HEAD 2>/dev/null || true)"
if [[ ! "$recorded" =~ ^[0-9a-f]{40}$ || ! "$head_sha" =~ ^[0-9a-f]{40}$ ]]; then
  unavailable
fi

evidence_path() {
  local path="$1"
  local rest dir base
  case "$path" in
    *' '*|*'->'*) return 1 ;;
  esac
  case "$path" in
    PROJECT_STATE.md) return 0 ;;
  esac
  [[ "$path" == specs/*/* ]] || return 1
  rest="${path#specs/}"
  dir="${rest%%/*}"
  base="${rest#*/}"
  [[ -n "$dir" && -n "$base" && "$dir" != */* && "$base" != */* ]] || return 1
  case "$base" in
    review.md|verification.md|handoff.md|closure-report.md) return 0 ;;
  esac
  return 1
}

envelope_of() {
  local recorded_sha="$1"
  local current="$2"
  local rel="$3"
  local path line status_path committed work
  git -C "$root" cat-file -e "${current}:${rel}" 2>/dev/null || return 1
  committed="$(git -C "$root" show "${current}:${rel}")"
  work="$(cat "$file")"
  [[ "$committed" == "$work" ]] || return 1
  git -C "$root" merge-base --is-ancestor "$recorded_sha" "$current" 2>/dev/null || return 1
  [[ "$recorded_sha" == "$current" ]] && return 1
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    evidence_path "$path" || return 1
  done < <(git -C "$root" diff --name-only --no-renames "$recorded_sha" "$current")
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    evidence_path "$path" || return 1
  done < <(git -C "$root" diff --name-only --no-renames HEAD; git -C "$root" diff --cached --name-only --no-renames HEAD)
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    status_path="${line:3}"
    evidence_path "$status_path" || return 1
  done < <(git -C "$root" status --porcelain --untracked-files=all)
  return 0
}

rel="${file#"$root"/}"
envelope=no
if [[ "$recorded" != "$head_sha" ]]; then
  if envelope_of "$recorded" "$head_sha" "$rel"; then
    envelope=yes
  else
    unavailable
  fi
fi

result="$(awk -F': ' '$1 == "result" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
class="$(awk -F': ' '$1 == "class" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
token="$(printf '%s' "$result" | tr '[:upper:]' '[:lower:]')"
class_token="$(printf '%s' "$class" | tr '[:upper:]' '[:lower:]')"
case "$token" in
  pass) route=pass ;;
  changes_requested) route=changes_requested ;;
  verified) route=verified ;;
  material_stop) route=material_stop ;;
  cost_stop) route=cost_stop ;;
  failed)
    case "$class_token" in
      material) route=material_stop ;;
      cost) route=cost_stop ;;
      *) route=failed ;;
    esac
    ;;
  *) route=unset ;;
esac
if [[ "$envelope" == yes && "$route" == pass ]]; then
  echo content_pass
elif [[ "$envelope" == yes && "$route" == verified ]]; then
  echo content_verified
else
  echo "$route"
fi
exit 0
