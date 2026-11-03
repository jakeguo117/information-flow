#!/usr/bin/env python3
"""Push local changes of three iCloud vault folders to GitHub (DigitalBrain).

One direction only: iCloud vault (read-only) -> own clone outside iCloud -> GitHub.

Rules (all enforced in code):
- Only paths under SCOPE are ever committed. Exact paths are staged; never `git add -A`.
- Never force-push, never rebase, never merge. Deletions are never pushed.
- The vault is never written: an audit hook aborts the process on any write, rename,
  delete, chmod or mkdir under the vault, and on any subprocess whose cwd is in the vault.
- Never runs git with cwd in the vault; the pull gitdir is only touched with a dummy
  work tree and only by an allowlist of commands that do not read the work tree.
- Round runs only when the pull (Obsidian Git, gitdir --pull-gitdir) is current:
  pull HEAD == GitHub main. Otherwise the round is skipped.
- Per file: push only when GitHub still has the version the vault was based on.
  Both sides changed -> skip that file. Vault equals an older GitHub version -> skip.
- Skipped: dot entries (.obsidian*, .trash, .DS_Store), iCloud copies "name 2.md"
  when "name.md" exists, `.name.icloud` stubs and dataless files, files modified less
  than --settle-seconds ago or changing between two reads.
- Push rejected (GitHub moved): the unpushed commit is dropped from the own clone
  (reset to origin/main there; the clone is outside iCloud). Retry next round.
- After a push, the pull gitdir bookkeeping (ref + index) is moved to the pushed commit
  only when every file changed in pull-HEAD..pushed is byte-identical in the vault and all
  those commits are ours. The vault itself is not touched by this.
- Alerts: log file + status.json only.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

SCOPE = ("📥 Inbox/Snipd", "📥 Inbox/WeRead", "📚 Books")
SF_DATALESS = 0x40000000
SHANGHAI = "Asia/Shanghai"
BRANCH = "main"
REMOTE_REF = "refs/remotes/origin/main"
GIT_TIMEOUT = 90
MAX_FILE_BYTES = 20 * 1024 * 1024
COMMIT_NAME = "Jake (iMac pusher)"
COMMIT_EMAIL = "64625126+jakeguo117@users.noreply.github.com"
COMMIT_PREFIX = "imac: sync Snipd WeRead Books"
MACBOOK_MARKERS = ("intake: sync Snipd WeRead sources", "vault backup:")
COPY_RE = re.compile(r"^(?P<stem>.+) (?P<n>[2-9]|[1-9][0-9])(?P<ext>\.[^./ ]+)?$")
PULL_GIT_ALLOWED = {"rev-parse", "symbolic-ref", "ls-tree", "read-tree", "update-ref",
                    "log", "cat-file", "merge-base", "fetch", "diff-tree"}
FORBIDDEN_PARTS = ("projects/trading",)

QUIET_WINDOWS = (  # Asia/Shanghai; weekday 0 = Monday
    ((0, 1, 2, 3, 4, 5), "07:55", "08:45"),  # trading-signal 08:05, dispatch 08:30
    ((0, 1, 2, 3, 4, 5), "10:35", "10:55"),  # data-kick 10:40
    (None, "03:20", "04:30"),                # digitalbrain-backup 03:30
)


class Fatal(Exception):
    pass


class AuthError(Fatal):
    pass


class GuardViolation(BaseException):
    """Raised by the audit hook. BaseException so generic handlers cannot swallow it."""


# ---------------------------------------------------------------- write guard

_GUARD = {"roots": (), "on": False}


def _under(p, roots) -> bool:
    if isinstance(p, int) or p is None:
        return False
    try:
        s = os.fsdecode(p)
    except Exception:
        return False
    if not os.path.isabs(s):
        s = os.path.join(os.getcwd(), s)
    s = os.path.normpath(s)
    rs = os.path.realpath(s)
    for r in roots:
        for cand in (s, rs):
            if cand == r or cand.startswith(r + os.sep):
                return True
    return False


_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
_PATH_EVENTS_1 = {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.chown", "os.utime",
                  "os.truncate", "os.chflags", "os.lchflags", "os.setxattr", "os.removexattr",
                  "shutil.rmtree", "os.mkfifo", "os.mknod"}
_PATH_EVENTS_2 = {"os.rename", "os.replace", "os.link", "os.symlink", "shutil.copyfile",
                  "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move"}


def _hook(event, args):
    if not _GUARD["on"]:
        return
    roots = _GUARD["roots"]
    if event == "open":
        path, mode, flags = (list(args) + [None, None, None])[:3]
        writing = False
        if isinstance(mode, str) and any(c in mode for c in "wax+"):
            writing = True
        if isinstance(flags, int) and flags & _WRITE_FLAGS:
            writing = True
        if writing and _under(path, roots):
            raise GuardViolation(f"blocked write open under vault: {path!r}")
    elif event in _PATH_EVENTS_1:
        if args and _under(args[0], roots):
            raise GuardViolation(f"blocked {event} under vault: {args[0]!r}")
    elif event in _PATH_EVENTS_2:
        for a in args[:2]:
            if _under(a, roots):
                raise GuardViolation(f"blocked {event} under vault: {a!r}")
    elif event == "subprocess.Popen":
        executable, argv, cwd = args[0], args[1], args[2]
        if cwd is not None and _under(cwd, roots):
            raise GuardViolation(f"blocked subprocess with cwd in vault: {cwd!r}")
        if cwd is None and _under(os.getcwd(), roots):
            raise GuardViolation("blocked subprocess: current directory is in the vault")
        argv = [os.fsdecode(a) for a in (argv or [])]
        for a in argv:
            if a.startswith("--work-tree") or a.startswith("core.worktree"):
                val = a.split("=", 1)[1] if "=" in a else ""
                if val == "" or _under(val, roots):
                    raise GuardViolation(f"blocked git work tree in vault: {a!r}")
            if a.startswith("--git-dir=") and _GUARD.get("pull_gitdir") and \
                    os.path.realpath(a.split("=", 1)[1]) == _GUARD["pull_gitdir"]:
                if "--work-tree=" + _GUARD.get("dummy_worktree", "") not in argv:
                    raise GuardViolation("blocked pull-gitdir git without dummy work tree")
                sub = _first_subcommand(argv)
                if sub not in PULL_GIT_ALLOWED:
                    raise GuardViolation(f"blocked pull-gitdir git {sub!r}")
                if sub == "read-tree" and any(x in argv for x in ("-u", "--reset")):
                    raise GuardViolation("blocked read-tree -u/--reset on pull gitdir")
                if sub == "fetch":
                    src = _GUARD.get("push_clone")
                    if not src or src not in argv:
                        raise GuardViolation("blocked pull-gitdir fetch from anywhere but the own push clone")


def _first_subcommand(argv):
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("-c", "-C"):
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        return a
    return None


_HOOK_INSTALLED = False


def install_guard(vault: Path, pull_gitdir: Path | None = None, dummy_worktree: Path | None = None,
                  push_clone: Path | None = None):
    global _HOOK_INSTALLED
    roots = {os.path.normpath(os.path.abspath(str(vault))), os.path.realpath(str(vault))}
    _GUARD["roots"] = tuple(sorted(roots))
    _GUARD["pull_gitdir"] = os.path.realpath(str(pull_gitdir)) if pull_gitdir else None
    _GUARD["dummy_worktree"] = str(dummy_worktree) if dummy_worktree else ""
    _GUARD["push_clone"] = os.path.realpath(str(push_clone)) if push_clone else None
    _GUARD["on"] = True
    if not _HOOK_INSTALLED:
        sys.addaudithook(_hook)
        _HOOK_INSTALLED = True


def release_guard():  # tests only; in production the process just exits
    _GUARD["on"] = False


# ---------------------------------------------------------------- helpers

def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def in_quiet_window(now: dt.datetime) -> bool:
    tz = ZoneInfo(SHANGHAI) if ZoneInfo else dt.timezone(dt.timedelta(hours=8))
    local = now.astimezone(tz)
    hm = local.strftime("%H:%M")
    for days, start, end in QUIET_WINDOWS:
        if days is not None and local.weekday() not in days:
            continue
        if start <= hm < end:
            return True
    return False


def in_scope(rel: str) -> bool:
    rel = nfc(rel)
    if not rel or rel.startswith("/") or "\0" in rel:
        return False
    parts = rel.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return False
    if any(p.startswith(".") for p in parts):
        return False
    return any(rel.startswith(nfc(s) + "/") for s in SCOPE)


def is_dataless(st: os.stat_result) -> bool:
    flags = getattr(st, "st_flags", None)
    return bool(flags is not None and flags & SF_DATALESS)


def is_icloud_copy(name: str, siblings: set[str]) -> bool:
    m = COPY_RE.match(name)
    if not m:
        return False
    original = m.group("stem") + (m.group("ext") or "")
    return nfc(original) in siblings


# ---------------------------------------------------------------- git

class Git:
    def __init__(self, git: str, deadline: float, base_args: list[str], cwd: str):
        self.git = git
        self.deadline = deadline
        self.base = base_args
        self.cwd = cwd
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_ASKPASS": "/usr/bin/false",
            "SSH_ASKPASS": "/usr/bin/false",
            "GIT_LITERAL_PATHSPECS": "1",
            "LC_ALL": "C",
        })

    def run(self, *args: str, check: bool = True, timeout: int | None = None,
            input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise Fatal("deadline reached before git " + args[0])
        t = max(1, min(timeout or GIT_TIMEOUT, int(remaining)))
        try:
            cp = subprocess.run([self.git, *self.base, "-c", "core.quotepath=off", *args],
                                input=input_bytes, stdin=None if input_bytes is not None else subprocess.DEVNULL,
                                capture_output=True, env=self.env, timeout=t, cwd=self.cwd)
        except subprocess.TimeoutExpired:
            raise Fatal(f"git {args[0]} timed out after {t}s")
        if check and cp.returncode != 0:
            raise Fatal(f"git {args[0]} rc={cp.returncode}: "
                        f"{cp.stderr.decode('utf-8', 'replace').strip()[:300]}")
        return cp

    def out(self, *args: str) -> str:
        return self.run(*args).stdout.decode("utf-8", "surrogateescape").strip()

    def rev(self, ref: str) -> str | None:
        cp = self.run("rev-parse", "--verify", "--quiet", ref + "^{commit}", check=False)
        return cp.stdout.decode().strip() or None if cp.returncode == 0 else None

    def is_ancestor(self, a: str, b: str) -> bool:
        return self.run("merge-base", "--is-ancestor", a, b, check=False).returncode == 0

    def tree(self, commit: str, paths: tuple[str, ...] = ()) -> dict[str, tuple[str, str, str]]:
        """nfc(path) -> (mode, sha, real_path)"""
        out = self.run("ls-tree", "-r", "-z", "--full-tree", commit, "--", *paths).stdout
        res = {}
        for rec in out.split(b"\0"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            mode, _typ, sha = meta.decode().split(" ")
            p = path.decode("utf-8", "surrogateescape")
            res[nfc(p)] = (mode, sha, p)
        return res


def classify_auth(stderr: str) -> bool:
    s = stderr.lower()
    return any(k in s for k in ("authentication failed", "could not read username", "403",
                                "permission to", "denied", "terminal prompts disabled",
                                "invalid username or password", "write access"))


def classify_rejected(stderr: str) -> bool:
    s = stderr.lower()
    return any(k in s for k in ("non-fast-forward", "fetch first", "[rejected]", "stale info",
                                "updates were rejected"))


# ---------------------------------------------------------------- vault scan (read-only)

class Scan:
    def __init__(self):
        self.files: dict[str, tuple[str, str, float, int]] = {}  # nfc rel -> (sha, real rel, mtime, size)
        self.placeholders: list[str] = []
        self.copies: list[str] = []
        self.unsettled: list[str] = []
        self.too_big: list[str] = []
        self.unreadable: list[str] = []


def read_file(path: Path) -> bytes:
    with open(path, "rb", buffering=0) as f:  # plain read, no mmap
        chunks = []
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            chunks.append(b)
    return b"".join(chunks)


def scan_vault(vault: Path, now_ts: float, settle: float, only: set[str] | None) -> Scan:
    sc = Scan()
    for top in SCOPE:
        root = vault / top
        try:
            os.lstat(root)
        except FileNotFoundError:
            continue
        stack = [(root, top)]
        while stack:
            d, drel = stack.pop()
            try:
                entries = list(os.scandir(d))
            except PermissionError as e:
                raise Fatal(f"vault not readable ({e}); Full Disk Access missing?")
            names = {nfc(e.name) for e in entries}
            for e in entries:
                name = e.name
                rel = f"{drel}/{name}"
                if name.startswith("."):
                    if name.endswith(".icloud") and len(name) > 8:
                        sc.placeholders.append(f"{drel}/{name[1:-7]}")
                    continue
                if is_icloud_copy(nfc(name), names):
                    sc.copies.append(rel)
                    continue
                st = e.stat(follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):
                    stack.append((Path(e.path), rel))
                    continue
                if not stat.S_ISREG(st.st_mode):
                    continue
                key = nfc(rel)
                if only is not None and key not in only:
                    continue
                if is_dataless(st):
                    sc.placeholders.append(rel)
                    continue
                if st.st_size > MAX_FILE_BYTES:
                    sc.too_big.append(rel)
                    continue
                if now_ts - st.st_mtime < settle:
                    sc.unsettled.append(rel)
                    continue
                try:
                    data = read_file(Path(e.path))
                except OSError as ex:
                    if isinstance(ex, PermissionError):
                        raise Fatal(f"vault not readable ({ex}); Full Disk Access missing?")
                    sc.unreadable.append(f"{rel}: {ex.strerror or ex}")
                    continue
                st2 = os.lstat(e.path)
                if (st2.st_mtime, st2.st_size) != (st.st_mtime, st.st_size) or len(data) != st.st_size:
                    sc.unsettled.append(rel)
                    continue
                sc.files[key] = (blob_sha(data), rel, st.st_mtime, st.st_size)
    return sc


def reread_sha(vault: Path, real_rel: str) -> tuple[str | None, float | None, int | None]:
    p = vault / real_rel
    try:
        st = os.lstat(p)
        if is_dataless(st):
            return None, None, None
        return blob_sha(read_file(p)), st.st_mtime, st.st_size
    except OSError:
        return None, None, None


# test hooks (never set in production)
_between_reads_hook = None
_before_push_hook = None
_before_bookkeeping_hook = None


# ---------------------------------------------------------------- main

def load_json(p: Path, default):
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, ValueError):
        return default


def save_json(p: Path, obj) -> None:
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    os.replace(tmp, p)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vault", required=True)
    ap.add_argument("--repo", required=True, help="own push clone, outside iCloud")
    ap.add_argument("--pull-gitdir", required=True, help="Obsidian Git gitdir (read + bookkeeping only)")
    ap.add_argument("--state", required=True)
    ap.add_argument("--log", default=None)
    ap.add_argument("--git", default="git")
    ap.add_argument("--dry-run", action="store_true", help="build the commit, never push, never bookkeep")
    ap.add_argument("--probe-push", action="store_true", help="with --dry-run: git push --dry-run (checks write access, changes nothing)")
    ap.add_argument("--only-paths", default=None, help="file with exact repo paths, one per line (cutover)")
    ap.add_argument("--message", default=None)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--ignore-quiet", action="store_true")
    ap.add_argument("--now", default=None)
    ap.add_argument("--settle-seconds", type=float, default=180.0)
    ap.add_argument("--recheck-seconds", type=float, default=5.0)
    ap.add_argument("--pull-behind-alert-seconds", type=float, default=600.0)
    ap.add_argument("--reject-alert-streak", type=int, default=3)
    ap.add_argument("--max-seconds", type=float, default=120.0)
    args = ap.parse_args(argv)

    started = time.monotonic()
    deadline = started + args.max_seconds
    vault = Path(args.vault)
    repo = Path(args.repo)
    gdir = Path(args.pull_gitdir)
    state = Path(args.state)
    log_p = Path(args.log) if args.log else state / "push.log"
    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    now_ts = now.timestamp() if args.now else time.time()
    stamp = now.isoformat(timespec="seconds")

    st: dict = {"time": stamp, "result": "failed", "dry_run": args.dry_run, "origin": None,
                "pull_head": None, "commit": None, "pushed": False, "paths": [], "numstat": [],
                "headings_added": {}, "skipped": {}, "needs_attention": [], "warnings": [], "errors": []}

    def finish(code: int) -> int:
        st["elapsed_s"] = round(time.monotonic() - started, 2)
        _GUARD_SAVE = _GUARD["on"]
        try:
            state.mkdir(parents=True, exist_ok=True)
            save_json(state / ("status-dryrun.json" if args.dry_run else "status.json"), st)
            line = (f"{stamp} result={st['result']} dry_run={int(args.dry_run)} "
                    f"origin={(st['origin'] or '-')[:8]} pull={(st['pull_head'] or '-')[:8]} "
                    f"commit={(st['commit'] or '-')[:8]} pushed={int(st['pushed'])} files={len(st['paths'])} "
                    f"skipped={ {k: len(v) for k, v in st['skipped'].items() if v} } "
                    f"attention={len(st['needs_attention'])} errors={len(st['errors'])}")
            log_p.parent.mkdir(parents=True, exist_ok=True)
            with open(log_p, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                for a in st["needs_attention"]:
                    f.write(f"{stamp} ATTENTION: {a}\n")
                for e in st["errors"]:
                    f.write(f"{stamp} error: {e}\n")
            print(line)
        except OSError as e:
            print(f"{stamp} could not write status/log: {e}", file=sys.stderr)
        _ = _GUARD_SAVE
        return code

    # ---- static guards
    rv = os.path.realpath(vault)
    for other in (repo, state, log_p.parent, gdir):
        ro = os.path.realpath(other)
        if ro == rv or ro.startswith(rv + os.sep) or rv.startswith(ro + os.sep):
            st["errors"].append(f"guard: {other} overlaps the vault")
            return finish(2)
    if any(x in rv for x in FORBIDDEN_PARTS) or any(x in os.path.realpath(repo) for x in FORBIDDEN_PARTS):
        st["errors"].append("guard: path points into trading folder")
        return finish(2)
    state.mkdir(parents=True, exist_ok=True)
    dummy_wt = state / "empty-worktree"
    dummy_wt.mkdir(exist_ok=True)
    os.chdir(state)
    install_guard(vault, gdir, dummy_wt, repo)

    if not args.dry_run and not args.ignore_quiet and in_quiet_window(now):
        st["result"] = "quiet"
        return finish(0)

    lock_f = open(state / "push.lock", "a+")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
        lock_f.close()
        if e.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
            st["result"] = "locked"
            return finish(0)
        raise
    try:
        try:
            return run_round(args, vault, repo, gdir, state, dummy_wt, now_ts, deadline, st, finish)
        except AuthError as e:
            st["errors"].append(str(e))
            st["needs_attention"].append(f"GitHub 登录或写权限失败：{e}")
            st["result"] = "auth_failed"
            return finish(2)
        except Fatal as e:
            st["errors"].append(str(e))
            st["result"] = "failed"
            if "Full Disk Access" in str(e):
                st["needs_attention"].append("读不了 iCloud 笔记库（磁盘权限）")
            return finish(2)
        except GuardViolation as e:
            st["errors"].append(f"WRITE GUARD: {e}")
            st["needs_attention"].append(f"守门拦下了对笔记库的写入并中止：{e}")
            st["result"] = "guard_abort"
            _GUARD["on"] = False  # allow writing our own status/log outside the vault
            return finish(3)
    finally:
        lock_f.close()


def run_round(args, vault, repo, gdir, state, dummy_wt, now_ts, deadline, st, finish) -> int:
    counters_p = state / "counters.json"
    counters = load_json(counters_p, {})
    synced_p = state / "synced.json"
    synced: dict[str, str] = load_json(synced_p, {})
    pending_p = state / "pending_bookkeeping.json"
    pending = load_json(pending_p, None)

    if not (repo / ".git").exists():
        raise Fatal(f"push clone missing: {repo}")
    if not gdir.is_dir():
        raise Fatal(f"pull gitdir missing: {gdir}")
    g = Git(args.git, deadline, ["-C", str(repo)], str(state))
    pg = Git(args.git, deadline, [f"--git-dir={gdir}", f"--work-tree={dummy_wt}"], str(state))

    # pull gitdir must not be mid-operation
    for marker in ("MERGE_HEAD", "REBASE_HEAD", "CHERRY_PICK_HEAD", "rebase-merge", "rebase-apply"):
        if (gdir / marker).exists():
            st["result"] = "skip_pull_midop"
            st["needs_attention"].append(f"Obsidian Git 的 Git 资料里有 {marker}（合并到一半），本轮不推")
            return finish(0)

    # ---- fetch
    if not args.no_fetch:
        cp = g.run("fetch", "--quiet", "--no-tags", "origin", f"+refs/heads/{BRANCH}:{REMOTE_REF}", check=False)
        if cp.returncode != 0:
            err = cp.stderr.decode("utf-8", "replace")
            if classify_auth(err):
                raise AuthError("fetch: " + err.strip()[:200])
            raise Fatal("fetch failed: " + err.strip()[:200])
    origin = g.rev(REMOTE_REF)
    if not origin:
        raise Fatal("origin/main missing in push clone")
    st["origin"] = origin

    # MacBook still pushing?
    last_origin = counters.get("last_origin")
    if last_origin and last_origin != origin and g.rev(last_origin) and g.is_ancestor(last_origin, origin):
        msgs = g.out("log", "--format=%s", f"{last_origin}..{origin}").splitlines()
        hits = [m for m in msgs if m.startswith(MACBOOK_MARKERS)]
        if hits:
            st["needs_attention"].append(f"GitHub 上又出现了 MacBook 风格的提交：{hits[0]}（MacBook 可能还在推）")

    # ---- pull gate
    phead = pg.rev("HEAD")
    st["pull_head"] = phead
    gate_ok = phead == origin
    if not gate_ok and pending and phead == pending.get("parent") and origin == pending.get("commit"):
        # we are the reason pull HEAD is behind: try bookkeeping now
        ok = bookkeeping(pg, g, vault, pending, st)
        if ok:
            pending_p.unlink(missing_ok=True)
            pending = None
            phead = pg.rev("HEAD")
            st["pull_head"] = phead
            gate_ok = phead == origin
        else:
            gate_ok = True  # files changed again since our push; allowed to push on top of our own commit
    if not gate_ok:
        since = counters.get("pull_behind_since")
        if counters.get("pull_behind_origin") != origin or since is None:
            counters["pull_behind_since"] = now_ts
            counters["pull_behind_origin"] = origin
            since = now_ts
        if now_ts - since >= args.pull_behind_alert_seconds:
            st["needs_attention"].append(
                f"拉取卡住：Obsidian Git 停在 {(phead or '-')[:8]}，GitHub 已到 {origin[:8]}，"
                f"已超过 {int((now_ts - since) // 60)} 分钟")
        try:
            st["skipped"]["both_changed"] = diagnose_both_changed(g, pg, vault, phead, origin)
            if st["skipped"]["both_changed"]:
                st["needs_attention"].append(
                    f"两边都改了（GitHub 和本地都改了同一篇），拉取会一直卡住：{st['skipped']['both_changed'][:5]}")
        except Fatal as e:
            st["warnings"].append(f"diagnose failed: {e}")
        st["result"] = "skip_pull_behind"
        counters["last_origin"] = origin
        save_json(counters_p, counters)
        return finish(0)
    counters.pop("pull_behind_since", None)
    counters.pop("pull_behind_origin", None)
    if pending and (now_ts - pending.get("since", now_ts)) > 1800:
        st["needs_attention"].append("推送后的记账更新超过 30 分钟还没完成")

    # ---- what changed
    only = None
    if args.only_paths:
        wanted = [nfc(l.strip()) for l in Path(args.only_paths).read_text(encoding="utf-8").splitlines() if l.strip()]
        bad = [w for w in wanted if not in_scope(w)]
        if bad:
            raise Fatal(f"--only-paths outside the three folders refused: {bad}")
        only = set(wanted)
    rtree = g.tree(origin, SCOPE)
    ptree = pg.tree(phead, SCOPE) if phead else {}
    sc = scan_vault(vault, now_ts, args.settle_seconds, only)
    skipped = {"placeholder": sc.placeholders, "icloud_copy": sc.copies, "still_writing": sc.unsettled,
               "too_big": sc.too_big, "unreadable": sc.unreadable, "both_changed": [], "vault_stale": [],
               "remote_deleted": [], "missing_in_vault_not_pushed": []}
    st["skipped"] = skipped

    to_push: dict[str, tuple[str, str]] = {}  # repo path -> (real vault rel, sha)
    for key, (sha, real_rel, _mt, _sz) in sorted(sc.files.items()):
        if not in_scope(key):
            continue
        r = rtree.get(key)
        rsha = r[1] if r else None
        if rsha == sha:
            synced[key] = sha
            continue
        if synced.get(key) == rsha:
            base = rsha
        else:
            base = ptree[key][1] if key in ptree else None
        if r is None:
            if key in synced:
                skipped["remote_deleted"].append(key)  # GitHub deleted it; never re-add silently
                continue
            to_push[key] = (real_rel, sha)
            continue
        if base is not None and rsha != base:
            if sha == base:
                skipped["vault_stale"].append(key)
            else:
                skipped["both_changed"].append(key)
            continue
        if older_version(g, origin, r[2], sha):
            skipped["vault_stale"].append(key)
            continue
        to_push[key] = (real_rel, sha)
    if only is None:
        for key in rtree:
            if key not in sc.files and in_scope(key) and \
                    key not in {nfc(x) for x in sc.placeholders + sc.copies + sc.unsettled + sc.too_big}:
                skipped["missing_in_vault_not_pushed"].append(key)
    else:
        missing = sorted(only - set(sc.files))
        if missing:
            st["warnings"].append(f"only-paths not readable/settled in vault: {missing}")

    if skipped["both_changed"]:
        st["needs_attention"].append(f"两边都改了，没推：{skipped['both_changed'][:5]}")
    if skipped["vault_stale"]:
        st["needs_attention"].append(f"笔记库里是旧版本，没推：{skipped['vault_stale'][:5]}")
    if skipped["remote_deleted"]:
        st["needs_attention"].append(f"GitHub 上删掉了、本地还在，没推：{skipped['remote_deleted'][:5]}")

    # settle recheck on candidates
    if to_push and args.recheck_seconds > 0:
        time.sleep(args.recheck_seconds)
    if _between_reads_hook:
        _between_reads_hook()
    for key in list(to_push):
        real_rel, sha = to_push[key]
        s2, _m, _s = reread_sha(vault, real_rel)
        if s2 != sha:
            skipped["still_writing"].append(real_rel)
            del to_push[key]

    if not to_push:
        st["result"] = "noop"
        counters["last_origin"] = origin
        save_json(synced_p, synced)
        save_json(counters_p, counters)
        return finish(0)

    # ---- build commit in own clone (outside iCloud)
    g.run("reset", "--hard", "-q", REMOTE_REF)
    root = os.path.realpath(repo)
    paths = []
    for key, (real_rel, sha) in sorted(to_push.items()):
        rp = rtree[key][2] if key in rtree else key
        dst = repo / rp
        if not os.path.realpath(dst.parent if dst.parent.exists() else repo).startswith(root):
            raise Fatal(f"refusing write outside clone: {dst}")
        data = read_file(vault / real_rel)
        if blob_sha(data) != sha:
            skipped["still_writing"].append(real_rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
        paths.append(rp)
    if not paths:
        st["result"] = "noop"
        return finish(0)
    for i in range(0, len(paths), 100):
        g.run("add", "--", *paths[i:i + 100])
    ns = g.run("diff", "--cached", "--name-status", "-z", "--no-renames").stdout.split(b"\0")
    staged = []
    for j in range(0, len(ns) - 1, 2):
        stt, p = ns[j].decode(), ns[j + 1].decode("utf-8", "surrogateescape")
        staged.append((stt, p))
    if any(s[0] not in ("A", "M") for s in staged):
        g.run("reset", "--hard", "-q", REMOTE_REF)
        raise Fatal(f"staged set contains non add/modify entries: {staged[:5]}")
    if sorted(nfc(p) for _, p in staged) != sorted(nfc(p) for p in paths) or \
            not all(in_scope(p) for _, p in staged):
        g.run("reset", "--hard", "-q", REMOTE_REF)
        raise Fatal("staged set differs from intended exact paths")
    numstat = []
    heads = {}
    for line in g.out("diff", "--cached", "--numstat").splitlines():
        a, d, p = line.split("\t", 2)
        numstat.append({"path": p, "added": a, "removed": d})
    for p in paths:
        diff = g.run("diff", "--cached", "-U0", "--", p).stdout.decode("utf-8", "replace")
        h = [l[1:].strip() for l in diff.splitlines() if l.startswith("+#") and not l.startswith("+++")]
        if h:
            heads[p] = h
    st["numstat"] = numstat
    st["headings_added"] = heads
    st["paths"] = paths
    msg = args.message or f"{COMMIT_PREFIX} ({len(paths)} files)"
    g.run("-c", f"user.name={COMMIT_NAME}", "-c", f"user.email={COMMIT_EMAIL}",
          "commit", "-q", "--no-verify", "-m", msg)
    commit = g.rev("HEAD")
    st["commit"] = commit

    if args.dry_run:
        if args.probe_push:
            cp = g.run("push", "--dry-run", "--porcelain", "origin", f"HEAD:refs/heads/{BRANCH}", check=False)
            err = cp.stderr.decode("utf-8", "replace")
            st["probe_push"] = {"rc": cp.returncode, "out": cp.stdout.decode("utf-8", "replace").strip()[-300:],
                                "err": err.strip()[-300:]}
        st["result"] = "dry_run_ok"
        return finish(0)

    # ---- push (never forced)
    if _before_push_hook:
        _before_push_hook()
    cp = g.run("push", "--porcelain", "origin", f"HEAD:refs/heads/{BRANCH}", check=False, timeout=120)
    err = cp.stderr.decode("utf-8", "replace") + cp.stdout.decode("utf-8", "replace")
    if cp.returncode != 0:
        g.run("reset", "--hard", "-q", REMOTE_REF)  # drop the unpushed commit; clone is outside iCloud
        st["commit_dropped"] = commit
        if classify_rejected(err):
            counters["reject_streak"] = counters.get("reject_streak", 0) + 1
            if counters["reject_streak"] >= args.reject_alert_streak:
                st["needs_attention"].append(f"连续 {counters['reject_streak']} 轮推送被 GitHub 拒收")
            st["result"] = "push_rejected"
            save_json(counters_p, counters)
            return finish(1)
        if classify_auth(err):
            raise AuthError("push: " + err.strip()[:200])
        raise Fatal("push failed: " + err.strip()[:200])
    counters["reject_streak"] = 0
    st["pushed"] = True
    g.run("update-ref", REMOTE_REF, commit)
    for key, (_rr, sha) in to_push.items():
        synced[key] = sha
    save_json(synced_p, synced)
    counters["last_origin"] = commit
    counters["last_push"] = st["time"]
    counters["last_push_commit"] = commit
    save_json(counters_p, counters)

    # ---- bookkeeping on the pull gitdir (never touches the vault)
    parent = pending["parent"] if pending else phead
    pend = {"commit": commit, "parent": parent, "since": now_ts}
    if _before_bookkeeping_hook:
        _before_bookkeeping_hook()
    if bookkeeping(pg, g, vault, pend, st):
        pending_p.unlink(missing_ok=True)
        st["result"] = "pushed"
    else:
        save_json(pending_p, pend)
        st["result"] = "pushed_bookkeeping_pending"
    return finish(0)


def diagnose_both_changed(g: Git, pg: Git, vault: Path, phead: str | None, origin: str) -> list[str]:
    """In-scope files changed upstream since pull HEAD and also changed in the vault."""
    if not phead or g.rev(phead) is None:
        return []
    rt = g.tree(origin, SCOPE)
    pt = g.tree(phead, SCOPE)
    out = []
    for key in sorted(set(rt) | set(pt)):
        if rt.get(key, (0, None))[1] == pt.get(key, (0, None))[1]:
            continue
        base = pt.get(key)
        if base is None:
            continue
        real = find_real(vault, base[2])
        cur = reread_sha(vault, real)[0] if real else None
        if cur is not None and cur != base[1] and cur != rt.get(key, (0, None))[1]:
            out.append(key)
    return out


def older_version(g: Git, origin: str, real_path: str, sha: str, limit: int = 50) -> bool:
    out = g.run("log", f"-{limit}", "--format=%H", origin, "--", real_path, check=False).stdout.decode().split()
    for c in out[1:]:
        cp = g.run("rev-parse", "--verify", "--quiet", f"{c}:{real_path}", check=False)
        if cp.returncode == 0 and cp.stdout.decode().strip() == sha:
            return True
    return False


def bookkeeping(pg: Git, g: Git, vault: Path, pend: dict, st: dict) -> bool:
    """Move the pull gitdir HEAD + index from `parent` to our `commit`, without touching the vault."""
    commit, parent = pend["commit"], pend["parent"]
    phead = pg.rev("HEAD")
    if phead == commit:
        return True
    if phead != parent:
        st["warnings"].append(f"bookkeeping skipped: pull HEAD {str(phead)[:8]} != expected {str(parent)[:8]}")
        return False
    if pg.rev(commit) is None:
        # copy the objects from our own clone (local, outside iCloud); no refs, no FETCH_HEAD
        src = _GUARD.get("push_clone") or os.path.realpath(g.base[1])
        cp = pg.run("fetch", "-q", "--no-tags", "--no-write-fetch-head", src, commit, check=False)
        if cp.returncode != 0 or pg.rev(commit) is None:
            st["warnings"].append("bookkeeping waiting: could not copy pushed commit into pull gitdir")
            return False
    authors = g.out("log", "--format=%an", f"{parent}..{commit}").splitlines()
    if not authors or any(a != COMMIT_NAME for a in authors):
        st["warnings"].append("bookkeeping skipped: commits from others in range")
        return False
    changed = g.run("diff", "--name-only", "-z", "--no-renames", parent, commit).stdout.split(b"\0")
    ctree = g.tree(commit)
    for raw in changed:
        if not raw:
            continue
        p = raw.decode("utf-8", "surrogateescape")
        ent = ctree.get(nfc(p))
        if ent is None:
            st["warnings"].append(f"bookkeeping skipped: {p} deleted in range")
            return False
        s, _m, _s = reread_sha(vault, p)
        if s is None:
            from_vault = find_real(vault, p)
            s = reread_sha(vault, from_vault)[0] if from_vault else None
        if s != ent[1]:
            st["warnings"].append(f"bookkeeping waiting: vault {p} differs from pushed version")
            return False
    head_ref = pg.out("symbolic-ref", "-q", "HEAD")
    cp = pg.run("read-tree", "-m", commit, check=False)
    if cp.returncode != 0:
        st["warnings"].append("bookkeeping retry later: read-tree " + cp.stderr.decode("utf-8", "replace").strip()[:120])
        return False
    cp = pg.run("update-ref", "-m", "imac-pusher: bookkeeping after own push", head_ref, commit, parent, check=False)
    if cp.returncode != 0:
        st["warnings"].append("bookkeeping retry later: update-ref " + cp.stderr.decode("utf-8", "replace").strip()[:120])
        return False
    st["bookkept"] = commit
    return True


def find_real(vault: Path, rel: str) -> str | None:
    cur = vault
    out = []
    for part in rel.split("/"):
        try:
            names = os.listdir(cur)
        except OSError:
            return None
        hit = next((n for n in names if nfc(n) == nfc(part)), None)
        if hit is None:
            return None
        out.append(hit)
        cur = cur / hit
    return "/".join(out)


if __name__ == "__main__":
    sys.exit(main())
