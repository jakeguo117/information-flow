#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Persist one material escalation without editing the approved spec.

set -u

if [[ "${1:-}" != "--record" || -z "${2:-}" || -z "${3:-}" || -z "${4:-}" ]]; then
  echo "Usage: scripts/wi_escalation_record.sh --record <change-dir> <category> <question>" >&2
  exit 2
fi

directory="$2"
category="$3"
question="$4"
handoff="${directory}/handoff.md"
approved="${directory}/spec.md"
if [[ ! -f "$handoff" || ! -f "$approved" ]]; then
  echo "escalation: handoff or spec is missing" >&2
  exit 2
fi

case "$category" in
  requirement|acceptance|product|architecture|authority|security|destructive|intent|retry|cost) ;;
  *)
    echo "escalation: unknown category" >&2
    exit 2
    ;;
esac

before="$(cksum "$approved")"
if [[ "$category" == "cost" ]]; then
  result="STOP — JAKE COST APPROVAL REQUIRED"
else
  result="STOP — JAKE DECISION REQUIRED"
fi

field() {
  awk -F': ' -v key="$1" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$handoff"
}

# Category is not question identity. The same unresolved question is reused.
# A different question appends a new immutable record.
target="${directory}/escalation.md"
if [[ -f "$target" ]]; then
  existing="$(python3 - "$target" "$category" "$question" <<'PY'
import sys
path, category, question = sys.argv[1:]
text = open(path, encoding="utf-8").read()
closed = set()
for block in text.split("\n---\n"):
    fields = {}
    for line in block.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value)
    if fields.get("resolution_event") == "terminal" and fields.get("choice") in {"approve", "reject", "defer", "cancel"}:
        closed.add(fields.get("escalation_id", ""))
for block in text.split("\n---\n"):
    fields = {}
    for line in block.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value)
    ident = fields.get("escalation_id", "")
    if (
        fields.get("problem") == category
        and fields.get("question") == question
        and fields.get("resolution") == "unresolved"
        and ident
        and ident not in closed
    ):
        print(ident)
        break
PY
)"
  if [[ -n "$existing" ]]; then
    echo "$result"
    exit 0
  fi
fi
seq=1
if [[ -f "$target" ]]; then
  seq="$(grep -c '^escalation_id: ' "$target" || true)"
  seq="$((seq + 1))"
fi
escalation_id="WI-ESC-${category}-${seq}"
if [[ -s "$target" ]]; then
  printf '%s\n' '---' >>"$target"
fi

cat >>"$target" <<EOF
result: ${result}
project_id: $(field project_id)
repository: $(field repository)
change_id: $(field change_id)
execution_id: $(field execution_id)
workflow_run_id: $(field workflow_run_id)
native_run_id: $(field native_run_id)
escalation_id: ${escalation_id}
triggering_decision_id: $(field decision_id)
record_revision: $(field expected_remote_sha)
problem: ${category}
question: ${question}
approved_intent: $(field decision_id)
evidence: ${handoff}
options: stop affected work
recommendation: none
next_legal_action: ${result}
checkpoint: ${directory}
budgets: repair_budget 3
resolution: unresolved
EOF

after="$(cksum "$approved")"
if [[ "$before" != "$after" ]]; then
  echo "escalation: approved file changed" >&2
  exit 1
fi

echo "$result"
exit 0
