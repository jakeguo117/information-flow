#!/usr/bin/env python3
"""Capture one verbatim thought, list undigested thoughts, or record a digest.

add and record-digest only create new files. publish commits and pushes
exactly one of those new paths to main, or refuses. Nothing here edits an
existing thought, digest, or journal, and nothing writes Cognition.
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


def emit(payload: dict[str, Any], ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _load_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _with_publish(vault: Path, result: dict[str, Any], ok: bool, enabled: bool) -> tuple[dict[str, Any], bool]:
    if not enabled or not ok:
        return result, ok
    relative = result.get("relative")
    if not isinstance(relative, str) or not relative:
        return result, ok
    published, pub_ok = thought_lib.publish_exact(vault, relative)
    merged = dict(result)
    merged["publish"] = published
    merged["pushed"] = bool(published.get("pushed"))
    if pub_ok:
        return merged, True
    merged["status"] = published.get("status") or "publish_refused"
    if published.get("status") == "refused":
        merged["status"] = "publish_refused"
    merged["message"] = published.get("message")
    return merged, False


def main(argv: list[str] | None = None) -> int:
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
        return emit(result, ok)

    if args.action == "add":
        if not args.text_file:
            return emit({"status": "refused", "message": "add requires --text-file", "files_written": 0}, False)
        text_path = Path(args.text_file).expanduser()
        if not text_path.is_file():
            return emit(
                {"status": "refused", "message": f"text file missing: {text_path}", "files_written": 0},
                False,
            )
        try:
            verbatim = _read_text(text_path)
            when = (
                thought_lib.parse_instant(args.at)
                if args.at
                else datetime.now(ZoneInfo("Asia/Shanghai"))
            )
        except (OSError, UnicodeError, ValueError) as exc:
            return emit({"status": "refused", "message": str(exc), "files_written": 0}, False)
        result, ok = thought_lib.add_thought(vault, verbatim, when, args.id)
        result, ok = _with_publish(vault, result, ok, args.publish)
        return emit(result, ok)

    if args.action == "record-digest":
        if not args.journal_result or not args.dispositions:
            return emit(
                {
                    "status": "refused",
                    "message": "record-digest requires --journal-result and --dispositions",
                    "files_written": 0,
                },
                False,
            )
        try:
            journal_result = _load_json(Path(args.journal_result).expanduser())
            dispositions = _load_json(Path(args.dispositions).expanduser())
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return emit({"status": "refused", "message": str(exc), "files_written": 0}, False)
        if not isinstance(journal_result, dict):
            return emit(
                {"status": "refused", "message": "journal result must be an object", "files_written": 0},
                False,
            )
        result, ok = thought_lib.record_digest(vault, journal_result, dispositions)
        result, ok = _with_publish(vault, result, ok, args.publish)
        return emit(result, ok)

    if args.action == "publish":
        if not args.path:
            return emit({"status": "refused", "message": "publish requires --path", "files_written": 0}, False)
        result, ok = thought_lib.publish_exact(vault, args.path)
        return emit(result, ok)

    if not args.path:
        return emit({"status": "refused", "message": "contents-body requires --path", "files_written": 0}, False)
    target = vault / args.path
    try:
        content = target.read_bytes()
        text = _read_text(target)
        meta_id = thought_lib._frontmatter(text).get("id") or thought_lib._frontmatter(text).get(
            "journal_event_id"
        )
        message = f"thought: {meta_id}" if thought_lib._frontmatter(text).get("type") == "thought" else f"thought-digest: {meta_id}"
        body = thought_lib.github_contents_create_body(args.path, content, message)
    except (OSError, UnicodeError, ValueError) as exc:
        return emit({"status": "refused", "message": str(exc), "files_written": 0}, False)
    return emit({"status": "success", "files_written": 0, "sent": False, "body": body}, True)


if __name__ == "__main__":
    raise SystemExit(main())
