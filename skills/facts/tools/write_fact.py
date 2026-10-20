#!/usr/bin/env python3
"""Append-only Fact records.

The caller chooses the output file or directory. Field rules live in
references/schema.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA_VERSION = "facts-0.1"
VALIDATION_STATES = ("unverified", "verified", "disputed", "corrected")
DEFAULT_VISIBILITY = "private-jake"
DIRECTORY_LOG_NAME = "facts.jsonl"
FACT_ID_RE = re.compile(r"^fact-[0-9a-f]{12}$")
AS_OF_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AS_OF_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
HONG_KONG = ZoneInfo("Asia/Hong_Kong")
HONG_KONG_OFFSET = timedelta(hours=8)


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


def compute_fact_id(source_ref: str, statement: str) -> str:
    digest = hashlib.sha1(f"{source_ref}|{statement}".encode("utf-8")).hexdigest()[:12]
    return f"fact-{digest}"


def blank(value: object) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def as_of_error(value: str) -> str | None:
    if AS_OF_DATE_RE.fullmatch(value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return "invalid as_of"
        return None
    if AS_OF_INSTANT_RE.fullmatch(value):
        try:
            parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return "invalid as_of"
        if parsed.utcoffset() != HONG_KONG_OFFSET:
            return "invalid as_of"
        return None
    return "invalid as_of"


def field_error(args: argparse.Namespace) -> str | None:
    if args.schema_version != SCHEMA_VERSION:
        return "unknown schema_version"
    if args.fact_id is not None and blank(args.fact_id):
        return "missing fact_id"
    if blank(args.statement):
        return "missing statement"
    refs = args.source_ref or []
    if not refs or any(blank(item) for item in refs):
        return "missing source_refs"
    if blank(args.as_of):
        return "missing as_of"
    if as_of_error(args.as_of):
        return "invalid as_of"
    if blank(args.validation_state):
        return "missing validation_state"
    if args.validation_state not in VALIDATION_STATES:
        return "invalid validation_state"
    return None


def parent_error(path: Path) -> str | None:
    parent = path.parent
    if parent != Path("") and not parent.is_dir():
        return "output directory does not exist"
    return None


def newline_error(path: Path) -> str | None:
    if not path.is_file():
        return None
    if path.stat().st_size == 0:
        return None
    with path.open("rb") as handle:
        handle.seek(-1, 2)
        if handle.read(1) != b"\n":
            return "output file must end with a newline"
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


def existing_fact_ids(path: Path) -> set[str]:
    found: set[str] = set()
    for record in read_records(path):
        fact_id = record.get("fact_id")
        if isinstance(fact_id, str):
            found.add(fact_id)
    return found


def resolve_fact_id(path: Path, provided: str | None, source_ref: str, statement: str) -> tuple[str, str | None]:
    if provided is None:
        return compute_fact_id(source_ref, statement), None
    if not FACT_ID_RE.fullmatch(provided):
        return "", "invalid fact_id"
    if provided in existing_fact_ids(path):
        return provided, None
    expected = compute_fact_id(source_ref, statement)
    if provided != expected:
        return "", "fact_id does not match formula"
    return provided, None


def record_from_args(args: argparse.Namespace, fact_id: str) -> dict:
    record: dict = {
        "schema_version": SCHEMA_VERSION,
        "fact_id": fact_id,
        "statement": args.statement,
        "source_refs": list(args.source_ref),
        "as_of": args.as_of,
        "validation_state": args.validation_state,
        "visibility": args.visibility if args.visibility else DEFAULT_VISIBILITY,
        "recorded_at": datetime.now(HONG_KONG).isoformat(timespec="seconds"),
    }
    for key, value in (
        ("measurement_scope", args.measurement_scope),
        ("limitations", args.limitations),
        ("validation_basis", args.validation_basis),
    ):
        if value:
            record[key] = value
    return record


def append_record(path: Path, record: dict) -> None:
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)


def group_by_id(records: list[dict]) -> list[dict]:
    order: list[str] = []
    grouped: dict[str, list[dict]] = {}
    for record in records:
        fact_id = record.get("fact_id")
        if not isinstance(fact_id, str):
            continue
        if fact_id not in grouped:
            order.append(fact_id)
            grouped[fact_id] = []
        grouped[fact_id].append(record)
    return [{"fact_id": fact_id, "records": grouped[fact_id]} for fact_id in order]


def command_write(args: argparse.Namespace) -> int:
    error = field_error(args)
    if error:
        return fail(error)
    path = target_file(Path(args.out))
    error = parent_error(path) or newline_error(path)
    if error:
        return fail(error)
    try:
        fact_id, error = resolve_fact_id(path, args.fact_id, args.source_ref[0], args.statement)
    except ValueError as exc:
        return fail(str(exc))
    if error:
        return fail(error)
    record = record_from_args(args, fact_id)
    if args.dry_run:
        emit({"ok": True, "dry_run": True, "path": str(path), "record": record})
        return 0
    append_record(path, record)
    emit({"ok": True, "dry_run": False, "path": str(path), "record": record})
    return 0


def command_retrieve(args: argparse.Namespace) -> int:
    keyword = args.keyword
    if not isinstance(keyword, str) or keyword == "":
        return fail("missing keyword")
    path = target_file(Path(args.out))
    error = parent_error(path)
    if error:
        return fail(error)
    try:
        records = read_records(path)
    except ValueError as exc:
        return fail(str(exc))
    matches = []
    for node in group_by_id(records):
        if any(keyword in str(item.get("statement", "")) for item in node["records"]):
            matches.append(node)
    emit({"ok": True, "dry_run": bool(args.dry_run), "path": str(path), "matches": matches})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a Fact record or retrieve by keyword.")
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write")
    write.add_argument("--out", required=True)
    write.add_argument("--fact-id", dest="fact_id", default=None)
    write.add_argument("--statement", default="")
    write.add_argument("--source-ref", dest="source_ref", action="append")
    write.add_argument("--as-of", dest="as_of", default="")
    write.add_argument("--validation-state", dest="validation_state", default="")
    write.add_argument("--measurement-scope", dest="measurement_scope", default=None)
    write.add_argument("--limitations", default=None)
    write.add_argument("--validation-basis", dest="validation_basis", default=None)
    write.add_argument("--visibility", default=None)
    write.add_argument("--schema-version", dest="schema_version", default=SCHEMA_VERSION)
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
