#!/usr/bin/env python3
"""Capture one verbatim thought, list undigested thoughts, or record a digest.

add and record-digest only create new files. publish commits and pushes
exactly one new path to main, or refuses. A success status is printed only
after that push succeeds. Nothing here edits an existing thought, digest, or
journal, and nothing writes Cognition.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import thought_lib

EXIT_SAVED = 0
EXIT_REFUSED = 2
EXIT_PUSH_FAILED = 3
EXIT_UNAVAILABLE = 4


def emit(payload: dict[str, Any], code: int) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return code


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _load_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _verbatim_of_file(path: Path | None) -> str:
    """Original words of a thought file. A digest list is not a thought, so it is empty."""
    if path is None or not path.is_file() or path.is_symlink():
        return ""
    try:
        text = _read_text(path)
        kind = thought_lib._frontmatter(text).get("type")
    except (OSError, UnicodeError, ValueError):
        return ""
    if kind != thought_lib.THOUGHT_TYPE:
        return ""
    try:
        return thought_lib.verbatim_of(text)
    except ValueError:
        return ""


def _not_saved(reason: str, verbatim: str, code: int, **extra: Any) -> int:
    payload: dict[str, Any] = {"status": "not_saved", "reason": reason, "verbatim": verbatim}
    payload.update(extra)
    return emit(payload, code)


def _failure_code(status: str | None) -> int:
    if status == "push_failed":
        return EXIT_PUSH_FAILED
    if status == "unavailable":
        return EXIT_UNAVAILABLE
    return EXIT_REFUSED


def _saved_or_not(result: dict[str, Any], verbatim: str) -> int:
    """Success only when this call pushed the file."""
    if result.get("status") == "success" and result.get("pushed") is True:
        payload = dict(result)
        payload["verbatim"] = verbatim
        return emit(payload, EXIT_SAVED)
    nested = result.get("publish")
    status = result.get("status")
    reason = str(result.get("message") or result.get("status") or "not pushed")
    if isinstance(nested, dict):
        status = str(nested.get("status") or status or "")
        reason = str(nested.get("message") or reason)
    if status == "success" and result.get("pushed") is not True:
        status = "refused"
        reason = "not pushed"
    return _not_saved(reason, verbatim, _failure_code(str(status) if status else None), **{
        key: result[key] for key in ("path", "relative", "id", "files_written") if key in result
    })


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except Exception as exc:
        return _not_saved(f"git is not available: {exc}", "", EXIT_UNAVAILABLE)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append-only journal thought capture")
    parser.add_argument("action", choices=["add", "list-open", "record-digest", "publish", "contents-body"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--text-file")
    parser.add_argument("--at", help="ISO-8601 capture time; default is now in Asia/Shanghai")
    parser.add_argument("--id")
    parser.add_argument("--journal-result")
    parser.add_argument("--dispositions")
    parser.add_argument("--path", help="vault-relative thought or digest path")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)
    vault = Path(args.vault).expanduser()

    if args.action == "list-open":
        result, ok = thought_lib.list_open(vault)
        return emit(result, EXIT_SAVED if ok else EXIT_REFUSED)

    if args.action == "add":
        if not args.text_file:
            return _not_saved("add requires --text-file", "", EXIT_REFUSED)
        text_path = Path(args.text_file).expanduser()
        if not text_path.is_file():
            return _not_saved(f"text file missing: {text_path}", "", EXIT_REFUSED)
        try:
            verbatim = _read_text(text_path)
            when = (
                thought_lib.parse_instant(args.at)
                if args.at
                else datetime.now(ZoneInfo("Asia/Shanghai"))
            )
        except (OSError, UnicodeError, ValueError) as exc:
            return _not_saved(str(exc), "", EXIT_REFUSED)
        result, ok = thought_lib.add_thought(vault, verbatim, when, args.id)
        if not ok:
            return _not_saved(
                str(result.get("message") or result.get("status") or "refused"),
                verbatim,
                _failure_code(str(result.get("status") or "")),
            )
        if not args.publish:
            return _not_saved("not pushed", verbatim, EXIT_REFUSED, path=result.get("path"), files_written=result.get("files_written"))
        published, _pub_ok = thought_lib.publish_exact(vault, str(result["relative"]))
        merged = dict(result)
        merged["publish"] = published
        merged["pushed"] = bool(published.get("pushed"))
        merged["status"] = published.get("status")
        merged["message"] = published.get("message")
        return _saved_or_not(merged, verbatim)

    if args.action == "record-digest":
        if not args.journal_result or not args.dispositions:
            return _not_saved(
                "record-digest requires --journal-result and --dispositions",
                "",
                EXIT_REFUSED,
            )
        try:
            journal_result = _load_json(Path(args.journal_result).expanduser())
            dispositions = _load_json(Path(args.dispositions).expanduser())
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return _not_saved(str(exc), "", EXIT_REFUSED)
        if not isinstance(journal_result, dict):
            return _not_saved("journal result must be an object", "", EXIT_REFUSED)
        result, ok = thought_lib.record_digest(vault, journal_result, dispositions)
        if not ok:
            return _not_saved(
                str(result.get("message") or result.get("status") or "refused"),
                "",
                _failure_code(str(result.get("status") or "")),
            )
        if not args.publish:
            return _not_saved(
                "not pushed",
                "",
                EXIT_REFUSED,
                path=result.get("path"),
                files_written=result.get("files_written"),
            )
        if not result.get("relative"):
            return _not_saved(str(result.get("message") or "not pushed"), "", EXIT_REFUSED)
        published, _pub_ok = thought_lib.publish_exact(vault, str(result["relative"]))
        merged = dict(result)
        merged["publish"] = published
        merged["pushed"] = bool(published.get("pushed"))
        merged["status"] = published.get("status")
        merged["message"] = published.get("message")
        return _saved_or_not(merged, "")

    if args.action == "publish":
        if not args.path:
            return _not_saved("publish requires --path", "", EXIT_REFUSED)
        verbatim = _verbatim_of_file(vault / args.path)
        result, _ok = thought_lib.publish_exact(vault, args.path)
        return _saved_or_not(result, verbatim)

    if not args.path:
        return _not_saved("contents-body requires --path", "", EXIT_REFUSED)
    target = vault / args.path
    try:
        content = target.read_bytes()
        text = _read_text(target)
        meta = thought_lib._frontmatter(text)
        meta_id = meta.get("id") or meta.get("journal_event_id")
        message = (
            f"thought: {meta_id}" if meta.get("type") == "thought" else f"thought-digest: {meta_id}"
        )
        body = thought_lib.github_contents_create_body(args.path, content, message)
    except (OSError, UnicodeError, ValueError) as exc:
        return _not_saved(str(exc), _verbatim_of_file(target), EXIT_REFUSED)
    verbatim = ""
    try:
        verbatim = thought_lib.verbatim_of(text)
    except ValueError:
        verbatim = ""
    return emit(
        {"status": "not_sent", "reason": "contents body was not sent", "verbatim": verbatim, "sent": False, "body": body},
        EXIT_REFUSED,
    )


if __name__ == "__main__":
    raise SystemExit(main())
