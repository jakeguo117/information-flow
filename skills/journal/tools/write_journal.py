#!/usr/bin/env python3
"""Persist one journal file after an exact confirmation phrase.

save and retry are idempotent for the same event_id. A different payload for
an event that is already on disk is a conflict and is not overwritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from journal_lib import perform, resolve_digest_snapshot


def emit(payload: dict[str, Any], ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one confirmed journal file")
    parser.add_argument("action", choices=["save", "retry"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument(
        "--append-digest",
        metavar="PATH",
        help="unavailable; the weekly journal does not attach a digest",
    )
    parser.add_argument(
        "--digest-snapshot",
        metavar="DIGEST_ID@rN",
        help="optional; record digest_id, snapshot_revision, and input_ids_sha256 when a caller still passes a Thursday snapshot. The current journal flow does not pass this",
    )
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser()
    approval_path = Path(args.approval).expanduser()
    if not approval_path.is_file():
        return emit(
            {"status": "unauthorized", "message": f"approval missing: {approval_path}", "files_written": 0},
            False,
        )
    try:
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return emit(
            {"status": "unauthorized", "message": f"invalid approval: {exc}", "files_written": 0},
            False,
        )
    if not isinstance(approval, dict):
        return emit(
            {"status": "unauthorized", "message": "approval must be a JSON object", "files_written": 0},
            False,
        )
    if args.append_digest:
        return emit(
            {
                "status": "unavailable",
                "message": (
                    "--append-digest is unavailable; the weekly journal does not attach a digest"
                ),
                "event_id": str(approval.get("event_id") or ""),
                "files_written": 0,
            },
            False,
        )
    snapshot = None
    if args.digest_snapshot:
        try:
            snapshot = resolve_digest_snapshot(vault, args.digest_snapshot)
        except ValueError as exc:
            return emit(
                {
                    "status": "validation_error",
                    "message": str(exc),
                    "event_id": str(approval.get("event_id") or ""),
                    "files_written": 0,
                },
                False,
            )
        except (OSError, UnicodeError) as exc:
            return emit(
                {
                    "status": "unavailable",
                    "message": f"digest snapshot unreadable: {exc}",
                    "event_id": str(approval.get("event_id") or ""),
                    "files_written": 0,
                },
                False,
            )
    result, ok = perform(vault, args.action, approval, snapshot=snapshot)
    return emit(result, ok)


if __name__ == "__main__":
    raise SystemExit(main())

