#!/usr/bin/env python3
"""Persist one cluster file after confirmation, or from a scheduled task.

save and retry create a file. They do not overwrite. publish commits and
pushes that one new file. contents-body prints a GitHub contents create body
and does not send it. The body never carries sha.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cluster_lib


def emit(payload: dict[str, Any], ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def _load_approval(path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not path.is_file():
        return None, {"status": "unauthorized", "message": f"approval missing: {path}", "files_written": 0}
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, {"status": "unauthorized", "message": f"invalid approval: {exc}", "files_written": 0}
    if not isinstance(approval, dict):
        return None, {"status": "unauthorized", "message": "approval must be a JSON object", "files_written": 0}
    return approval, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one cluster file")
    parser.add_argument("action", choices=["save", "retry", "publish", "contents-body"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--approval")
    parser.add_argument("--path", help="vault-relative cluster path")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="scheduled task: skip confirmation; still writes only the -gpt file",
    )
    args = parser.parse_args(argv)
    vault = Path(args.vault).expanduser()

    if args.action in {"publish", "contents-body"}:
        if not args.path:
            return emit(
                {"status": "refused", "message": f"{args.action} requires --path", "files_written": 0},
                False,
            )
        if args.action == "publish":
            result, ok = cluster_lib.publish_exact(vault, args.path)
            return emit(result, ok)
        try:
            body = cluster_lib.contents_body_for(vault, args.path)
        except (OSError, UnicodeError, ValueError) as exc:
            return emit(
                {"status": "refused", "message": str(exc), "files_written": 0, "sent": False},
                False,
            )
        return emit(
            {
                "status": "not_sent",
                "reason": "contents body was not sent",
                "sent": False,
                "files_written": 0,
                "body": body,
            },
            False,
        )

    if not args.approval:
        return emit(
            {"status": "unauthorized", "message": "save requires --approval", "files_written": 0},
            False,
        )
    approval, problem = _load_approval(Path(args.approval).expanduser())
    if problem is not None or approval is None:
        return emit(problem or {"status": "unauthorized", "message": "approval missing", "files_written": 0}, False)
    result, ok = cluster_lib.perform(vault, args.action, approval, scheduled=args.scheduled)
    return emit(result, ok)


if __name__ == "__main__":
    raise SystemExit(main())
