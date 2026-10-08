#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Look up an existing pull request for one change id.
# Prints "reuse <url>" or "create". Prints NOT_VERIFIED when GitHub cannot be read.
# Does not create a pull request.

set -u

change_id="${1:-}"
if [[ ! "$change_id" =~ ^WI-CHG-[0-9]{4}$ ]]; then
  echo "lookup: change id must be WI-CHG-NNNN" >&2
  exit 1
fi

if [[ -n "${WI_PR_LOOKUP_FIXTURE_URL:-}" ]]; then
  printf 'reuse %s\n' "$WI_PR_LOOKUP_FIXTURE_URL"
  exit 0
fi

repo="${WI_PROJECT_REPOSITORY:-}"
if [[ -z "$repo" && -f PROJECT_STATE.md ]]; then
  repo="$(awk -F': ' '$1 == "Repository" { print substr($0, index($0, ": ") + 2); exit }' PROJECT_STATE.md)"
fi
if [[ -z "$repo" ]]; then
  echo "NOT_VERIFIED"
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "NOT_VERIFIED"
  exit 0
fi

json="$(gh pr list --repo "$repo" --state all --search "${change_id} in:title" --json number,title,url --limit 20 2>/dev/null || true)"
if [[ -z "$json" ]]; then
  echo "NOT_VERIFIED"
  exit 0
fi

# Search can lag behind pull request creation. A list is the effect check.
if [[ "$json" == "[]" ]]; then
  listed="$(gh pr list --repo "$repo" --state all --json number,title,url --limit 100 2>/dev/null || true)"
  if [[ -n "$listed" ]]; then
    json="$listed"
  fi
fi

url="$(CHANGE_ID="$change_id" python3 -c '
import json, os, sys
change_id = os.environ["CHANGE_ID"]
try:
    rows = json.loads(sys.stdin.read() or "[]")
except json.JSONDecodeError:
    rows = None
if not isinstance(rows, list):
    sys.exit(2)
for row in rows:
    title = row.get("title") or ""
    if change_id in title:
        print(row.get("url") or "")
        break
' <<<"$json" || true)"

if [[ -n "$url" ]]; then
  printf 'reuse %s\n' "$url"
else
  echo "create"
fi
exit 0
