#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Admit resume only from an explicit Jake approval that names the escalation.

set -u

if [[ "${1:-}" != "--check" || ! -f "${2:-}" || ! -f "${3:-}" ]]; then
  echo "Usage: scripts/wi_resolution_check.sh --check <resolution.md> <escalation.md>" >&2
  exit 2
fi

resolution="$2"
escalation="$3"

field() {
  awk -F': ' -v key="$2" '$1 == key { print substr($0, index($0, ": ") + 2); exit }' "$1"
}

choice="$(field "$resolution" resolution)"
actor="$(field "$resolution" actor)"
evidence="$(field "$resolution" evidence)"
content="$(field "$resolution" content_sha256)"
decision="$(field "$resolution" decision_id)"
predecessor="$(field "$resolution" predecessor_decision_id)"
escalation_id="$(field "$resolution" escalation_id)"

case "$choice" in
  reject|defer|cancel|approve) ;;
  *)
    echo "resolution: reject reason=choice" >&2
    exit 1
    ;;
esac

# Reject, defer, and cancel stay terminal for this escalation.
# A later approve cannot reactivate that escalation.
terminal="$(python3 - "$escalation" "$escalation_id" <<'PY' || true
import sys
path, wanted = sys.argv[1:]
text = open(path, encoding="utf-8").read()
for block in text.split("\n---\n"):
    fields = {}
    for line in block.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value)
    if fields.get("resolution_event") == "terminal" and fields.get("escalation_id") == wanted:
        if fields.get("choice") in {"reject", "defer", "cancel", "approve"}:
            print(fields["choice"])
            break
PY
)"
if [[ -n "$terminal" ]]; then
  echo "resolution: reject reason=terminal" >&2
  exit 1
fi

# Every Decision B outcome needs a new decision id before any terminal write.
if [[ -z "$decision" || -z "$predecessor" || "$decision" == "$predecessor" ]]; then
  echo "resolution: reject reason=identity" >&2
  exit 1
fi

triggering="$(python3 - "$escalation" "$escalation_id" <<'PY' || true
import sys
path, wanted = sys.argv[1:]
text = open(path, encoding="utf-8").read()
for block in text.split("\n---\n"):
    fields = {}
    for line in block.splitlines():
        if line.startswith("---") or ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value)
    if fields.get("escalation_id") == wanted:
        print(fields.get("triggering_decision_id", ""))
        sys.exit(0)
sys.exit(1)
PY
)"
if [[ -z "$triggering" || "$predecessor" != "$triggering" ]]; then
  echo "resolution: reject reason=ancestry" >&2
  exit 1
fi

persist_choice() {
  if [[ -s "$escalation" ]]; then
    printf '%s\n' '---' >>"$escalation"
  fi
  cat >>"$escalation" <<EOF
resolution_event: terminal
escalation_id: ${escalation_id}
choice: ${choice}
decision_id: ${decision}
predecessor_decision_id: ${predecessor}
EOF
}

if [[ "$choice" != "approve" ]]; then
  persist_choice
  echo "resolution: stop choice=${choice}"
  exit 0
fi

# actor and evidence are a syntactic shape check.
# "Jake" and a non-empty evidence string are not an authenticated approval.
# Native approval receipt is NOT_VERIFIED. This script does not verify a receipt.
if [[ "$actor" != "Jake" || -z "$evidence" || "$evidence" == "none" || "$evidence" == "forged" ]]; then
  echo "resolution: reject reason=approval" >&2
  exit 1
fi
if [[ ! "$content" =~ ^[0-9a-f]{64}$ ]]; then
  echo "resolution: reject reason=identity" >&2
  exit 1
fi

blocked="$(python3 - "$escalation" "$escalation_id" <<'PY' || true
import sys
path, wanted = sys.argv[1:]
text = open(path, encoding="utf-8").read()
terminal = set()
unresolved = []
for block in text.split("\n---\n"):
    fields = {}
    for line in block.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value)
    ident = fields.get("escalation_id", "")
    if fields.get("resolution_event") == "terminal" and fields.get("choice") in {"approve", "reject", "defer", "cancel"}:
        terminal.add(ident)
    if fields.get("resolution") == "unresolved" and ident:
        unresolved.append(ident)
for ident in unresolved:
    if ident != wanted and ident not in terminal:
        print(ident)
        break
PY
)"
if [[ -n "$blocked" ]]; then
  echo "resolution: reject reason=blocked" >&2
  exit 1
fi

persist_choice
echo "resolution: admit decision=${decision}"
echo "native approval receipt: NOT_VERIFIED"
exit 0
