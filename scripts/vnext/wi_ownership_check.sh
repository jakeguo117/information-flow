#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Read-only ownership check for WI-REQ-013.
# Two active ownership records that name the same write target are rejected
# unless both an integrator and independence evidence are recorded.
# This script does not create branches, commits, or pull requests.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_ownership_check.sh --check"
  exit 0
fi

if [[ "${1:-}" != "--check" ]]; then
  echo "ownership: only --check is supported" >&2
  exit 2
fi

ROOT="${WI_OWNERSHIP_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$ROOT" || ! -d "$ROOT" ]]; then
  echo "ownership: root is missing" >&2
  exit 2
fi

records="$(mktemp)"
trap 'rm -f "$records"' EXIT

while IFS= read -r file; do
  state="$(awk -F': ' '$1 == "ownership_state" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
  if [[ "$state" != "active" ]]; then
    continue
  fi
  change_id="$(awk -F': ' '$1 == "change_id" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
  targets="$(awk -F': ' '$1 == "write_targets" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
  integrator="$(awk -F': ' '$1 == "integrator" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
  evidence="$(awk -F': ' '$1 == "independence_evidence" { print substr($0, index($0, ": ") + 2); exit }' "$file")"
  if [[ -z "$change_id" || -z "$targets" ]]; then
    echo "ownership: ${file} is missing change_id or write_targets" >&2
    exit 1
  fi
  printf '%s\t%s\t%s\t%s\n' "$change_id" "$targets" "${integrator:-none}" "${evidence:-none}" >>"$records"
done < <(find "$ROOT/specs" -name ownership.md -type f 2>/dev/null | sort)

if [[ ! -s "$records" ]]; then
  echo "ownership: ok active=0"
  exit 0
fi

python3 - "$records" << 'PY'
import sys
rows = []
for line in open(sys.argv[1], encoding="utf-8"):
    change_id, targets, integrator, evidence = line.rstrip("\n").split("\t", 3)
    paths = [part.strip() for part in targets.split(",") if part.strip() and part.strip() != "none"]
    rows.append((change_id, paths, integrator.strip(), evidence.strip()))

blocked = False
for i, left in enumerate(rows):
    for right in rows[i + 1 :]:
        overlap = sorted(set(left[1]) & set(right[1]))
        if not overlap:
            continue
        reconciled = (
            left[2] not in ("", "none")
            and right[2] not in ("", "none")
            and left[3] not in ("", "none")
            and right[3] not in ("", "none")
        )
        if reconciled:
            print(f"ownership: overlap reconciled integrator={left[2]} targets={','.join(overlap)}")
            continue
        print(
            f"ownership: overlap blocks {left[0]} and {right[0]} on {','.join(overlap)}",
            file=sys.stderr,
        )
        blocked = True

if blocked:
    sys.exit(1)
print(f"ownership: ok active={len(rows)}")
PY
