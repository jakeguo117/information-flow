#!/usr/bin/env python3
"""Append-only Fact records.

The caller chooses the output file or directory. Nothing here points at a
vault path. Field names are the local contract in references/schema.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VERIFICATION_STATUSES = ("待核验", "已核验", "有争议", "已更正")
DIRECTORY_LOG_NAME = "facts.jsonl"


def emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def fail(message: str) -> int:
    emit({"ok": False, "error": message})
    print(message, file=sys.stderr)
    return 1


def target_file(out: Path) -> Path:
    if out.exists() and out.is_dir():
        return out / DIRECTORY_LOG_NAME
    return out


def record_from_args(args: argparse.Namespace) -> dict:
    record = {
        "id": args.id,
        "verification_status": args.verification_status,
        "text": args.text,
    }
    if args.link is not None:
        record["link"] = args.link
    if args.date is not None:
        record["date"] = args.date
    return record


def validation_error(record: dict) -> str | None:
    fact_id = record.get("id")
    status = record.get("verification_status")
    text = record.get("text")
    if not isinstance(fact_id, str) or fact_id == "":
        return "missing id"
    if not isinstance(status, str) or status == "":
        return "missing verification_status"
    if status not in VERIFICATION_STATUSES:
        return "invalid verification_status"
    if not isinstance(text, str) or text == "":
        return "missing text"
    return None


def read_records(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip() == "":
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_no} is not json") from exc
        if not isinstance(item, dict):
            raise ValueError(f"line {line_no} is not an object")
        records.append(item)
    return records


def append_record(path: Path, record: dict) -> None:
    parent = path.parent
    if parent != Path("") and not parent.is_dir():
        raise FileNotFoundError("output directory does not exist")
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)


def group_by_id(records: list[dict]) -> list[dict]:
    order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for record in records:
        fact_id = record.get("id")
        if not isinstance(fact_id, str):
            continue
        if fact_id not in grouped:
            order.append(fact_id)
            grouped[fact_id] = []
        grouped[fact_id].append(record)
    return [{"id": fact_id, "records": grouped[fact_id]} for fact_id in order]


def command_write(args: argparse.Namespace) -> int:
    record = record_from_args(args)
    error = validation_error(record)
    if error:
        return fail(error)
    path = target_file(Path(args.out))
    if args.dry_run:
        emit({"ok": True, "dry_run": True, "path": str(path), "record": record})
        return 0
    try:
        append_record(path, record)
    except FileNotFoundError as exc:
        return fail(str(exc))
    emit({"ok": True, "dry_run": False, "path": str(path), "record": record})
    return 0


def command_retrieve(args: argparse.Namespace) -> int:
    keyword = args.keyword
    if not isinstance(keyword, str) or keyword == "":
        return fail("missing keyword")
    path = target_file(Path(args.out))
    try:
        records = read_records(path)
    except ValueError as exc:
        return fail(str(exc))
    matches = []
    for node in group_by_id(records):
        if any(keyword in str(item.get("text", "")) for item in node["records"]):
            matches.append(node)
    emit({"ok": True, "dry_run": bool(args.dry_run), "path": str(path), "matches": matches})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a Fact record or retrieve by keyword.")
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("--out", required=True)
    write.add_argument("--id", default="")
    write.add_argument("--verification-status", dest="verification_status", default="")
    write.add_argument("--text", default="")
    write.add_argument("--link", default=None)
    write.add_argument("--date", default=None)
    write.add_argument("--dry-run", action="store_true")
    write.set_defaults(func=command_write)

    retrieve = sub.add_parser("retrieve")
    retrieve.add_argument("--out", required=True)
    retrieve.add_argument("--keyword", default="")
    retrieve.add_argument("--dry-run", action="store_true")
    retrieve.set_defaults(func=command_retrieve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
