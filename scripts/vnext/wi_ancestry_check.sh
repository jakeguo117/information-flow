#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Flow-forward check. Approved behavior A must stay readable and name its replacement.
# Silent removal of A fails. This script does not edit either file.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_ancestry_check.sh --check <superseded-file> <replacement-file> <kept-sentence>"
  exit 0
fi

if [[ "${1:-}" != "--check" || -z "${2:-}" || -z "${3:-}" || -z "${4:-}" ]]; then
  echo "Usage: scripts/wi_ancestry_check.sh --check <superseded-file> <replacement-file> <kept-sentence>" >&2
  exit 2
fi

old="$2"
new="$3"
sentence="$4"

if [[ ! -f "$old" || ! -f "$new" ]]; then
  echo "ancestry: missing file" >&2
  exit 1
fi

if ! grep -q "SUPERSEDED BY" "$old"; then
  echo "ancestry: silent overwrite; superseded file has no SUPERSEDED BY marker" >&2
  exit 1
fi

if ! grep -F -q "$sentence" "$old"; then
  echo "ancestry: previous behavior is not readable" >&2
  exit 1
fi

if grep -F -q "$sentence" "$new"; then
  echo "ancestry: replacement still presents the superseded sentence as current" >&2
  exit 1
fi

echo "ancestry: ok"
exit 0
