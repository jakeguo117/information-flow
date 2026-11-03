#!/usr/bin/env python3
"""Journal confirmation gate and intake selection.

Encodes the existing journal rules: unchecked intake is not journal material,
and a journal file is written only after an exact confirmation phrase.
Does not write Cognition, does not git commit or push, and does not start
collectors, reminders, or network services.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import vault_guard

CONFIRM_PHRASES = ("可以写", "写吧", "OK 写")
JOURNAL_DIR_NAME = "📝 Journal"
COGNITION_DIR_NAME = "📖 Cognition"
KNOWN_CHANNELS = frozenset({"snipd", "weread", "youtube"})
CHANNEL_RE = re.compile(r"摄入：(\d{4}-\d{2}-\d{2})\s*·\s*(\S+)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
DIGEST_MARKER_PATTERN = r"(?:\r?\n)?<!-- information-flow-weekly-digest generator=(\S+) sha256=([0-9a-f]{64}) -->\s*\Z"
DIGEST_MARKER_RE = re.compile(DIGEST_MARKER_PATTERN)
DIGEST_ID_RE = re.compile(r"dg-cy-\d{8}")
SNAPSHOT_SPEC_RE = re.compile(r"^(dg-(cy-\d{8}))@r([1-9][0-9]*)$")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SNAPSHOT_KEYS = ("digest_id", "snapshot_revision", "input_ids_sha256")


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def channel_of(item: Any) -> str | None:
    for line in item.extra:
        match = CHANNEL_RE.search(line)
        if match:
            return match.group(2)
    return None


def is_related(item: Any, echo_terms: list[str]) -> bool:
    if not echo_terms:
        return False
    blob = "\n".join([item.heading, item.wiki, *item.extra])
    return any(term and term in blob for term in echo_terms)


def journal_material(items: list[Any], echo_terms: list[str]) -> dict[str, Any]:
    """Checked related items may enter a journal. Unchecked related items never do.

    A channel other than snipd/weread/youtube is reported as a new-channel sample.
    New-channel items follow the same checked/unchecked rule; the channel name
    does not authorize a write.
    """
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    new_channels: list[dict[str, Any]] = []
    for item in items:
        kind = channel_of(item)
        related = is_related(item, echo_terms)
        record = {
            "heading": item.heading,
            "checked": bool(item.checked),
            "wiki": item.wiki,
            "channel": kind,
            "related": related,
        }
        if kind and kind not in KNOWN_CHANNELS:
            new_channels.append(record)
        if related and item.checked:
            selected.append(record)
        elif related and not item.checked:
            skipped.append(record)
    return {
        "selected": selected,
        "skipped_unchecked_related": skipped,
        "new_channels": new_channels,
        "selected_count": len(selected),
        "skipped_unchecked_related_count": len(skipped),
    }


def _read_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _frontmatter_value(text: str, key: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    prefix = f"{key}:"
    for line in text[4:end].splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def event_id_of(text: str) -> str | None:
    return _frontmatter_value(text, "event_id")


def input_ids_sha256(input_ids: list[str]) -> str:
    """sha256 hex of input_ids joined by a newline, with no trailing newline."""
    if not isinstance(input_ids, list) or any(not isinstance(item, str) or item == "" for item in input_ids):
        raise ValueError("input_ids must be a list of non-empty strings")
    if any("\n" in item or "\r" in item for item in input_ids):
        raise ValueError("input_ids entries must be single-line strings")
    return fingerprint("\n".join(input_ids))


def normalized_snapshot_fields(approval: dict[str, Any]) -> dict[str, Any] | None:
    """Return digest snapshot frontmatter fields, or None when the approval has none."""
    digest_id = approval.get("digest_id")
    revision = approval.get("snapshot_revision")
    sha = approval.get("input_ids_sha256")
    if digest_id in (None, "") and revision in (None, "") and sha in (None, ""):
        return None
    if not isinstance(digest_id, str) or DIGEST_ID_RE.fullmatch(digest_id) is None:
        raise ValueError("digest_id must look like dg-cy-YYYYMMDD")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ValueError("snapshot_revision must be a positive integer")
    if not isinstance(sha, str) or SHA256_RE.fullmatch(sha) is None:
        raise ValueError("input_ids_sha256 must be a sha256 hex digest")
    return {
        "digest_id": digest_id,
        "snapshot_revision": revision,
        "input_ids_sha256": sha,
    }


def render_journal(approval: dict[str, Any]) -> str:
    date = str(approval.get("date") or "")
    if not DATE_RE.match(date):
        raise ValueError("date must be YYYY-MM-DD")
    try:
        number = int(approval.get("journal_number"))
    except (TypeError, ValueError) as exc:
        raise ValueError("journal_number must be a positive integer") from exc
    if number < 1:
        raise ValueError("journal_number must be a positive integer")
    title = str(approval.get("title") or "")
    if not title or any(ch in title for ch in "/\\\n\r\t") or title in {".", ".."}:
        raise ValueError("title must be a single path segment")
    event_id = str(approval.get("event_id") or "")
    if not EVENT_RE.match(event_id):
        raise ValueError("event_id is missing or unsafe")
    body = approval.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("body must be non-empty text")
    topics = approval.get("topics") or []
    if not isinstance(topics, list) or any(not isinstance(item, str) for item in topics):
        raise ValueError("topics must be a list of strings")
    previous = str(approval.get("previous") or "")
    if any(ch in previous for ch in "/\\\n\r"):
        raise ValueError("previous must be a wikilink stem")
    heading = f"周记 {number} — {title}"
    lines = [
        "---",
        f"date: {date}",
        "type: journal",
        "tags:",
        "  - journal",
        f'title: "{heading}"',
        f"event_id: {event_id}",
    ]
    fields = normalized_snapshot_fields(approval)
    if fields is not None:
        lines.extend(f"{key}: {fields[key]}" for key in SNAPSHOT_KEYS)
    lines.extend(
        [
            "---",
            "",
            f"# {heading}",
            "",
            body.rstrip(),
            "",
            "---",
            "## Connections / 关联",
            "**Topics / 主题:**",
        ]
    )
    if topics:
        for topic in topics:
            lines.append(topic if topic.startswith("[[") else f"[[{topic}]]")
    else:
        lines.append("（合成案例无主题）")
    lines.append("")
    prev = f"[[{previous}]]" if previous else "（无）"
    lines.append(f"**Previous / 上一篇:** {prev}")
    lines.append("")
    return "\n".join(lines)


def strip_generator_marker(text: str) -> str:
    """Drop the trailing weekly-digest generator comment, if present."""
    return DIGEST_MARKER_RE.sub("", text)


def parse_digest_snapshot_spec(spec: str) -> tuple[str, str, int]:
    """Parse ``dg-cy-YYYYMMDD@rN`` into digest_id, cycle_id, and revision."""
    match = SNAPSHOT_SPEC_RE.fullmatch(spec)
    if not match:
        raise ValueError("digest snapshot must look like dg-cy-YYYYMMDD@rN")
    return match.group(1), match.group(2), int(match.group(3))


def _yaml_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("snapshot scalar is empty")
    if value.startswith('"'):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("snapshot scalar is not valid JSON") from exc
        if not isinstance(loaded, str):
            raise ValueError("snapshot scalar must be a string")
        return loaded
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1]
    return value


def parse_snapshot_frontmatter(text: str) -> dict[str, Any]:
    """Read digest_id, snapshot_revision, and input_ids from a snapshot file."""
    if not text.startswith("---\n"):
        raise ValueError("snapshot is missing frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("snapshot frontmatter is not closed")
    digest_id = None
    revision = None
    input_ids = None
    lines = text[4:end].splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("digest_id:"):
            digest_id = _yaml_scalar(line.split(":", 1)[1])
        elif line.startswith("snapshot_revision:"):
            raw = line.split(":", 1)[1].strip().strip('"').strip("'")
            if not re.fullmatch(r"[0-9]+", raw):
                raise ValueError("snapshot_revision must be an integer")
            revision = int(raw)
        elif line == "input_ids: []":
            input_ids = []
        elif line == "input_ids:":
            items: list[str] = []
            index += 1
            while index < len(lines):
                item = re.fullmatch(r"  - (.+)", lines[index])
                if not item:
                    break
                items.append(_yaml_scalar(item.group(1)))
                index += 1
            input_ids = items
            continue
        index += 1
    if not isinstance(digest_id, str) or DIGEST_ID_RE.fullmatch(digest_id) is None:
        raise ValueError("snapshot digest_id is missing")
    if revision is None:
        raise ValueError("snapshot_revision is missing")
    if revision < 1:
        raise ValueError("snapshot_revision must be a positive integer")
    if input_ids is None:
        raise ValueError("snapshot input_ids must be a list")
    return {"digest_id": digest_id, "snapshot_revision": revision, "input_ids": input_ids}


def _reject_digest_symlinks(vault: Path, rel: Path) -> None:
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        raise OSError("digest path escapes the vault")
    current = vault
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise OSError("refusing to read digest through a symlink")


def resolve_digest_snapshot(vault: Path, spec: str) -> dict[str, Any]:
    """Load snapshot identity fields from ``📋 Digests/cycles/{cycle_id}/r{n}.md``."""
    digest_id, cycle_id, revision = parse_digest_snapshot_spec(spec)
    rel = Path("📋 Digests") / "cycles" / cycle_id / f"r{revision}.md"
    _reject_digest_symlinks(vault, rel)
    path = vault / rel
    if not path.is_file():
        raise OSError("digest snapshot file is missing")
    parsed = parse_snapshot_frontmatter(read_digest(vault, rel))
    if parsed["digest_id"] != digest_id:
        raise ValueError("snapshot digest_id does not match --digest-snapshot")
    if parsed["snapshot_revision"] != revision:
        raise ValueError("snapshot_revision does not match --digest-snapshot")
    return {
        "digest_id": digest_id,
        "snapshot_revision": revision,
        "input_ids_sha256": input_ids_sha256(parsed["input_ids"]),
    }


def read_digest(vault: Path, digest_path: Path) -> str:
    """Read a weekly digest that must live inside the vault under 📋 Digests/."""
    path = digest_path if digest_path.is_absolute() else vault / digest_path
    if path.is_symlink():
        raise OSError("refusing to read digest through a symlink")
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise OSError("digest path escapes the vault") from exc
    if not rel.parts or rel.parts[0] != "📋 Digests" or resolved.suffix != ".md":
        raise OSError("digest must be a .md file under 📋 Digests/")
    return strip_generator_marker(resolved.read_text(encoding="utf-8"))


def journal_filename(approval: dict[str, Any]) -> str:
    date = str(approval.get("date") or "")
    title = str(approval.get("title") or "")
    return f"{date} {title}.md"


def _journal_dir(vault: Path) -> Path:
    directory = vault / JOURNAL_DIR_NAME
    if directory.is_symlink():
        raise OSError("refusing to use a symlinked journal directory")
    resolved = directory.resolve() if directory.exists() else (vault.resolve() / JOURNAL_DIR_NAME)
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise OSError("journal path escapes the vault") from exc
    if resolved.parent != vault.resolve():
        raise OSError("journal path escapes the vault")
    return directory


def list_journal_files(vault: Path) -> list[Path]:
    directory = _journal_dir(vault)
    if not directory.exists():
        return []
    files: list[Path] = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or path.suffix != ".md":
            continue
        # Thought files and digest lists live under 📝 Journal/想法/ and are
        # not journal entries. A stray top-level file with those types is
        # skipped too, so listing cannot treat it as a weekly journal.
        if _frontmatter_value(_read_text_or_empty(path), "type") in {"thought", "thought-digest"}:
            continue
        files.append(path)
    return sorted(files)


def cognition_file_count(vault: Path) -> int:
    root = vault / COGNITION_DIR_NAME
    if not root.exists():
        return 0
    if root.is_symlink():
        raise OSError("refusing to inspect cognition through a symlink")
    count = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        if path.is_file() and path.suffix == ".md":
            count += 1
    return count


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise OSError("refusing to write through a symlink")
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(str(tmp), flags, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp, path)


def confirmation_granted(approval: dict[str, Any]) -> bool:
    return approval.get("confirmed") is True and approval.get("phrase") in CONFIRM_PHRASES


def perform(
    vault: Path,
    action: str,
    approval: dict[str, Any],
    *,
    snapshot: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    event_id = str(approval.get("event_id") or "")
    if action not in {"save", "retry"}:
        return {"status": "unavailable", "message": "action must be save or retry", "files_written": 0}, False
    if not vault.is_dir():
        return {
            "status": "unavailable" if confirmation_granted(approval) else "refused",
            "message": "vault missing; journal will not be written elsewhere",
            "event_id": event_id,
            "files_written": 0,
        }, False

    rejected = vault_guard.rejection(vault)
    if rejected is not None:
        status, message = rejected
        return {
            "status": status,
            "message": message,
            "event_id": event_id,
            "files_written": 0,
        }, False

    if not confirmation_granted(approval):
        count = len(list_journal_files(vault)) if (vault / JOURNAL_DIR_NAME).exists() else 0
        return {
            "status": "refused",
            "message": "journal save requires confirmed=true and phrase 可以写, 写吧, or OK 写",
            "event_id": event_id,
            "files_written": 0,
            "journal_files": count,
        }, False

    try:
        approved_snapshot = normalized_snapshot_fields(approval)
        if snapshot is not None:
            if approved_snapshot != snapshot:
                raise ValueError("approval snapshot fields do not match --digest-snapshot")
        elif approved_snapshot is not None:
            raise ValueError("snapshot fields require --digest-snapshot")
        rendered = render_journal(approval)
    except ValueError as exc:
        return {
            "status": "validation_error",
            "message": str(exc),
            "event_id": event_id,
            "files_written": 0,
        }, False

    expected = approval.get("payload_sha256")
    actual = fingerprint(rendered)
    if not expected or expected != actual:
        return {
            "status": "stale_approval",
            "message": "approval payload_sha256 does not match the rendered journal",
            "event_id": event_id,
            "files_written": 0,
        }, False

    before_cognition = cognition_file_count(vault)
    try:
        existing_files = list_journal_files(vault)
    except OSError as exc:
        return {
            "status": "unavailable",
            "message": str(exc),
            "event_id": event_id,
            "files_written": 0,
        }, False

    matches: list[tuple[Path, str]] = []
    for path in existing_files:
        text = path.read_text(encoding="utf-8")
        if event_id_of(text) == event_id:
            matches.append((path, text))
    if len(matches) > 1:
        return {
            "status": "conflict",
            "message": "more than one journal file already has this event_id",
            "event_id": event_id,
            "files_written": 0,
        }, False
    if len(matches) == 1:
        path, text = matches[0]
        if text == rendered:
            return {
                "status": "success",
                "already_persisted": True,
                "event_id": event_id,
                "path": str(path),
                "fingerprint": fingerprint(text),
                "files_written": 0,
                "journal_files_for_event": 1,
            }, True
        return {
            "status": "conflict",
            "message": "persisted journal differs from this event payload; not overwritten",
            "event_id": event_id,
            "path": str(path),
            "fingerprint": fingerprint(text),
            "files_written": 0,
        }, False

    target = _journal_dir(vault) / journal_filename(approval)
    if target.exists():
        return {
            "status": "conflict",
            "message": "target journal path exists under a different event; not overwritten",
            "event_id": event_id,
            "path": str(target),
            "files_written": 0,
        }, False

    try:
        _atomic_write(target, rendered)
        readback = target.read_text(encoding="utf-8")
    except OSError as exc:
        if target.exists():
            try:
                target.unlink()
            except OSError:
                pass
        return {
            "status": "unavailable",
            "message": f"write failed: {exc}",
            "event_id": event_id,
            "files_written": 0,
        }, False
    if readback != rendered:
        try:
            target.unlink()
        except OSError:
            pass
        return {
            "status": "conflict",
            "message": "readback did not match the rendered journal; file removed",
            "event_id": event_id,
            "files_written": 0,
        }, False
    if cognition_file_count(vault) != before_cognition:
        try:
            target.unlink()
        except OSError:
            pass
        return {
            "status": "conflict",
            "message": "journal save touched cognition files; journal write rolled back",
            "event_id": event_id,
            "files_written": 0,
        }, False
    return {
        "status": "success",
        "already_persisted": False,
        "event_id": event_id,
        "path": str(target),
        "fingerprint": fingerprint(readback),
        "files_written": 1,
        "journal_files_for_event": 1,
    }, True

