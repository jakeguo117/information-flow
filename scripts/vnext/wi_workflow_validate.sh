#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Validate the project lifecycle workflow with Spec Kit 1.0.13.
# specify-cli 1.0.13 has no "workflow validate" subcommand. This script uses
# the same validate_workflow function that "specify workflow run" uses.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
WORKFLOW="$ROOT/.specify/workflows/change-lifecycle/workflow.yml"

if [[ ! -f "$WORKFLOW" ]]; then
  echo "workflow validate: missing ${WORKFLOW}" >&2
  exit 1
fi

if specify workflow --help 2>&1 | grep -q 'validate'; then
  specify workflow validate "$WORKFLOW"
  exit $?
fi

echo "workflow validate: specify-cli 1.0.13 has no workflow validate subcommand; using validate_workflow"
specify_bin="$(command -v specify)"
python_bin="$(sed -n '1s/^#!//p' "$specify_bin")"
"$python_bin" - "$WORKFLOW" << 'PY'
import sys
from pathlib import Path
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

path = Path(sys.argv[1])
errors = validate_workflow(WorkflowDefinition.from_yaml(path))
if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
text = path.read_text()
if text.count("type: gate") != 1:
    print("workflow validate: expected exactly one gate", file=sys.stderr)
    sys.exit(1)
jake = text.find("Jake gate before Approved")
repair = text.find("No Jake gate on this repair")
if jake < 0 or repair < 0 or jake > repair:
    print("workflow validate: Jake gate must come before repair", file=sys.stderr)
    sys.exit(1)
print("workflow validate: ok")
PY
