#!/usr/bin/env bash
# Cursor Cloud Agent install (runs during each Build; must be idempotent).
# information-flow: mostly stdlib + yt-dlp (matches CI). Bake a .venv so agents start warm.
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PY="${PYTHON:-python3}"
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), sys.version' || {
  echo "Python >= 3.11 required"; exit 1; }
# Cloud Agent images often lack ensurepip; bake venv support once into the snapshot.
if ! "$PY" -c 'import ensurepip' 2>/dev/null; then
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv python3-pip \
      || sudo apt-get install -y -qq python3.12-venv python3-pip \
      || sudo apt-get install -y -qq python3.11-venv python3-pip
  else
    apt-get update -qq
    apt-get install -y -qq python3-venv python3-pip \
      || apt-get install -y -qq python3.12-venv python3-pip
  fi
fi
[ -x .venv/bin/python ] || "$PY" -m venv .venv
. .venv/bin/activate
python -m pip install -q --upgrade pip
# CI uses yt-dlp for YouTube intake; keep quiet
python -m pip install -q yt-dlp
# offline smoke (same as .github/workflows/package-chatgpt-plugin.yml; no vault/secrets)
python scripts/package_journal_pack.py --chatgpt-plugin >/dev/null
python scripts/test_journal_pack.py PackageTests.test_extracted_zip_runs_builder
echo "cursor install ok: $(python --version)"
