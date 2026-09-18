#!/bin/sh
# Copy Snipd/ and Inbox/WeRead from the iCloud vault onto an origin/main
# worktree, then commit and push only those paths. Never touches Journal,
# Digests, the dirty vault branch, or com.jake.journal-daily-digest.
set -eu

PLUGIN_ROOT="${PLUGIN_ROOT:-$HOME/plugins/information-flow}"
VAULT="${INTAKE_VAULT:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain}"
WORKTREE="${INTAKE_SOURCE_WORKTREE:-$PLUGIN_ROOT/state/digitalbrain-main}"
WAIT="${INTAKE_SOURCE_ICLOUD_WAIT:-45}"
SNIPD="Snipd"
WEREAD="📥 Inbox/WeRead"
COMMIT_MSG="intake: sync Snipd WeRead sources"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
  log "error: $*" >&2
  exit 1
}

path_allowed() {
  case "$1" in
    "$SNIPD"|"$SNIPD"/*|"$WEREAD"|"$WEREAD"/*) return 0 ;;
    *) return 1 ;;
  esac
}

porcelain_path() {
  rel=${1#???}
  rel=${rel#\"}
  rel=${rel%\"}
  printf '%s\n' "$rel"
}

require_source_paths() {
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    path_allowed "$rel" || die "$1: $rel"
  done
}

if [ "$WAIT" -gt 0 ]; then
  log "waiting ${WAIT}s for iCloud"
  sleep "$WAIT"
fi

# launchd may start with a cwd git cannot read. Never cd into iCloud:
# macOS then returns EPERM on getcwd() for later git calls.
cd "$PLUGIN_ROOT" || die "cannot cd to plugin root: $PLUGIN_ROOT"

[ -d "$VAULT/.git" ] || die "vault is not a git repo: $VAULT"
command -v git >/dev/null || die "git not found"
command -v rsync >/dev/null || die "rsync not found"
command -v python3 >/dev/null || die "python3 not found"

realpath_of() {
  python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

vault_real=$(realpath_of "$VAULT")

git -C "$VAULT" fetch origin

if [ ! -e "$WORKTREE/.git" ]; then
  mkdir -p "$(dirname "$WORKTREE")"
  if [ -d "$WORKTREE" ]; then
    rmdir "$WORKTREE" 2>/dev/null || die "worktree path exists and is not empty: $WORKTREE"
  fi
  log "creating origin/main worktree at $WORKTREE"
  git -C "$VAULT" worktree add "$WORKTREE" main
else
  git -C "$WORKTREE" fetch origin
fi

wt_real=$(realpath_of "$WORKTREE")
[ "$wt_real" != "$vault_real" ] || die "refusing to commit in the iCloud vault working tree"

branch=$(git -C "$WORKTREE" rev-parse --abbrev-ref HEAD)
if [ "$branch" != "main" ]; then
  log "checking out main in worktree (was $branch)"
  git -C "$WORKTREE" checkout main
fi

git -C "$WORKTREE" merge --ff-only origin/main

status=$(git -C "$WORKTREE" -c core.quotepath=false status --porcelain)
if [ -n "$status" ]; then
  paths=$(printf '%s\n' "$status" | while IFS= read -r line; do
    [ -n "$line" ] || continue
    porcelain_path "$line"
  done)
  require_source_paths "worktree has unrelated local changes" <<EOF
$paths
EOF
fi

sync_tree() {
  src=$1
  dest=$2
  label=$3
  if [ ! -d "$src" ]; then
    log "skip missing $label at $src"
    return 0
  fi
  mkdir -p "$dest"
  rsync -a --delete --exclude '.DS_Store' "$src/" "$dest/"
  log "synced $label"
}

sync_tree "$VAULT/$SNIPD" "$WORKTREE/$SNIPD" "$SNIPD"
sync_tree "$VAULT/$WEREAD" "$WORKTREE/$WEREAD" "$WEREAD"

stage_tree() {
  rel=$1
  if [ -e "$WORKTREE/$rel" ] || [ -n "$(git -C "$WORKTREE" ls-files -- "$rel")" ]; then
    git -C "$WORKTREE" add -- "$rel"
    git -C "$WORKTREE" add -u -- "$rel"
  fi
}

stage_tree "$SNIPD"
stage_tree "$WEREAD"

cached=$(git -C "$WORKTREE" -c core.quotepath=false diff --cached --name-only)
if [ -z "$cached" ]; then
  log "no source changes"
  exit 0
fi

require_source_paths "refusing to commit unexpected path" <<EOF
$cached
EOF

log "committing source changes:"
printf '%s\n' "$cached" | while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  log "  $rel"
done

git -C "$WORKTREE" commit -m "$COMMIT_MSG"
sha=$(git -C "$WORKTREE" rev-parse HEAD)
git -C "$WORKTREE" push origin main
log "pushed $sha"
