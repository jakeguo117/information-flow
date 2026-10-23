#!/bin/sh
# Paste into the Codex Cloud environment for jakeguo117/obsidian-digitalbrain.
# Setup-phase internet clones public information-flow. The agent phase can stay offline.
# INFOFLOW_REF is the git ref to fetch. Testing default is this branch; use main after merge.
set -eu

REF="${INFOFLOW_REF:-cursor/codex-cloud-journal-guard-e437}"
REPO="${INFOFLOW_REPO:-https://github.com/jakeguo117/information-flow.git}"

if [ -n "${INFOFLOW_HOME:-}" ]; then
  DEST="$INFOFLOW_HOME"
elif [ -w /opt ] || [ "$(id -u)" -eq 0 ]; then
  DEST="/opt/information-flow"
else
  DEST="${HOME}/.codex/information-flow"
fi

command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }

python3 -m pip install --quiet --disable-pip-version-check 'PyYAML==6.0.1'

mkdir -p "$(dirname "$DEST")"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" fetch --depth 1 origin "$REF"
  git -C "$DEST" checkout --force FETCH_HEAD
else
  rm -rf "$DEST"
  git clone --depth 1 --branch "$REF" "$REPO" "$DEST"
fi

printf '%s\n' "codex-cloud" > "$DEST/.runtime-codex-cloud"
printf '%s\n' "$DEST" > "${HOME}/.infoflow-codex-home"

persist() {
  file="$1"
  touch "$file"
  if ! grep -q 'INFOFLOW_RUNTIME=codex-cloud' "$file"; then
    cat >> "$file" <<EOF
export INFOFLOW_RUNTIME=codex-cloud
export INFOFLOW_HOME="$DEST"
export INFOFLOW_REF="$REF"
EOF
  fi
}
persist "${HOME}/.bashrc"
persist "${HOME}/.profile"

echo "information-flow skills: $DEST"
echo "ref: $REF"
echo "workspace root must be the obsidian-digitalbrain checkout (it has 📝 Journal/)"
