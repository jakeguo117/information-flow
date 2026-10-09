#!/usr/bin/env python3
"""Append-only thought capture and digest lists for the journal skill.

Each thought is a new file. Digested state is a new digest file written only
after a successful journal save. This module never edits or deletes an
existing thought or digest. It does not write Cognition.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import journal_lib

SHANGHAI = ZoneInfo("Asia/Shanghai")
JOURNAL_DIR_NAME = journal_lib.JOURNAL_DIR_NAME
THOUGHT_DIR_NAME = "想法"
DIGEST_DIR_NAME = "digests"
THOUGHT_TYPE = "thought"
DIGEST_TYPE = "thought-digest"
DISPOSITIONS = ("展开", "看过未展开")
WEEK_RE = re.compile(r"^\d{4}-W\d{2}$")
ID_RE = re.compile(r"^thought-\d{8}-\d{4}(?:-[2-9]\d*)?$")
VERBATIM_MARK = "\n---\n原话:\n"
MAX_SUFFIX = 99


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_instant(raw: str) -> datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(SHANGHAI)


def week_id(local: datetime) -> str:
    iso = local.date().isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def stamp(local: datetime) -> str:
    return local.strftime("%Y%m%d-%H%M")


def thought_id_for(local: datetime, suffix: int | None = None) -> str:
    base = f"thought-{stamp(local)}"
    if suffix is None:
        return base
    if suffix < 2:
        raise ValueError("suffix starts at 2")
    return f"{base}-{suffix}"


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key] = value.strip().strip('"').strip("'")
    return values


def verbatim_of(text: str) -> str:
    index = text.find(VERBATIM_MARK)
    if index < 0:
        raise ValueError("thought file has no 原话 marker")
    return text[index + len(VERBATIM_MARK) :]


def render_thought(thought_id: str, local: datetime, verbatim: str) -> str:
    if not ID_RE.match(thought_id):
        raise ValueError("unsafe thought id")
    week = week_id(local)
    captured = local.isoformat(timespec="seconds")
    header = (
        "---\n"
        f"id: {thought_id}\n"
        f"type: {THOUGHT_TYPE}\n"
        "tags:\n"
        "  - thought\n"
        f"captured_at: {captured}\n"
        f"week: {week}\n"
        f"verbatim_sha256: {fingerprint(verbatim)}\n"
        "---\n"
        "原话:\n"
    )
    return header + verbatim


def render_digest(
    event_id: str,
    journal_stem: str,
    rows: list[tuple[str, str]],
) -> str:
    if not journal_lib.EVENT_RE.match(event_id):
        raise ValueError("unsafe journal event_id")
    if any(ch in journal_stem for ch in "/\\\n\r"):
        raise ValueError("unsafe journal stem")
    lines = [
        "---",
        f"type: {DIGEST_TYPE}",
        "tags:",
        "  - thought-digest",
        f"journal_event_id: {event_id}",
        f'journal_stem: "{journal_stem}"',
        f"consumed_count: {len(rows)}",
        "---",
        "",
        f"# 想法消化 {event_id}",
        "",
    ]
    link = f"[[{journal_stem}]]"
    for thought_id, disposition in rows:
        if not ID_RE.match(thought_id):
            raise ValueError("unsafe thought id")
        if disposition not in DISPOSITIONS:
            raise ValueError("disposition must be 展开 or 看过未展开")
        lines.append(f"- id: {thought_id}")
        lines.append(f"  disposition: {disposition}")
        lines.append(f"  journal: {link}")
    lines.append("")
    return "\n".join(lines)


def digest_ids(text: str) -> list[str]:
    found: list[str] = []
    for line in text.splitlines():
        if not line.startswith("- id: "):
            continue
        thought_id = line[len("- id: ") :].strip()
        if ID_RE.match(thought_id):
            found.append(thought_id)
    return found


def _vault(vault: Path) -> Path:
    if not vault.is_dir():
        raise OSError("vault missing")
    if vault.is_symlink():
        raise OSError("refusing to use a symlinked vault")
    return vault


def _thought_root(vault: Path) -> Path:
    root = vault / JOURNAL_DIR_NAME / THOUGHT_DIR_NAME
    if root.is_symlink() or (vault / JOURNAL_DIR_NAME).is_symlink():
        raise OSError("refusing to use a symlinked thought directory")
    resolved_vault = vault.resolve()
    probe = root.resolve() if root.exists() else (resolved_vault / JOURNAL_DIR_NAME / THOUGHT_DIR_NAME)
    try:
        probe.relative_to(resolved_vault)
    except ValueError as exc:
        raise OSError("thought path escapes the vault") from exc
    return root


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise OSError("refusing to write through a symlink")


def _create_exclusive(path: Path, text: str) -> None:
    """Create path. Never replaces an existing file."""
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
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
    readback = _read(path)
    if readback != text:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise OSError("readback did not match the new file")


def _read(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise OSError("refusing to read through a symlink")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def thought_path(vault: Path, week: str, thought_id: str) -> Path:
    if not WEEK_RE.match(week) or not ID_RE.match(thought_id):
        raise ValueError("unsafe thought path")
    return _thought_root(vault) / week / f"{thought_id}.md"


def digest_path(vault: Path, event_id: str) -> Path:
    if not journal_lib.EVENT_RE.match(event_id):
        raise ValueError("unsafe journal event_id")
    return _thought_root(vault) / DIGEST_DIR_NAME / f"digest-{event_id}.md"


def _iter_thought_files(vault: Path) -> list[Path]:
    root = _thought_root(vault)
    if not root.exists():
        return []
    found: list[Path] = []
    for week_dir in root.iterdir():
        if week_dir.is_symlink() or not week_dir.is_dir() or not WEEK_RE.match(week_dir.name):
            continue
        for path in week_dir.iterdir():
            if path.is_symlink() or not path.is_file() or path.suffix != ".md":
                continue
            if not path.name.startswith("thought-"):
                continue
            found.append(path)
    return sorted(found)


def _iter_digest_files(vault: Path) -> list[Path]:
    directory = _thought_root(vault) / DIGEST_DIR_NAME
    if not directory.exists() or directory.is_symlink() or not directory.is_dir():
        return []
    found: list[Path] = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or path.suffix != ".md":
            continue
        if not path.name.startswith("digest-"):
            continue
        found.append(path)
    return sorted(found)


def _load_thought(path: Path) -> dict[str, Any]:
    text = _read(path)
    meta = _frontmatter(text)
    verbatim = verbatim_of(text)
    thought_id = meta.get("id") or ""
    ok = (
        meta.get("type") == THOUGHT_TYPE
        and ID_RE.match(thought_id) is not None
        and path.stem == thought_id
        and meta.get("verbatim_sha256") == fingerprint(verbatim)
    )
    return {
        "id": thought_id,
        "path": str(path),
        "relative": None,
        "week": meta.get("week"),
        "captured_at": meta.get("captured_at"),
        "verbatim": verbatim,
        "verbatim_sha256": fingerprint(verbatim),
        "readable": ok,
    }


def consumed_ids(vault: Path) -> set[str]:
    found: set[str] = set()
    for path in _iter_digest_files(vault):
        text = _read(path)
        if _frontmatter(text).get("type") != DIGEST_TYPE:
            continue
        found.update(digest_ids(text))
    return found


def list_open(vault: Path) -> tuple[dict[str, Any], bool]:
    try:
        _vault(vault)
        thoughts = []
        unreadable = []
        for path in _iter_thought_files(vault):
            item = _load_thought(path)
            item["relative"] = str(path.relative_to(vault))
            if not item["readable"]:
                unreadable.append(item["path"])
                continue
            thoughts.append(item)
        taken = consumed_ids(vault)
    except (OSError, ValueError) as exc:
        return {"status": "unavailable", "message": str(exc), "thoughts": [], "count": 0}, False
    open_items = [item for item in thoughts if item["id"] not in taken]
    open_items.sort(key=lambda item: (item.get("captured_at") or "", item["id"]))
    ids = [item["id"] for item in open_items]
    if len(ids) != len(set(ids)):
        return {
            "status": "conflict",
            "message": "duplicate thought ids on disk",
            "thoughts": open_items,
            "count": len(open_items),
            "unreadable": unreadable,
        }, False
    return {
        "status": "success",
        "thoughts": open_items,
        "count": len(open_items),
        "unreadable": unreadable,
    }, True


def add_thought(
    vault: Path,
    verbatim: str,
    at: datetime,
    explicit_id: str | None = None,
) -> tuple[dict[str, Any], bool]:
    if verbatim == "":
        return {"status": "refused", "message": "verbatim is empty", "files_written": 0}, False
    if at.tzinfo is None:
        return {
            "status": "refused",
            "message": "timestamp must include a timezone",
            "files_written": 0,
        }, False
    try:
        _vault(vault)
        local = at.astimezone(SHANGHAI)
        week = week_id(local)
        if explicit_id is not None:
            if not ID_RE.match(explicit_id) or not explicit_id.startswith(f"thought-{stamp(local)}"):
                return {
                    "status": "refused",
                    "message": "explicit id does not match the Shanghai minute",
                    "files_written": 0,
                }, False
            candidates = [explicit_id]
        else:
            candidates = [thought_id_for(local)]
            candidates.extend(thought_id_for(local, suffix) for suffix in range(2, MAX_SUFFIX + 1))
        root = _thought_root(vault)
        _ensure_dir(root)
        _ensure_dir(root / week)
    except (OSError, ValueError) as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0}, False

    saw_existing = False
    for thought_id in candidates:
        path = root / week / f"{thought_id}.md"
        if path.exists() or path.is_symlink():
            saw_existing = True
            if explicit_id is None:
                continue
            try:
                existing = _read(path)
            except OSError as exc:
                return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
            try:
                same = (
                    _frontmatter(existing).get("id") == thought_id
                    and verbatim_of(existing) == verbatim
                    and fingerprint(verbatim) == _frontmatter(existing).get("verbatim_sha256")
                )
            except ValueError:
                same = False
            if same:
                return {
                    "status": "already_persisted",
                    "id": thought_id,
                    "path": str(path),
                    "relative": str(path.relative_to(vault)),
                    "week": week,
                    "verbatim": verbatim,
                    "files_written": 0,
                }, True
            return {
                "status": "refused",
                "message": "thought path already exists and was not modified",
                "id": thought_id,
                "path": str(path),
                "files_written": 0,
            }, False
        rendered = render_thought(thought_id, local, verbatim)
        before = journal_lib.cognition_file_count(vault)
        try:
            _create_exclusive(path, rendered)
        except FileExistsError:
            if explicit_id is None:
                continue
            return {
                "status": "refused",
                "message": "thought path already exists and was not modified",
                "id": thought_id,
                "path": str(path),
                "files_written": 0,
            }, False
        except OSError as exc:
            return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
        if journal_lib.cognition_file_count(vault) != before:
            return {
                "status": "conflict",
                "message": "thought capture observed a cognition file change",
                "id": thought_id,
                "path": str(path),
                "files_written": 1,
            }, False
        return {
            "status": "success",
            "id": thought_id,
            "path": str(path),
            "relative": str(path.relative_to(vault)),
            "week": week,
            "verbatim": verbatim,
            "files_written": 1,
        }, True
    message = "thought path already exists and was not modified" if saw_existing else "no free thought id"
    return {"status": "refused", "message": message, "files_written": 0}, False


def _journal_ok(vault: Path, result: dict[str, Any]) -> tuple[Path, str] | str:
    if not isinstance(result, dict) or result.get("status") != "success":
        return "journal result is not success"
    event_id = str(result.get("event_id") or "")
    raw_path = result.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        return "journal result has no path"
    path = Path(raw_path)
    try:
        resolved = path.resolve()
        resolved.relative_to(vault.resolve())
    except (OSError, ValueError):
        return "journal path escapes the vault"
    journal_dir = (vault / JOURNAL_DIR_NAME).resolve()
    if path.is_symlink() or not path.is_file():
        return "journal file is missing"
    if resolved.parent != journal_dir:
        return "journal file is not a top-level journal entry"
    try:
        text = _read(path)
    except OSError as exc:
        return str(exc)
    meta = _frontmatter(text)
    if meta.get("type") != "journal" or meta.get("event_id") != event_id:
        return "journal file does not match the success result"
    if not journal_lib.EVENT_RE.match(event_id):
        return "unsafe journal event_id"
    return path, event_id


def record_digest(
    vault: Path,
    journal_result: dict[str, Any],
    dispositions: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    try:
        _vault(vault)
    except OSError as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
    checked = _journal_ok(vault, journal_result)
    if isinstance(checked, str):
        return {"status": "refused", "message": checked, "files_written": 0}, False
    journal_file, event_id = checked
    listed, ok = list_open(vault)
    if not ok:
        return {
            "status": "refused",
            "message": listed.get("message") or "thought list is not usable",
            "files_written": 0,
        }, False
    if listed.get("unreadable"):
        return {
            "status": "refused",
            "message": "unreadable thought files; digest not written",
            "files_written": 0,
        }, False
    open_ids = [item["id"] for item in listed["thoughts"]]
    if not isinstance(dispositions, list):
        return {"status": "refused", "message": "dispositions must be a list", "files_written": 0}, False
    mapped: dict[str, str] = {}
    for row in dispositions:
        if not isinstance(row, dict):
            return {"status": "refused", "message": "disposition row must be an object", "files_written": 0}, False
        thought_id = str(row.get("id") or "")
        disposition = str(row.get("disposition") or "")
        if thought_id in mapped:
            return {"status": "refused", "message": "duplicate disposition id", "files_written": 0}, False
        if disposition not in DISPOSITIONS:
            return {
                "status": "refused",
                "message": "disposition must be 展开 or 看过未展开",
                "files_written": 0,
            }, False
        mapped[thought_id] = disposition
    if set(mapped) != set(open_ids):
        return {
            "status": "refused",
            "message": "digest must name exactly the current undigested thoughts",
            "files_written": 0,
            "open_ids": open_ids,
        }, False
    if not mapped:
        return {
            "status": "success",
            "message": "no undigested thoughts; digest file not created",
            "event_id": event_id,
            "files_written": 0,
        }, True
    rows = sorted(mapped.items())
    try:
        rendered = render_digest(event_id, journal_file.stem, rows)
        path = digest_path(vault, event_id)
        _ensure_dir(path.parent)
    except (OSError, ValueError) as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
    if path.exists() or path.is_symlink():
        try:
            existing = _read(path)
        except OSError as exc:
            return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
        if existing == rendered:
            return {
                "status": "already_persisted",
                "event_id": event_id,
                "path": str(path),
                "relative": str(path.relative_to(vault)),
                "files_written": 0,
            }, True
        return {
            "status": "refused",
            "message": "digest path already exists and was not modified",
            "event_id": event_id,
            "path": str(path),
            "files_written": 0,
        }, False
    before = journal_lib.cognition_file_count(vault)
    try:
        _create_exclusive(path, rendered)
    except FileExistsError:
        return {
            "status": "refused",
            "message": "digest path already exists and was not modified",
            "event_id": event_id,
            "path": str(path),
            "files_written": 0,
        }, False
    except OSError as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0}, False
    if journal_lib.cognition_file_count(vault) != before:
        return {
            "status": "conflict",
            "message": "digest write observed a cognition file change",
            "path": str(path),
            "files_written": 1,
        }, False
    return {
        "status": "success",
        "event_id": event_id,
        "path": str(path),
        "relative": str(path.relative_to(vault)),
        "ids": [thought_id for thought_id, _ in rows],
        "files_written": 1,
    }, True


def github_contents_create_body(path: str, content: bytes, message: str, branch: str = "main") -> dict[str, str]:
    """Body for a GitHub contents create call. Never includes sha."""
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path:
        raise ValueError("unsafe contents path")
    if not path.startswith(f"{JOURNAL_DIR_NAME}/{THOUGHT_DIR_NAME}/"):
        raise ValueError("contents create is only for a thought or digest path")
    if not message.strip() or "\n" in message or "sha" in message.lower():
        raise ValueError("unsafe commit message")
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


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        env=env,
        check=False,
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
        xy = entry[:2].decode("utf-8", "surrogateescape")
        path = entry[3:].decode("utf-8", "surrogateescape")
        if xy[0] in {"R", "C"}:
            end2 = data.find(b"\0", index)
            if end2 < 0:
                raise ValueError("unreadable git rename")
            path = data[index:end2].decode("utf-8", "surrogateescape")
            index = end2 + 1
        items.append((xy, path))
    return items


def _parse_name_status_z(data: bytes) -> list[tuple[str, str]]:
    parts = data.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    if len(parts) % 2:
        raise ValueError("unreadable git name-status")
    rows: list[tuple[str, str]] = []
    for offset in range(0, len(parts), 2):
        rows.append(
            (
                parts[offset].decode("utf-8", "surrogateescape"),
                parts[offset + 1].decode("utf-8", "surrogateescape"),
            )
        )
    return rows


def _relative_publish_path(vault: Path, relative: str) -> tuple[Path, str] | str:
    if not relative or relative.startswith("/") or "\\" in relative or "\x00" in relative:
        return "unsafe publish path"
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return "unsafe publish path"
    target = vault / path
    try:
        resolved = target.resolve()
        resolved.relative_to((_thought_root(vault)).resolve())
    except (OSError, ValueError):
        return "publish path is outside 📝 Journal/想法"
    if target.is_symlink() or not target.is_file():
        return "publish path is not a new file"
    posix = path.as_posix()
    try:
        text = _read(target)
    except OSError as exc:
        return str(exc)
    meta = _frontmatter(text)
    kind = meta.get("type")
    if kind == THOUGHT_TYPE:
        thought_id = meta.get("id") or ""
        if target.stem != thought_id or not ID_RE.match(thought_id):
            return "thought file id does not match its path"
        if target.parent.name != meta.get("week"):
            return "thought file week does not match its path"
    elif kind == DIGEST_TYPE:
        event_id = meta.get("journal_event_id") or ""
        if target.parent.name != DIGEST_DIR_NAME or target.name != f"digest-{event_id}.md":
            return "digest file name does not match its journal event"
    else:
        return "publish path is not a thought or digest file"
    return target, posix


def _origin_bytes(repo: Path, relative: str) -> bytes | None:
    proc = _git(repo, ["show", f"origin/main:{relative}"])
    if proc.returncode != 0:
        return None
    return proc.stdout


def _head_has(repo: Path, relative: str) -> bool:
    proc = _git(repo, ["cat-file", "-e", f"HEAD:{relative}"])
    return proc.returncode == 0


def _unstage(repo: Path, relative: str) -> None:
    restored = _git(repo, ["restore", "--staged", "--", relative])
    if restored.returncode != 0:
        _git(repo, ["reset", "-q", "HEAD", "--", relative])


def publish_exact(vault: Path, relative: str) -> tuple[dict[str, Any], bool]:
    """Commit and push exactly one new thought or digest file to main.

    Refuses if the path already exists on main, if the commit would modify
    or delete anything, or if the worktree has any other change. The weekly
    journal file is never an allowed extra path.
    """
    try:
        _vault(vault)
        checked = _relative_publish_path(vault, relative)
    except OSError as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0, "pushed": False}, False
    if isinstance(checked, str):
        return {"status": "refused", "message": checked, "files_written": 0, "pushed": False}, False
    target, posix = checked
    inside = _git(vault, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or _git_text(inside).strip() != "true":
        return {
            "status": "unavailable",
            "message": "vault is not a git worktree; file was not pushed",
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }, False
    toplevel = _git(vault, ["rev-parse", "--show-toplevel"])
    if toplevel.returncode != 0 or Path(_git_text(toplevel).strip()).resolve() != vault.resolve():
        return {
            "status": "refused",
            "message": "vault is not the git root; nothing was committed",
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }, False
    branch = _git(vault, ["branch", "--show-current"])
    if branch.returncode != 0 or _git_text(branch).strip() != "main":
        return {
            "status": "refused",
            "message": "publish only runs on main; nothing was committed",
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }, False
    fetched = _git(vault, ["fetch", "origin", "main"])
    if fetched.returncode != 0:
        return {
            "status": "unavailable",
            "message": f"fetch origin main failed: {_git_error(fetched)}",
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }, False
    head = _git(vault, ["rev-parse", "HEAD"])
    origin = _git(vault, ["rev-parse", "origin/main"])
    if head.returncode != 0 or origin.returncode != 0:
        return {
            "status": "unavailable",
            "message": "HEAD or origin/main is missing",
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }, False
    head_sha = _git_text(head).strip()
    origin_sha = _git_text(origin).strip()
    status = _git(vault, ["status", "--porcelain=v1", "-uall", "-z"])
    if status.returncode != 0:
        return {
            "status": "unavailable",
            "message": _git_error(status),
            "files_written": 0,
            "pushed": False,
        }, False
    try:
        rows = _parse_status_z(status.stdout)
    except ValueError as exc:
        return {"status": "unavailable", "message": str(exc), "files_written": 0, "pushed": False}, False
    remote_bytes = _origin_bytes(vault, posix)

    def base(extra: dict[str, Any], ok: bool) -> tuple[dict[str, Any], bool]:
        payload = {
            "path": str(target),
            "relative": posix,
            "files_written": 0,
            "pushed": False,
        }
        payload.update(extra)
        return payload, ok

    if remote_bytes is not None:
        return base(
            {
                "status": "refused",
                "message": "path already exists on main; not modified and not pushed",
            },
            False,
        )

    ahead = _git(vault, ["rev-list", "--count", "origin/main..HEAD"])
    behind = _git(vault, ["rev-list", "--count", "HEAD..origin/main"])
    if ahead.returncode != 0 or behind.returncode != 0:
        return base({"status": "unavailable", "message": "could not compare HEAD with origin/main"}, False)
    ahead_n = int(_git_text(ahead).strip() or "0")
    behind_n = int(_git_text(behind).strip() or "0")
    if behind_n:
        return base({"status": "refused", "message": "main is behind origin/main; nothing was pushed"}, False)

    cached_now = _git(vault, ["diff", "--cached", "--name-status", "-z"])
    if cached_now.returncode != 0:
        return base({"status": "unavailable", "message": _git_error(cached_now)}, False)
    try:
        staged_rows = _parse_name_status_z(cached_now.stdout)
    except ValueError as exc:
        return base({"status": "unavailable", "message": str(exc)}, False)
    if any(status != "A" for status, _path in staged_rows):
        return base(
            {
                "status": "refused",
                "message": "staged diff modifies or deletes a file; not pushed",
            },
            False,
        )
    if staged_rows not in ([], [("A", posix)]):
        return base(
            {
                "status": "refused",
                "message": "staged diff is not exactly this one new file; not pushed",
            },
            False,
        )

    if not rows and ahead_n == 1 and _head_has(vault, posix):
        shown = _git(vault, ["show", "--name-status", "--format=", "-z", "HEAD"])
        try:
            changed = _parse_name_status_z(shown.stdout)
        except ValueError as exc:
            return base({"status": "unavailable", "message": str(exc)}, False)
        if changed == [("A", posix)]:
            pushed = _git(vault, ["push", "origin", "HEAD:main"])
            if pushed.returncode != 0:
                return base(
                    {"status": "push_failed", "message": _git_error(pushed), "commit": head_sha},
                    False,
                )
            return base({"status": "success", "pushed": True, "commit": head_sha}, True)
        return base(
            {"status": "refused", "message": "unpushed commit is not exactly this new file; not pushed"},
            False,
        )

    if rows != [("??", posix)] or ahead_n != 0 or head_sha != origin_sha:
        return base(
            {
                "status": "refused",
                "message": "worktree has another change or main has unpushed commits; nothing was committed",
            },
            False,
        )
    if _head_has(vault, posix):
        return base(
            {"status": "refused", "message": "path already exists in HEAD; not modified and not pushed"},
            False,
        )

    added = _git(vault, ["add", "--", posix])
    if added.returncode != 0:
        return base({"status": "unavailable", "message": _git_error(added)}, False)
    cached = _git(vault, ["diff", "--cached", "--name-status", "-z"])
    status_after = _git(vault, ["status", "--porcelain=v1", "-uall", "-z"])
    try:
        cached_rows = _parse_name_status_z(cached.stdout)
        status_rows = _parse_status_z(status_after.stdout)
    except ValueError as exc:
        _unstage(vault, posix)
        return base({"status": "unavailable", "message": str(exc)}, False)
    if cached_rows != [("A", posix)] or status_rows != [("A ", posix)]:
        _unstage(vault, posix)
        return base(
            {
                "status": "refused",
                "message": "staging was not exactly one new file; index restored and nothing was committed",
            },
            False,
        )
    kind = _frontmatter(_read(target)).get("type")
    if kind == THOUGHT_TYPE:
        message = f"thought: {_frontmatter(_read(target)).get('id')}"
    else:
        message = f"thought-digest: {_frontmatter(_read(target)).get('journal_event_id')}"
    committed = _git(vault, ["commit", "-m", message, "--", posix])
    if committed.returncode != 0:
        _unstage(vault, posix)
        return base({"status": "unavailable", "message": _git_error(committed)}, False)
    shown = _git(vault, ["show", "--name-status", "--format=", "-z", "HEAD"])
    try:
        changed = _parse_name_status_z(shown.stdout)
    except ValueError as exc:
        return base({"status": "refused", "message": str(exc)}, False)
    new_head = _git_text(_git(vault, ["rev-parse", "HEAD"])).strip()
    if changed != [("A", posix)]:
        return base(
            {
                "status": "refused",
                "message": "commit was not exactly one new file; not pushed and not deleted",
                "commit": new_head,
            },
            False,
        )
    clean = _parse_status_z(_git(vault, ["status", "--porcelain=v1", "-uall", "-z"]).stdout)
    if clean:
        return base(
            {
                "status": "refused",
                "message": "worktree changed during commit; not pushed",
                "commit": new_head,
            },
            False,
        )
    pushed = _git(vault, ["push", "origin", "HEAD:main"])
    if pushed.returncode != 0:
        return base({"status": "push_failed", "message": _git_error(pushed), "commit": new_head}, False)
    return base({"status": "success", "pushed": True, "commit": new_head}, True)
