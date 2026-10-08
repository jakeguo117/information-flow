#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Check the acceptance fixture against behavior A or behavior B.
# Behavior B also requires the superseded A sentence to remain readable.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_acceptance_fixture_check.sh --expect A|B"
  exit 0
fi

if [[ "${1:-}" != "--expect" || -z "${2:-}" ]]; then
  echo "Usage: scripts/wi_acceptance_fixture_check.sh --expect A|B" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fixture="$ROOT/docs/acceptance/fixture.md"
sentence_a="ACCEPTANCE_FIXTURE: behavior A is the current sentence."
sentence_b="ACCEPTANCE_FIXTURE: behavior B replaced A."
evidence_line="ACCEPTANCE_EVIDENCE: present"

if [[ ! -f "$fixture" ]]; then
  echo "fixture: missing ${fixture}" >&2
  exit 1
fi

if [[ "$2" == "A" ]]; then
  if ! grep -F -q "$sentence_a" "$fixture"; then
    echo "fixture: behavior A sentence is missing" >&2
    exit 1
  fi
  echo "fixture: ok behavior=A"
  exit 0
fi

if [[ "$2" != "B" ]]; then
  echo "fixture: expected A or B" >&2
  exit 2
fi

if ! grep -F -q "$sentence_b" "$fixture"; then
  echo "fixture: behavior B sentence is missing" >&2
  exit 1
fi
if ! grep -F -q "$evidence_line" "$fixture"; then
  echo "fixture: ACCEPTANCE_EVIDENCE is missing" >&2
  exit 1
fi
if grep -F -q "$sentence_a" "$fixture"; then
  echo "fixture: behavior A is still presented as the current fixture sentence" >&2
  exit 1
fi

bug_file="$ROOT/docs/acceptance/bug-fixture.txt"
bug_sentence="bug-fixture: approved behavior"
if [[ ! -f "$bug_file" ]] || ! grep -F -q "$bug_sentence" "$bug_file"; then
  echo "fixture: bug fixture does not match the approved sentence" >&2
  exit 1
fi

bash "$ROOT/scripts/vnext/wi_ancestry_check.sh" --check \
  "$ROOT/specs/006-acceptance-a/spec.md" \
  "$ROOT/specs/007-acceptance-b/spec.md" \
  "$sentence_a" || exit 1

echo "fixture: ok behavior=B"
exit 0
