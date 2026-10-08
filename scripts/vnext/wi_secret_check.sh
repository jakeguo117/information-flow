#!/usr/bin/env bash
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

# Flag simulated or real credentials in project records.
# Prints the pattern name and path only. It does not print the matched text.

set -u

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: scripts/wi_secret_check.sh --check [root]"
  exit 0
fi

if [[ "${1:-}" != "--check" ]]; then
  echo "secret: only --check is supported" >&2
  exit 2
fi

ROOT="${2:-${WI_SECRET_ROOT:-}}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [[ -z "$ROOT" || ! -d "$ROOT" ]]; then
  echo "secret: root is missing" >&2
  exit 2
fi

python3 - "$ROOT" << 'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
patterns = [
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("stripe_live", re.compile(r"sk_live_[A-Za-z0-9]{8,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
]
roots = [
    root / "PROJECT_STATE.md",
    root / "specs",
    root / "docs",
    root / "templates",
    root / ".specify" / "templates",
    root / ".github",
]
found = False
for start in roots:
    if not start.exists():
        continue
    files = [start] if start.is_file() else [p for p in start.rglob("*") if p.is_file()]
    for path in files:
        if ".cache" in path.parts or path.suffix in {".png", ".jpg"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in patterns:
            if pattern.search(text):
                print(f"secret: {name} in {path}", file=sys.stderr)
                found = True
if found:
    sys.exit(1)
print("secret: ok")
PY
