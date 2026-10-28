#!/usr/bin/env python3
"""Create-only weekday cluster files for the ChatGPT daily-cluster skill.

Normal saves require the same confirmation phrases as write_journal and write
``📋 Digests/cluster/YYYY-MM-DD.md`` (multi-day ``YYYY-MM-DD_DD.md``).
Scheduled saves skip that phrase and may only create the ``-gpt`` sibling.
Neither mode overwrites, and neither writes ``📋 Digests/daily``.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_JOURNAL_TOOLS = Path(__file__).resolve().parents[2] / "journal" / "tools"
if str(_JOURNAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(_JOURNAL_TOOLS))

import journal_lib  # noqa: E402

CLUSTER_DIR = "📋 Digests/cluster"
DAILY_MARK = "Digests/daily"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SPAN_RE = re.compile(r"^\d{2}$")
NAME_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:_(?P<span>\d{2}))?(?P<gpt>-gpt)?\.md$"
)
SKIP_MESSAGE = "skipped: already exists"
ALREADY_MESSAGE = "今天已归"
DAILY_MESSAGE = "拒绝写入 📋 Digests/daily"
MAIN_MESSAGE = "scheduled mode refuses the main file"
GPT_MESSAGE = "normal mode writes the main file, not -gpt"


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def confirmation_granted(approval: dict[str, Any]) -> bool:
    return journal_lib.confirmation_granted(approval)


def commit_message_for(filename: str) -> str:
    """``cluster:`` plus the filename stem. Main files use ``YYYY-MM-DD``."""
    if not filename.endswith(".md"):
        raise ValueError("cluster filename must end with .md")
    return f"cluster: {filename[:-3]}"


def _is_daily(path: str) -> bool:
    posix = path.replace("\\", "/").strip()
    return DAILY_MARK in posix


def checked_filename(date: str, span_end: str | None, scheduled: bool) -> str:
    if not isinstance(date, str) or DATE_RE.fullmatch(date) is None:
        raise ValueError("date must be YYYY-MM-DD")
    start = datetime.date.fromisoformat(date)
    suffix = "-gpt" if scheduled else ""
    if span_end is None or span_end == "":
        return f"{start.isoformat()}{suffix}.md"
    if not isinstance(span_end, str) or SPAN_RE.fullmatch(span_end) is None:
        raise ValueError("span end must be DD")
    try:
        end = start.replace(day=int(span_end))
    except ValueError as exc:
        raise ValueError("span end day is not in this month") from exc
    if end <= start:
        raise ValueError("span end day must be after the start date")
    return f"{start.isoformat()}_{span_end}{suffix}.md"


def relative_for(filename: str) -> str:
    match = NAME_RE.fullmatch(filename)
    if match is None:
        raise ValueError("cluster filename must be YYYY-MM-DD.md or YYYY-MM-DD_DD.md")
    return f"{CLUSTER_DIR}/{filename}"


def assert_cluster_relative(relative: str) -> str:
    if not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")):
        raise ValueError("unsafe cluster path")
    if "\\" in relative or "\x00" in relative:
        raise ValueError("unsafe cluster path")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe cluster path")
    posix = path.as_posix()
    if _is_daily(posix):
        raise ValueError(DAILY_MESSAGE)
    prefix = f"{CLUSTER_DIR}/"
    if not posix.startswith(prefix) or posix.count("/") != 2:
        raise ValueError("cluster path must be 📋 Digests/cluster/YYYY-MM-DD.md")
    if NAME_RE.fullmatch(path.name) is None:
        raise ValueError("cluster filename must be YYYY-MM-DD.md or YYYY-MM-DD_DD.md")
    return posix


def _validate_body(date: str, body: str) -> None:
    if not isinstance(body, str) or body == "":
        raise ValueError("body must be the cluster markdown")
    if body.startswith("---"):
        raise ValueError("cluster file must not have frontmatter")
    lines = body.splitlines()
    if not lines or lines[0] != f"# Digests cluster · {date}":
        raise ValueError("first line must be # Digests cluster · YYYY-MM-DD")
    quotes = [line for line in lines if line.startswith(">")]
    if len(quotes) != 1:
        raise ValueError("cluster file needs exactly one > quote line")
    quote_at = lines.index(quotes[0])
    if quote_at == 0 or any(line.strip() for line in lines[1:quote_at]):
        raise ValueError("quote line must follow the title")
    if not any(line.startswith("## ") for line in lines[quote_at + 1 :]):
        raise ValueError("cluster file needs ## sections")


def _vault(vault: Path) -> Path:
    if not vault.is_dir():
        raise OSError("vault missing")
    if vault.is_symlink():
        raise OSError("refusing to use a symlinked vault")
    return vault


def _reject_symlink_parents(vault: Path) -> Path:
    parent = vault / "📋 Digests"
    root = parent / "cluster"
    if parent.is_symlink() or root.is_symlink():
        raise OSError("refusing to write through a symlink")
    probe = root.resolve() if root.exists() else vault.resolve() / "📋 Digests" / "cluster"
    try:
        probe.relative_to(vault.resolve())
    except ValueError as exc:
        raise OSError("cluster path escapes the vault") from exc
    return root


def _create_exclusive(path: Path, text: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise OSError("refusing to write through a symlink")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    readback = path.read_text(encoding="utf-8")
    if readback != text:
        try:
            path.unlink()
        except OSError:
            pass
        raise OSError("readback did not match")


def _fail(status: str, message: str, **extra: Any) -> tuple[dict[str, Any], bool]:
    payload: dict[str, Any] = {"status": status, "message": message, "files_written": 0}
    payload.update(extra)
    return payload, False


def perform(
    vault: Path,
    action: str,
    approval: dict[str, Any],
    *,
    scheduled: bool = False,
) -> tuple[dict[str, Any], bool]:
    if action not in {"save", "retry"}:
        return _fail("unavailable", "action must be save or retry")
    given = approval.get("path")
    if isinstance(given, str) and _is_daily(given):
        return _fail("refused", DAILY_MESSAGE)
    if not scheduled and not confirmation_granted(approval):
        return _fail(
            "refused",
            "cluster save requires confirmed=true and phrase 可以写, 写吧, or OK 写",
        )
    if not vault.is_dir():
        return _fail("unavailable", "vault missing; cluster will not be written elsewhere")
    try:
        _vault(vault)
        date = str(approval.get("date") or "")
        span = approval.get("span_end")
        if span is None:
            span = ""
        filename = checked_filename(date, str(span) if span != "" else None, scheduled)
        relative = relative_for(filename)
        if isinstance(given, str) and given.replace("\\", "/") != relative:
            if scheduled and not given.endswith("-gpt.md"):
                raise ValueError(MAIN_MESSAGE)
            if not scheduled and given.endswith("-gpt.md"):
                raise ValueError(GPT_MESSAGE)
            raise ValueError("path does not match the cluster filename for this date")
        if scheduled and not filename.endswith("-gpt.md"):
            raise ValueError(MAIN_MESSAGE)
        if not scheduled and filename.endswith("-gpt.md"):
            raise ValueError(GPT_MESSAGE)
        _reject_symlink_parents(vault)
    except ValueError as exc:
        message = str(exc)
        status = "refused" if message in {DAILY_MESSAGE, MAIN_MESSAGE, GPT_MESSAGE} else "validation_error"
        return _fail(status, message)
    except OSError as exc:
        return _fail("unavailable", str(exc))

    target = vault / relative
    if scheduled and target.is_file() and not target.is_symlink():
        return {
            "status": "skipped",
            "message": SKIP_MESSAGE,
            "path": str(target),
            "relative": relative,
            "files_written": 0,
        }, True
    try:
        body = approval.get("body")
        if not isinstance(body, str):
            raise ValueError("body must be the cluster markdown")
        _validate_body(date, body)
    except ValueError as exc:
        return _fail("validation_error", str(exc))
    expected = approval.get("payload_sha256")
    actual = fingerprint(body)
    if not isinstance(expected, str) or expected != actual:
        return _fail("stale_approval", "approval payload_sha256 does not match the cluster body")
    if target.exists() or target.is_symlink():
        try:
            existing = target.read_text(encoding="utf-8") if target.is_file() and not target.is_symlink() else None
        except (OSError, UnicodeError) as exc:
            return _fail("unavailable", str(exc))
        if existing == body:
            return {
                "status": "success",
                "already_persisted": True,
                "message": "重复送达，只留一份",
                "path": str(target),
                "relative": relative,
                "fingerprint": fingerprint(existing),
                "files_written": 0,
            }, True
        return _fail("refused", ALREADY_MESSAGE, path=str(target), relative=relative)
    try:
        _create_exclusive(target, body)
        readback = target.read_text(encoding="utf-8")
    except FileExistsError:
        try:
            existing = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return _fail("unavailable", str(exc))
        if scheduled:
            return {
                "status": "skipped",
                "message": SKIP_MESSAGE,
                "path": str(target),
                "relative": relative,
                "files_written": 0,
            }, True
        if existing == body:
            return {
                "status": "success",
                "already_persisted": True,
                "message": "重复送达，只留一份",
                "path": str(target),
                "relative": relative,
                "fingerprint": fingerprint(existing),
                "files_written": 0,
            }, True
        return _fail("refused", ALREADY_MESSAGE, path=str(target), relative=relative)
    except OSError as exc:
        return _fail("unavailable", f"write failed: {exc}")
    if readback != body or readback.startswith("---"):
        try:
            target.unlink()
        except OSError:
            pass
        return _fail("conflict", "readback did not match the cluster body; file removed")
    return {
        "status": "success",
        "already_persisted": False,
        "path": str(target),
        "relative": relative,
        "fingerprint": fingerprint(readback),
        "files_written": 1,
    }, True


def github_contents_create_body(
    path: str,
    content: bytes,
    message: str,
    branch: str = "main",
) -> dict[str, str]:
    """Body for a GitHub contents create call. Never includes sha."""
    posix = assert_cluster_relative(path)
    if not message.strip() or "\n" in message or "sha" in message.lower():
        raise ValueError("unsafe commit message")
    if message != commit_message_for(Path(posix).name):
        raise ValueError("commit message must be cluster: <filename stem>")
    if branch != "main":
        raise ValueError("contents create branch must be main")
    body = {
        "message": message,
        "content": base64.b64encode(content).decode("ascii"),
        "branch": branch,
    }
    if "sha" in body:
        raise RuntimeError("create body must not carry sha")
    return body


def contents_body_for(vault: Path, relative: str) -> dict[str, str]:
    posix = assert_cluster_relative(relative)
    target = vault / posix
    if target.is_symlink() or not target.is_file():
        raise ValueError("contents body requires the cluster file on disk")
    data = target.read_bytes()
    text = data.decode("utf-8")
    match = NAME_RE.fullmatch(Path(posix).name)
    if match is None:
        raise ValueError("cluster filename must be YYYY-MM-DD.md or YYYY-MM-DD_DD.md")
    _validate_body(match.group("date"), text)
    message = commit_message_for(Path(posix).name)
    return github_contents_create_body(posix, data, message)


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, env=env, check=False)
    except (FileNotFoundError, OSError) as exc:
        return subprocess.CompletedProcess(
            args=["git", *args],
            returncode=127,
            stdout=b"",
            stderr=f"git is not available: {exc}".encode(),
        )


def _git_text(proc: subprocess.CompletedProcess[bytes]) -> str:
    return proc.stdout.decode("utf-8", "surrogateescape")


def _git_error(proc: subprocess.CompletedProcess[bytes]) -> str:
    text = proc.stderr.decode("utf-8", "replace").strip()
    return text[:500] or f"git exited {proc.returncode}"


def _parse_status_z(data: bytes) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    index = 0
    while index < len(data):
        end = data.find(b"\0", index)
        if end < 0:
            break
        entry = data[index:end]
        index = end + 1
        if len(entry) < 4 or entry[2:3] != b" ":
            raise ValueError("unreadable git status")
        items.append((entry[:2].decode("utf-8", "surrogateescape"), entry[3:].decode("utf-8", "surrogateescape")))
    return items


def _parse_name_status_z(data: bytes) -> list[tuple[str, str]]:
    parts = data.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    rows: list[tuple[str, str]] = []
    index = 0
    while index < len(parts):
        raw = parts[index].decode("utf-8", "surrogateescape")
        if raw[:1] in {"R", "C"}:
            raise ValueError("rename or copy is not an add")
        if index + 1 >= len(parts):
            raise ValueError("unreadable git name-status")
        rows.append((raw, parts[index + 1].decode("utf-8", "surrogateescape")))
        index += 2
    return rows


def _pub(status: str, message: str, **extra: Any) -> tuple[dict[str, Any], bool]:
    payload: dict[str, Any] = {
        "status": status,
        "message": message,
        "files_written": 0,
        "pushed": False,
    }
    payload.update(extra)
    return payload, status == "success" and bool(payload.get("pushed"))


def publish_exact(vault: Path, relative: str) -> tuple[dict[str, Any], bool]:
    """Commit and push one new cluster file. Never updates a path already on main."""
    try:
        posix = assert_cluster_relative(relative)
        _vault(vault)
    except ValueError as exc:
        return _pub("refused", str(exc))
    except OSError as exc:
        return _pub("unavailable", str(exc))
    target = vault / posix
    if target.is_symlink() or not target.is_file():
        return _pub("refused", "publish path is not a cluster file", path=str(target), relative=posix)
    try:
        resolved = target.resolve()
        resolved.relative_to(vault.resolve())
        text = target.read_text(encoding="utf-8")
        match = NAME_RE.fullmatch(Path(posix).name)
        if match is None:
            raise ValueError("cluster filename must be YYYY-MM-DD.md or YYYY-MM-DD_DD.md")
        _validate_body(match.group("date"), text)
        message = commit_message_for(Path(posix).name)
    except (OSError, UnicodeError, ValueError) as exc:
        return _pub("refused", str(exc), path=str(target), relative=posix)

    inside = _git(vault, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode == 127 or b"git is not available" in inside.stderr:
        return _pub("unavailable", "git is not available; file was not pushed", path=str(target), relative=posix)
    if inside.returncode != 0 or _git_text(inside).strip() != "true":
        return _pub("unavailable", "vault is not a git worktree; file was not pushed", path=str(target), relative=posix)
    toplevel = _git(vault, ["rev-parse", "--show-toplevel"])
    if toplevel.returncode != 0 or Path(_git_text(toplevel).strip()).resolve() != vault.resolve():
        return _pub("refused", "vault is not the git root; nothing was committed", path=str(target), relative=posix)
    branch = _git(vault, ["branch", "--show-current"])
    if branch.returncode != 0 or _git_text(branch).strip() != "main":
        return _pub("refused", "publish only runs on main; nothing was committed", path=str(target), relative=posix)
    fetched = _git(vault, ["fetch", "origin", "main"])
    if fetched.returncode != 0:
        return _pub("unavailable", f"fetch origin main failed: {_git_error(fetched)}", path=str(target), relative=posix)
    exists = _git(vault, ["cat-file", "-e", f"origin/main:{posix}"])
    if exists.returncode == 0:
        return _pub("refused", "path already exists on main; not modified and not pushed", path=str(target), relative=posix)

    status = _git(vault, ["status", "--porcelain=v1", "-uall", "-z"])
    if status.returncode != 0:
        return _pub("unavailable", _git_error(status), path=str(target), relative=posix)
    try:
        rows = _parse_status_z(status.stdout)
    except ValueError as exc:
        return _pub("refused", str(exc), path=str(target), relative=posix)
    blocked = [f"{xy} {path}" for xy, path in rows if not (path == posix and xy in {"??", "A "})]
    if blocked:
        return _pub(
            "refused",
            f"worktree has another change: {', '.join(blocked[:8])}; nothing was committed",
            path=str(target),
            relative=posix,
        )
    if not any(path == posix and xy in {"??", "A "} for xy, path in rows):
        head_has = _git(vault, ["cat-file", "-e", f"HEAD:{posix}"])
        if head_has.returncode == 0:
            return _pub("refused", "path already exists on main; not modified and not pushed", path=str(target), relative=posix)
        return _pub("refused", "path is not a new untracked file; nothing was committed", path=str(target), relative=posix)

    added = _git(vault, ["add", "--", posix])
    if added.returncode != 0:
        return _pub("unavailable", _git_error(added), path=str(target), relative=posix)
    cached = _git(vault, ["diff", "--cached", "--name-status", "-z"])
    try:
        staged = _parse_name_status_z(cached.stdout) if cached.returncode == 0 else None
    except ValueError:
        staged = None
    if staged != [("A", posix)]:
        _git(vault, ["restore", "--staged", "--", posix])
        return _pub(
            "refused",
            "staging was not exactly one new file; index restored and nothing was committed",
            path=str(target),
            relative=posix,
        )
    committed = _git(vault, ["-c", "commit.gpgsign=false", "commit", "-m", message, "--", posix])
    if committed.returncode != 0:
        _git(vault, ["restore", "--staged", "--", posix])
        return _pub("unavailable", _git_error(committed), path=str(target), relative=posix)
    pushed = _git(vault, ["push", "origin", "HEAD:main"])
    new_head = _git_text(_git(vault, ["rev-parse", "HEAD"])).strip()
    if pushed.returncode != 0:
        return _pub("push_failed", _git_error(pushed), path=str(target), relative=posix, commit=new_head)
    return {
        "status": "success",
        "path": str(target),
        "relative": posix,
        "files_written": 0,
        "pushed": True,
        "commit": new_head,
        "message": message,
    }, True
