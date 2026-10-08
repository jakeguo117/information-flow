#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Deterministic fail-fast string check for an engineering plan.
# This is not proof of architecture, security, or cost compliance.

set -u

if [[ "${1:-}" != "--check" || ! -f "${2:-}" ]]; then
  echo "Usage: scripts/wi_plan_boundary.sh --check <plan.md>" >&2
  exit 2
fi

plan="$(cat "$2")"
fail() {
  echo "plan-boundary: reject reason=$1" >&2
  exit 1
}

if [[ "$plan" == *"UNKNOWN_PREDICATE"* || "$plan" == *"ARCHITECTURE_PREDICATE_UNRESOLVED"* ]]; then
  fail unknown-predicate
fi
if [[ "$plan" != *"## Verified Baseline"* ]]; then
  fail missing-baseline
fi
if [[ "$plan" != *"scripts/wi_event_check.sh"* ]]; then
  fail missing-reuse
fi
if [[ "$plan" == *"authorize a plan upgrade"* || "$plan" == *"GPT GitHub write is authorized"* || "$plan" == *"Computer Use is the normal transport"* || "$plan" == *"add a second orchestrator"* ]]; then
  fail material-departure
fi
if [[ "$plan" != *"PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE"* ]]; then
  fail missing-result
fi

# Fail-fast only. A CONTINUE line is not architecture, security, or cost proof.
echo "PLAN_ACCEPTED_WITHIN_BOUNDARY — CONTINUE"
exit 0
