#!/bin/sh
# Copy Snipd/ and Inbox/WeRead from the iCloud vault onto a standalone
# origin/main clone, then commit and push only those paths. Never runs git
# inside the iCloud vault (launchd cannot getcwd() there), and never touches
# Journal, Digests, the dirty vault branch, or com.jake.journal-daily-digest.
set -eu

PLUGIN_ROOT="${PLUGIN_ROOT:-$HOME/plugins/information-flow}"
VAULT="${INTAKE_VAULT:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain}"
WORKTREE="${INTAKE_SOURCE_WORKTREE:-$PLUGIN_ROOT/state/digitalbrain-main}"
REMOTE="${INTAKE_SOURCE_REMOTE:-git@github.com:jakeguo117/obsidian-digitalbrain.git}"
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

realpath_of() {
  python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

# Global gitconfig rewrites git@github.com to https. Launchd often cannot
# use osxkeychain, so git on this clone ignores global/system config.
gitw() {
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git -C "$WORKTREE" "$@"
}

git_clone() {
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git clone --branch main --single-branch "$REMOTE" "$WORKTREE"
}

if [ "$WAIT" -gt 0 ]; then
  log "waiting ${WAIT}s for iCloud"
  sleep "$WAIT"
fi

# launchd may start with a cwd git cannot read. Never cd into iCloud:
# macOS then returns EPERM on getcwd() for later git calls.
cd "$PLUGIN_ROOT" || die "cannot cd to plugin root: $PLUGIN_ROOT"

[ -d "$VAULT" ] || die "vault missing: $VAULT"
command -v git >/dev/null || die "git not found"
command -v rsync >/dev/null || die "rsync not found"
command -v python3 >/dev/null || die "python3 not found"

vault_real=$(realpath_of "$VAULT")

if [ -f "$WORKTREE/.git" ]; then
  log "replacing iCloud-linked worktree with standalone clone"
  rm -rf "$WORKTREE"
fi

if [ ! -d "$WORKTREE/.git" ]; then
  if [ -e "$WORKTREE" ]; then
    rm -rf "$WORKTREE"
  fi
  mkdir -p "$(dirname "$WORKTREE")"
  log "cloning $REMOTE into $WORKTREE"
  git_clone
fi

wt_real=$(realpath_of "$WORKTREE")
[ "$wt_real" != "$vault_real" ] || die "refusing to commit in the iCloud vault working tree"

gitw config user.name Jake
gitw config user.email jakeguo117@gmail.com
gitw remote set-url origin "$REMOTE"
gitw fetch origin

branch=$(gitw rev-parse --abbrev-ref HEAD)
if [ "$branch" != "main" ]; then
  log "checking out main in worktree (was $branch)"
  gitw checkout main
fi

gitw merge --ff-only origin/main

status=$(gitw -c core.quotepath=false status --porcelain)
if [ -n "$status" ]; then
  paths=$(printf '%s\n' "$status" | while IFS= read -r line; do
    [ -n "$line" ] || continue
    porcelain_path "$line"
  done)
  require_source_paths "clone has unrelated local changes" <<EOF
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
  if [ -e "$WORKTREE/$rel" ] || [ -n "$(gitw ls-files -- "$rel")" ]; then
    gitw add -- "$rel"
    gitw add -u -- "$rel"
  fi
}

stage_tree "$SNIPD"
stage_tree "$WEREAD"

cached=$(gitw -c core.quotepath=false diff --cached --name-only)
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

gitw commit -m "$COMMIT_MSG"
sha=$(gitw rev-parse HEAD)
gitw push origin main
log "pushed $sha"
