#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Read the canonical authority graph and validate it.
# Exit 0: local bindings passed. External sources may be NOT_VERIFIED.
# Exit 10: a required binding is missing or the graph is not readable.
# Exit 11: an observation names the wrong authority identity.
# Exit 12: a pinned external revision does not match the observation.
# Exit 14: a required authority is NOT_VERIFIED.
# This script does not fetch the network.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_authority_check.sh --check|--self-test"
  exit 0
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  echo "authority-graph: FAIL missing binding" >&2
  exit 10
fi

exec python3 "$ROOT/scripts/vnext/wi_authority_check.py" "$@"
