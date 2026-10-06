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

from journal_lib import perform


def emit(payload: dict[str, Any], ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one confirmed journal file")
    parser.add_argument("action", choices=["save", "retry"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--approval", required=True)
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
    result, ok = perform(vault, args.action, approval)
    return emit(result, ok)


if __name__ == "__main__":
    raise SystemExit(main())
