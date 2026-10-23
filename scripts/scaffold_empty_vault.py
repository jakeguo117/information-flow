#!/usr/bin/env python3
"""Create an empty information-flow vault from templates/empty-vault.

Mode A: private git vault. Clone or init, commit the template locally, do not
push. Mode B: local or mounted directory. No git init unless --git-init.

Re-entry, when .infoflow/vault.json exists and template_id matches, only
adds missing template directories and files. It does not delete or overwrite
existing files, and it does not run an inbox index.

S1 and S2 (pick A/B in a UI, then connect a source, with posting left out)
are manual Workflow checks. This command is the step-2 scaffold only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from infoflow_config import (  # noqa: E402
    reject_placeholder,
    write_user_config,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PLUGIN_ROOT / "templates" / "empty-vault"
MARKER_REL = Path(".infoflow") / "vault.json"
HONG_KONG = ZoneInfo("Asia/Hong_Kong")
GIT_TIMEOUT_S = 20
FORBIDDEN_GIT = {"push", "send-pack"}


class ScaffoldError(Exception):
    """Expected scaffold failure. The vault is not reported as ready."""


def template_meta() -> dict:
    path = TEMPLATE_ROOT / MARKER_REL
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScaffoldError(f"template marker unreadable: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScaffoldError(f"template marker is not an object: {path}")
    for key in ("template_id", "template_version"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ScaffoldError(f"template marker missing {key}: {path}")
    return data


def template_files() -> list[Path]:
    if not TEMPLATE_ROOT.is_dir():
        raise ScaffoldError(f"missing template: {TEMPLATE_ROOT}")
    found: list[Path] = []
    for path in TEMPLATE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(TEMPLATE_ROOT)
        if any(part in {"..", ""} for part in rel.parts):
            raise ScaffoldError(f"refusing template path: {rel}")
        found.append(rel)
    if not found:
        raise ScaffoldError(f"template is empty: {TEMPLATE_ROOT}")
    return sorted(found, key=lambda item: item.as_posix())


def write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def hong_kong_now() -> str:
    return datetime.now(HONG_KONG).isoformat(timespec="seconds")


def logical_path(path: Path) -> Path:
    path = path.expanduser()
    if not path.is_absolute():
        raise ScaffoldError(f"vault_root must be an absolute path: {path}")
    return path.resolve()


def assert_outside_code_repo(path: Path) -> Path:
    target = logical_path(path)
    root = PLUGIN_ROOT.resolve()
    if target == root or root in target.parents:
        raise ScaffoldError(
            "refusing to use the information-flow code repository as vault_root: "
            f"{target}"
        )
    template = TEMPLATE_ROOT.resolve()
    if target == template or template in target.parents or target in template.parents:
        raise ScaffoldError(f"refusing to scaffold into the template package: {target}")
    return target


def run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    if args and args[0] in FORBIDDEN_GIT:
        raise ScaffoldError("refusing to push during vault scaffold")
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScaffoldError(f"git {' '.join(args)} timed out") from exc
    except OSError as exc:
        raise ScaffoldError(f"git {' '.join(args)} failed: {exc}") from exc
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ScaffoldError(f"git {' '.join(args)} failed: {detail}")
    return result


def read_marker(vault: Path) -> dict | None:
    path = vault / MARKER_REL
    if not path.exists():
        return None
    if not path.is_file():
        raise ScaffoldError(f"vault marker is not a file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScaffoldError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScaffoldError(f"vault marker is not an object: {path}")
    return data


def has_commits(vault: Path) -> bool:
    if not (vault / ".git").exists():
        return False
    result = run_git(["rev-parse", "--verify", "HEAD"], cwd=vault, check=False)
    return result.returncode == 0


def classify(vault: Path) -> str:
    if not vault.exists():
        return "missing"
    if not vault.is_dir():
        return "not-dir"
    if read_marker(vault) is not None:
        return "marked"
    for child in vault.iterdir():
        if child.name == ".git":
            continue
        return "conflict"
    if has_commits(vault):
        return "conflict"
    return "empty"


def assert_remote_accessible(remote: str) -> None:
    result = run_git(["ls-remote", remote], check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ScaffoldError(
            f"git remote not accessible (auth, network, or missing repo): {remote}: {detail}"
        )


def ensure_remote(vault: Path, remote: str) -> None:
    existing = run_git(["remote", "get-url", "origin"], cwd=vault, check=False)
    if existing.returncode != 0:
        run_git(["remote", "add", "origin", remote], cwd=vault)
        return
    if existing.stdout.strip() != remote:
        run_git(["remote", "set-url", "origin", remote], cwd=vault)


def ensure_branch(vault: Path, branch: str) -> None:
    if not has_commits(vault):
        current = run_git(["symbolic-ref", "--short", "HEAD"], cwd=vault, check=False)
        if current.returncode == 0 and current.stdout.strip() == branch:
            return
        run_git(["checkout", "-B", branch], cwd=vault)
        return
    local = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=vault, check=False)
    remote = run_git(
        ["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        cwd=vault,
        check=False,
    )
    if local.returncode != 0 and remote.returncode != 0:
        raise ScaffoldError(f"branch {branch} not found in the vault repo")
    run_git(["checkout", branch], cwd=vault)


def clone_repo(vault: Path, remote: str, branch: str) -> None:
    result = run_git(["clone", "--", remote, str(vault)], check=False)
    if result.returncode != 0:
        if vault.exists():
            shutil.rmtree(vault)
        detail = (result.stderr or result.stdout or "").strip()
        raise ScaffoldError(f"git clone failed: {detail}")
    ensure_remote(vault, remote)
    ensure_branch(vault, branch)


def init_repo(vault: Path, remote: str, branch: str) -> None:
    if not vault.exists():
        vault.mkdir(parents=True)
    if not (vault / ".git").exists():
        run_git(["init", "-b", branch, str(vault)])
    ensure_remote(vault, remote)
    ensure_branch(vault, branch)


def init_local_git(vault: Path) -> None:
    if (vault / ".git").exists():
        return
    run_git(["init", "-b", "main", str(vault)])


def ensure_identity(vault: Path) -> None:
    """Set a non-personal identity only when the repo has none."""
    name = run_git(["config", "user.name"], cwd=vault, check=False)
    email = run_git(["config", "user.email"], cwd=vault, check=False)
    if name.returncode != 0 or not name.stdout.strip():
        run_git(["config", "user.name", "information-flow"], cwd=vault)
    if email.returncode != 0 or not email.stdout.strip():
        run_git(["config", "user.email", "information-flow@localhost"], cwd=vault)


def commit_paths(vault: Path, paths: list[Path], message: str) -> str:
    if not paths:
        return ""
    ensure_identity(vault)
    rels = [path.relative_to(vault).as_posix() for path in paths]
    allowed = {rel.as_posix() for rel in template_files()}
    unexpected = sorted(rel for rel in rels if rel not in allowed)
    if unexpected:
        raise ScaffoldError(f"refusing to commit unexpected path: {unexpected[0]}")
    run_git(["add", "--", *rels], cwd=vault)
    staged = [
        line
        for line in run_git(
            ["-c", "core.quotepath=false", "diff", "--cached", "--name-only"],
            cwd=vault,
        ).stdout.splitlines()
        if line
    ]
    extra = sorted(name for name in staged if name not in allowed)
    if extra:
        run_git(["reset", "-q", "--", *rels], cwd=vault, check=False)
        raise ScaffoldError(f"refusing to commit unexpected path: {extra[0]}")
    if not staged:
        return ""
    run_git(["commit", "-m", message], cwd=vault)
    return run_git(["rev-parse", "HEAD"], cwd=vault).stdout.strip()


def render_marker(mode: str) -> bytes:
    meta = template_meta()
    payload = {
        "template_id": meta["template_id"],
        "template_version": meta["template_version"],
        "storage_mode": mode,
        "created_at": hong_kong_now(),
    }
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


class TreeWriter:
    def __init__(self, root: Path, created_root: bool) -> None:
        self.root = root
        self.created_root = created_root
        self.created: list[Path] = []
        self.created_git = False
        self.done = False

    def wrote(self, path: Path) -> None:
        self.created.append(path)

    def rollback(self) -> None:
        if self.done:
            return
        if self.created_root and self.root.exists():
            shutil.rmtree(self.root)
            return
        for path in reversed(self.created):
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
        if self.created_git:
            git_dir = self.root / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
        for path in reversed(self.created):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass

    def success(self) -> None:
        self.done = True


def remember_new_dirs(path: Path, writer: TreeWriter | None) -> None:
    missing: list[Path] = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    path.mkdir(parents=True, exist_ok=True)
    if writer is None:
        return
    for directory in reversed(missing):
        if directory.is_dir():
            writer.wrote(directory)


def place_file(dest: Path, data: bytes, writer: TreeWriter | None) -> None:
    remember_new_dirs(dest.parent, writer)
    if writer is not None:
        writer.wrote(dest)
    try:
        write_bytes(dest, data)
    except OSError as exc:
        raise ScaffoldError(f"failed to write {dest}: {exc.strerror or exc}") from exc


def copy_missing(vault: Path, *, fresh: bool, mode: str, writer: TreeWriter | None) -> list[Path]:
    written: list[Path] = []
    for rel in template_files():
        if rel.as_posix() == MARKER_REL.as_posix():
            continue
        dest = vault / rel
        if dest.exists():
            if fresh:
                raise ScaffoldError(f"refusing to overwrite {dest}")
            continue
        place_file(dest, (TEMPLATE_ROOT / rel).read_bytes(), writer)
        written.append(dest)
    marker = vault / MARKER_REL
    if fresh or not marker.exists():
        if marker.exists():
            raise ScaffoldError(f"refusing to overwrite {marker}")
        place_file(marker, render_marker(mode), writer)
        written.append(marker)
    return written


def matching_marker(vault: Path) -> dict:
    marker = read_marker(vault)
    if marker is None:
        raise ScaffoldError(f"missing vault marker: {vault / MARKER_REL}")
    expected = template_meta()["template_id"]
    found = marker.get("template_id")
    if found != expected:
        raise ScaffoldError(
            f"vault template_id is {found!r}; this scaffold only soft-fills {expected!r}"
        )
    return marker


def config_updates(mode: str, vault: Path, remote: str | None, branch: str | None) -> dict:
    updates = {"vault_root": str(vault), "storage_mode": mode}
    if mode == "A":
        updates["git_remote"] = remote
        updates["git_branch"] = branch
    return updates


def finish_config(config_path: Path, updates: dict, vault: Path) -> None:
    try:
        write_user_config(config_path, updates)
    except OSError as exc:
        raise ScaffoldError(
            f"vault is on disk at {vault} but config write failed: {config_path}: {exc}"
        ) from exc


def soft_fill(vault: Path, mode: str, remote: str | None, branch: str | None, config_path: Path) -> int:
    matching_marker(vault)
    written = copy_missing(vault, fresh=False, mode=mode, writer=None)
    if mode == "A" and written and (vault / ".git").is_dir():
        commit_paths(vault, written, "fill missing empty-vault template paths")
    finish_config(config_path, config_updates(mode, vault, remote, branch), vault)
    print(f"vault already initialized: {vault}")
    if written:
        print(f"filled {len(written)} missing template path(s); existing files were left unchanged")
    else:
        print("no missing template paths; existing files were left unchanged")
    print("vault.json was left unchanged")
    return 0


def prepare_mode_a(vault: Path, remote: str, branch: str, writer: TreeWriter) -> str:
    assert_remote_accessible(remote)
    if not vault.exists():
        clone_repo(vault, remote, branch)
        writer.created_root = True
        return classify(vault)
    if not (vault / ".git").exists():
        writer.created_git = True
    init_repo(vault, remote, branch)
    return classify(vault)


def scaffold(
    mode: str,
    vault_root: str,
    *,
    remote: str | None,
    branch: str,
    config_path: Path,
    git_init: bool,
) -> None:
    if mode not in {"A", "B"}:
        raise ScaffoldError(f"storage mode must be A or B, got {mode!r}")
    if mode == "A":
        if not remote:
            raise ScaffoldError("mode A requires --git-remote")
        remote = reject_placeholder(remote, "git_remote")
        branch = reject_placeholder(branch, "git_branch")
    vault = assert_outside_code_repo(Path(vault_root))
    state = classify(vault)
    if state == "not-dir":
        raise ScaffoldError(f"vault_root is not a directory: {vault}")
    if state == "conflict":
        raise ScaffoldError(
            f"vault_root is not empty and has no empty-vault marker: {vault}"
        )
    if state == "marked":
        soft_fill(vault, mode, remote, branch, config_path)
        return

    created_root = not vault.exists()
    writer = TreeWriter(vault, created_root)
    try:
        if mode == "A":
            assert remote is not None
            state = prepare_mode_a(vault, remote, branch, writer)
            if state == "marked":
                found = read_marker(vault)
                expected = template_meta()["template_id"]
                if found is None or found.get("template_id") != expected:
                    raise ScaffoldError(
                        "git remote is not an empty information-flow vault; nothing was committed"
                    )
                writer.success()
                soft_fill(vault, mode, remote, branch, config_path)
                return
            if state == "conflict":
                raise ScaffoldError(
                    "git remote is not empty and has no empty-vault marker; "
                    "nothing was committed"
                )
            if state not in {"empty", "missing"}:
                raise ScaffoldError(f"unexpected vault state after git prepare: {state}")
        else:
            if not vault.exists():
                vault.mkdir(parents=True)
                writer.created_root = True
            if git_init and not (vault / ".git").exists():
                writer.created_git = True
                init_local_git(vault)
        written = copy_missing(vault, fresh=True, mode=mode, writer=writer)
        if mode == "A":
            commit_paths(vault, written, "initialize empty information-flow vault")
        writer.success()
    except ScaffoldError:
        writer.rollback()
        raise
    except OSError as exc:
        writer.rollback()
        raise ScaffoldError(f"failed to write vault: {exc.strerror or exc}") from exc

    finish_config(config_path, config_updates(mode, vault, remote, branch), vault)
    print(f"vault ready: {vault}")
    print(f"storage_mode={mode}")
    if mode == "A":
        print("template committed in the vault repo; not pushed")
    elif git_init:
        print("local git initialized; no commit and no remote were added")
    else:
        print("no git init")
    print("next: connect an input source when you want; a first index run is not required")


def default_config_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("INFOFLOW_CONFIG")
    if env:
        return Path(env).expanduser()
    return PLUGIN_ROOT / "config.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scaffold an empty information-flow vault. "
            "Mode A commits the template locally and does not push. "
            "Mode B writes directories only (git init is off unless --git-init). "
            "Does not run an inbox index and does not set up posting."
        )
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    mode_a = sub.add_parser("A", help="private git vault repo")
    mode_a.add_argument("--vault-root", required=True, help="absolute local path for the vault")
    mode_a.add_argument("--git-remote", required=True, help="git remote URL for the vault repo")
    mode_a.add_argument("--branch", default="main")
    mode_a.add_argument("--config", help="user config.json to write")
    mode_b = sub.add_parser("B", help="local or mounted directory")
    mode_b.add_argument("--vault-root", required=True, help="absolute local or mounted path")
    mode_b.add_argument(
        "--git-init",
        action="store_true",
        help="optional local git init; off by default; does not commit or add a remote",
    )
    mode_b.add_argument("--config", help="user config.json to write")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    remote = getattr(args, "git_remote", None)
    branch = getattr(args, "branch", "main")
    git_init = bool(getattr(args, "git_init", False))
    try:
        scaffold(
            args.mode,
            args.vault_root,
            remote=remote,
            branch=branch,
            config_path=default_config_path(args.config),
            git_init=git_init,
        )
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except SystemExit as exc:
        if exc.code in (0, None):
            return 0
        message = exc.code if isinstance(exc.code, str) else "config error"
        print(f"error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
