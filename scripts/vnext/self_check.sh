#!/usr/bin/env bash
# Guard self-checks for the ported VNext scripts.
# A zero exit is not an AIC acceptance PASS.
# Does not enroll a project, write a vault, load launchd, or merge.

set -u
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"
fail=0
say() { printf '%s\n' "$*"; }

say "py_compile"
python3 -m py_compile scripts/vnext/wi_authority_check.py scripts/vnext/wi_bootstrap.py scripts/vnext/wi_event_check.py scripts/vnext/status_board.py scripts/vnext/continue_caller.py || fail=1

say "bash -n"
for f in scripts/vnext/*.sh; do
  bash -n "$f" || fail=1
done

say "merge_if_head mismatch rejects"
if scripts/vnext/wi_merge_if_head.sh --expected aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --actual bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb >/tmp/vnext-merge-mismatch.out 2>/tmp/vnext-merge-mismatch.err; then
  say "mismatch was accepted"
  fail=1
else
  say "mismatch rejected"
fi

say "merge_if_head match"
sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
scripts/vnext/wi_merge_if_head.sh --expected "$sha" --actual "$sha" >/tmp/vnext-merge-match.out || fail=1

say "secret check on an empty temp root"
tmp="$(mktemp -d)"
scripts/vnext/wi_secret_check.sh --check "$tmp" || fail=1
rm -rf "$tmp"

say "event check rejects a non-object payload"
ev="$(mktemp)"
ho="$(mktemp)"
ef="$(mktemp)"
printf '%s\n' '[]' >"$ev"
printf '%s\n' 'workflow_state: draft' >"$ho"
: >"$ef"
if scripts/vnext/wi_event_check.sh --check "$ev" "$ho" "$ef" >/tmp/vnext-event.out 2>/tmp/vnext-event.err; then
  say "bad event was admitted"
  fail=1
else
  say "bad event rejected"
fi
rm -f "$ev" "$ho" "$ef"

say "plan boundary rejects a plan with no verified baseline"
plan="$(mktemp)"
printf '%s\n' 'no baseline here' >"$plan"
if scripts/vnext/wi_plan_boundary.sh --check "$plan" >/tmp/vnext-plan.out 2>/tmp/vnext-plan.err; then
  say "empty plan was accepted"
  fail=1
else
  say "empty plan rejected"
fi
rm -f "$plan"

say "projection rejects a SHA headline"
proj="$(mktemp)"
printf '%s\n' 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' >"$proj"
if scripts/vnext/wi_projection_check.sh --check "$proj" >/tmp/vnext-proj.out 2>/tmp/vnext-proj.err; then
  say "SHA headline was accepted"
  fail=1
else
  say "SHA headline rejected"
fi
rm -f "$proj"

say "approval blocks a material delta with a blank decision"
chg="$(mktemp)"
cat >"$chg" <<'EOF'
ADDED: a new behavior
MODIFIED: none
REMOVED: none
Jake decision: blank until decided
Status: Draft
Approved content: none
EOF
if scripts/vnext/wi_approval_check.sh --check "$chg" >/tmp/vnext-approval.out 2>/tmp/vnext-approval.err; then
  say "blank decision was accepted"
  fail=1
else
  say "blank decision blocked"
fi
rm -f "$chg"

say "ancestry rejects a file with no superseded marker"
oldf="$(mktemp)"
newf="$(mktemp)"
printf '%s\n' 'behavior A' >"$oldf"
printf '%s\n' 'behavior B keeps behavior A' >"$newf"
if scripts/vnext/wi_ancestry_check.sh --check "$oldf" "$newf" "behavior A" >/tmp/vnext-anc.out 2>/tmp/vnext-anc.err; then
  say "missing superseded marker was accepted"
  fail=1
else
  say "missing superseded marker rejected"
fi
rm -f "$oldf" "$newf"

if [[ "$fail" -ne 0 ]]; then
  say "vnext guard self-check: failed"
  exit 1
fi
say "vnext guard self-check: completed"
say "This result is not an AIC acceptance PASS."
exit 0
