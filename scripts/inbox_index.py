#!/usr/bin/env python3
"""Append-only inbox-0.1 index for Sources and Inputs.

Writes ``sources.jsonl`` and ``inputs.jsonl`` (one JSON object per line).
Does not run git and does not edit Inbox notes. The caller supplies
``received_at_lookup``; this module puts that callable, plus index first-seen
hooks, on ``ParseContext`` before calling ``inbox_lib``.

State changes are later lines in ``inputs.jsonl`` (``record_type`` = ``state``).
Readers apply the latest state line for each ``input_id`` on top of the
original input line. The schema still says the state-event table is filled
by T11; this module owns the lines it appends.

``--dry-run`` plans the same lines and writes nothing.

A file that is not a note, and a note that fails to parse, is skipped.
The jsonl record fields do not change. Success JSON adds ``skipped``
(objects ``{"path", "reason"}``, paths relative to ``--inbox``) and
``skipped_count``. Discovery uses ``reason`` ``not_a_note``; a parse
failure uses the parser message. See ``discover_notes``. ``IndexConflict``,
a bad received-at map, and IO errors still fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import inbox_lib

SOURCES_NAME = "sources.jsonl"
INPUTS_NAME = "inputs.jsonl"
STATE_RECORD = "state"
PROCESS_STATES = ("pending", "processing", "completed", "failed", "retry_pending")
# Kickoff §4: the 2021–2022 Instagram batch is a historical import.
HISTORICAL_THROUGH_YEAR = 2022
# Discovery skip. Parse failures use the parser message instead.
NOT_A_NOTE = "not_a_note"

_PLATFORM_DIRS = (
    ("youtube", "📥 Inbox/YouTube-Likes"),
    ("snipd", "📥 Inbox/Snipd"),
    ("weread", "📥 Inbox/WeRead"),
    ("x", "📥 Inbox/X-Bookmarks"),
    ("instagram", "📥 Inbox/Instagram-Saves"),
    ("thought", "📝 Journal/想法"),
)
_FILENAME_DATE = re.compile(r"(20\d{2})-\d{2}-\d{2}")
_IG_PUBLISHED = re.compile(r"视频发布时间\s*[:：]\s*(20\d{2})")
_EMPTY_FINGERPRINT = inbox_lib.content_fingerprint("")
_FROM_EXISTING_INPUT = (
    "received_at",
    "process_state",
    "last_error",
    "last_cycle_id",
    "topics",
    "summary_ref",
    "process_version",
    "suspected_duplicate_of",
    "inbox_ref",
)


@dataclass(frozen=True)
class InboxNote:
    """One synthetic or vault note. ``path`` is the vault-relative ref."""

    path: str
    text: str
    platform: str
    origin: str | None = None


@dataclass(frozen=True)
class Discovery:
    """Platform notes plus files skipped before parse.

    ``skipped`` items are ``{"path", "reason"}``. ``reason`` is
    ``not_a_note`` for the narrow rule in ``_non_note_reason``.
    ``_index``, ``processed``, and dot-directories are not listed: they
    are index machinery, not candidate notes.
    """

    notes: list[InboxNote]
    skipped: list[dict[str, str]]


@dataclass(frozen=True)
class FieldDiff:
    record_id: str
    field: str
    existing: object
    proposed: object


class IndexConflict(Exception):
    """On-disk index does not match this run. Nothing new is appended."""

    def __init__(self, diffs: list[FieldDiff]):
        self.diffs = diffs
        lines = [
            f"{item.record_id}.{item.field}: {item.existing!r} != {item.proposed!r}"
            for item in diffs
        ]
        super().__init__("index differs from stored record; not writing\n" + "\n".join(lines))


@dataclass
class IndexResult:
    dry_run: bool
    sources: list[dict]
    inputs: list[dict]
    created_source_ids: list[str]
    created_input_ids: list[str]
    existing_input_ids: list[str]
    planned_sources: list[dict]
    planned_inputs: list[dict]
    skipped: list[dict[str, str]]


def inputs_for_week(inputs: list[dict], week: str) -> list[dict]:
    """Inputs whose ``source_week`` is ``week``. Empty weeks are not new."""

    return [item for item in inputs if item.get("source_week") == week]


def discover_notes(root: Path) -> Discovery:
    """Read platform note trees under a vault root or an Inbox directory.

    Non-notes are omitted from ``notes`` and listed in ``skipped`` with
    ``reason`` ``not_a_note``. The rule is ``_non_note_reason`` only.
    Parse failures are decided later, one note at a time.
    """

    if not root.is_dir():
        raise ValueError(f"inbox path is not a directory: {root}")
    notes: list[InboxNote] = []
    skipped: list[dict[str, str]] = []
    seen: set[Path] = set()
    for platform, rel in _PLATFORM_DIRS:
        base = _platform_dir(root, rel)
        if base is None:
            continue
        for path in sorted(base.rglob("*.md")):
            if not path.is_file() or _skipped(path, base):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            note_path = _note_ref(path, root)
            reason = _non_note_reason(path, base)
            if reason is not None:
                skipped.append({"path": note_path, "reason": reason})
                continue
            notes.append(InboxNote(note_path, path.read_text(encoding="utf-8"), platform))
    return Discovery(notes, skipped)


def index_notes(
    notes: list[InboxNote],
    index_dir: Path,
    *,
    now: str,
    received_at_lookup: Callable[[str], str | None] | None = None,
    dry_run: bool = False,
) -> IndexResult:
    """Parse notes and append new Source / Input lines. Same event returns the old id.

    ``NoteParseError`` skips that note. Other notes are still indexed.
    ``skipped`` lists those parse failures and does not include discovery
    skips. Record fields are unchanged.
    """

    clock = _clock(now)
    sources_path = index_dir / SOURCES_NAME
    inputs_path = index_dir / INPUTS_NAME
    _ensure_appendable(sources_path)
    _ensure_appendable(inputs_path)

    sources = _read_jsonl(sources_path)
    input_lines = _read_jsonl(inputs_path)
    bases, events = _split_inputs(input_lines)
    working_sources = list(sources)
    working_inputs = list(bases)
    planned_sources: list[dict] = []
    planned_inputs: list[dict] = []
    created_source_ids: list[str] = []
    created_input_ids: list[str] = []
    existing_input_ids: list[str] = []
    diffs: list[FieldDiff] = []
    skipped: list[dict[str, str]] = []

    for note in notes:
        try:
            parsed, existing_source = _parse_with_index(
                note, working_sources, working_inputs, clock, received_at_lookup
            )
        except inbox_lib.NoteParseError as exc:
            skipped.append({"path": note.path, "reason": str(exc)})
            continue
        source = parsed["source"]
        if existing_source is None:
            planned_sources.append(source)
            created_source_ids.append(source["source_id"])
            working_sources.append(source)
        else:
            diffs.extend(
                _diff_record(
                    existing_source["source_id"],
                    existing_source,
                    _stabilize_source(source, existing_source),
                )
            )
        for item in parsed["inputs"]:
            existing_item = _find_input(working_inputs, item)
            if existing_item is None:
                fresh = dict(item)
                owner = _fingerprint_owner(working_inputs, fresh["content_fingerprint"])
                if owner is not None:
                    fresh["suspected_duplicate_of"] = owner
                planned_inputs.append(fresh)
                created_input_ids.append(fresh["input_id"])
                working_inputs.append(fresh)
            else:
                item_diffs = _diff_record(
                    existing_item["input_id"],
                    existing_item,
                    _stabilize_input(item, existing_item),
                )
                if item_diffs:
                    diffs.extend(item_diffs)
                else:
                    existing_input_ids.append(existing_item["input_id"])

    if diffs:
        raise IndexConflict(diffs)
    if not dry_run:
        for record in planned_sources:
            _append_and_readback(sources_path, record)
        for record in planned_inputs:
            _append_and_readback(inputs_path, record)
        sources = _read_jsonl(sources_path)
        bases, events = _split_inputs(_read_jsonl(inputs_path))
        visible_inputs = _apply_state(bases, events)
    else:
        visible_inputs = _apply_state(working_inputs, events)
        sources = working_sources
    return IndexResult(
        dry_run=dry_run,
        sources=sources,
        inputs=visible_inputs,
        created_source_ids=created_source_ids,
        created_input_ids=created_input_ids,
        existing_input_ids=existing_input_ids,
        planned_sources=planned_sources,
        planned_inputs=planned_inputs,
        skipped=skipped,
    )


def append_state(
    index_dir: Path,
    input_id: str,
    process_state: str,
    *,
    at: str,
    last_error: str | None = None,
    last_cycle_id: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Append one state line. The latest line for ``input_id`` wins. Identical state is not rewritten."""

    if process_state not in PROCESS_STATES:
        raise ValueError(f"process_state must be one of {PROCESS_STATES}")
    if process_state == "failed" and not last_error:
        raise ValueError("failed state requires last_error")
    moment = _clock(at)
    inputs_path = index_dir / INPUTS_NAME
    _ensure_appendable(inputs_path)
    bases, events = _split_inputs(_read_jsonl(inputs_path))
    if not any(item.get("input_id") == input_id for item in bases):
        raise ValueError(f"unknown input_id: {input_id}")
    event: dict = {
        "schema_version": inbox_lib.SCHEMA_VERSION,
        "record_type": STATE_RECORD,
        "input_id": input_id,
        "process_state": process_state,
        "at": moment,
    }
    if last_error is not None:
        event["last_error"] = last_error
    if last_cycle_id is not None:
        event["last_cycle_id"] = last_cycle_id
    base = next(item for item in bases if item["input_id"] == input_id)
    projected = dict(base)
    projected["process_state"] = process_state
    if last_error is not None:
        projected["last_error"] = last_error
    if last_cycle_id is not None:
        projected["last_cycle_id"] = last_cycle_id
    current = next(item for item in _apply_state(bases, events) if item["input_id"] == input_id)
    unchanged = (
        projected.get("process_state") == current.get("process_state")
        and projected.get("last_error") == current.get("last_error")
        and projected.get("last_cycle_id") == current.get("last_cycle_id")
    )
    if unchanged:
        return {"written": False, "dry_run": dry_run, "would_write": False, "event": event}
    if dry_run:
        return {"written": False, "dry_run": True, "would_write": True, "event": event}
    _append_and_readback(inputs_path, event)
    return {"written": True, "dry_run": False, "would_write": True, "event": event}


def read_index(index_dir: Path) -> tuple[list[dict], list[dict]]:
    """Return sources and inputs with the latest state event applied."""

    sources = _read_jsonl(index_dir / SOURCES_NAME)
    bases, events = _split_inputs(_read_jsonl(index_dir / INPUTS_NAME))
    return sources, _apply_state(bases, events)


def _parse_with_index(
    note: InboxNote,
    sources: list[dict],
    inputs: list[dict],
    clock: str,
    received_at_lookup: Callable[[str], str | None] | None,
) -> tuple[dict, dict | None]:
    origin = note.origin or _infer_origin(note)
    seen, known = _seen_maps(inputs)

    def lookup(item_id: str) -> str | None:
        if received_at_lookup is None:
            return None
        return received_at_lookup(item_id)

    def item_first_seen(item_id: str) -> str | None:
        if item_id in seen:
            return seen[item_id]
        if item_id in known:
            return None
        return clock

    def parse(first_seen: str, revision: int) -> dict:
        ctx = inbox_lib.ParseContext(
            path=note.path,
            first_seen_at=first_seen,
            received_at=None,
            received_at_lookup=lookup,
            item_first_seen_at=item_first_seen,
            origin=origin,
            content_revision=revision,
        )
        return inbox_lib.parse_note(note.text, note.platform, ctx)

    parsed = parse(clock, 1)
    existing = _find_source(sources, parsed["source"])
    if existing is None:
        return parsed, None
    parsed = parse(existing["first_seen_at"], int(existing["content_revision"]))
    return parsed, existing


def _infer_origin(note: InboxNote) -> str:
    if note.platform != "instagram":
        return "collected"
    named = _FILENAME_DATE.search(Path(note.path).name)
    if named:
        year = int(named.group(1))
    else:
        published = _IG_PUBLISHED.search(note.text)
        year = int(published.group(1)) if published else None
    if year is not None and year <= HISTORICAL_THROUGH_YEAR:
        return "historical_import"
    return "collected"


def _seen_maps(inputs: list[dict]) -> tuple[dict[str, str], set[str]]:
    seen: dict[str, str] = {}
    known: set[str] = set()
    for item in inputs:
        ext = item.get("external_item_id")
        if not isinstance(ext, str) or not ext:
            continue
        known.add(ext)
        captured = item.get("captured_at")
        if item.get("time_basis") == "first_seen" and isinstance(captured, str):
            seen[ext] = captured
    return seen, known


def _find_source(sources: list[dict], proposed: dict) -> dict | None:
    platform = proposed["platform"]
    external = proposed.get("external_content_id")
    if external:
        for source in sources:
            if source.get("platform") == platform and source.get("external_content_id") == external:
                return source
    url = proposed.get("canonical_url")
    for source in sources:
        if source.get("platform") == platform and source.get("canonical_url") == url:
            return source
    return None


def _find_input(inputs: list[dict], proposed: dict) -> dict | None:
    for item in inputs:
        if item.get("input_id") == proposed["input_id"]:
            return item
    external = proposed.get("external_item_id")
    if not external:
        return None
    prefix = proposed["input_id"].split("-", 2)[1]
    for item in inputs:
        if item.get("external_item_id") != external:
            continue
        if item.get("input_id", "").split("-", 2)[1] == prefix:
            return item
    return None


def _fingerprint_owner(inputs: list[dict], fingerprint: str) -> str | None:
    if not fingerprint or fingerprint == _EMPTY_FINGERPRINT:
        return None
    for item in inputs:
        if item.get("content_fingerprint") == fingerprint:
            return item["input_id"]
    return None


def _stabilize_source(proposed: dict, existing: dict) -> dict:
    stabilized = dict(proposed)
    stabilized["raw_refs"] = list(existing.get("raw_refs") or [])
    stabilized["first_seen_at"] = existing.get("first_seen_at")
    stabilized["content_revision"] = existing.get("content_revision")
    return stabilized


def _stabilize_input(proposed: dict, existing: dict) -> dict:
    stabilized = dict(proposed)
    for key in _FROM_EXISTING_INPUT:
        if key in existing:
            stabilized[key] = existing[key]
    return stabilized


def _diff_record(record_id: str, existing: dict, proposed: dict) -> list[FieldDiff]:
    keys = list(existing.keys())
    for key in proposed:
        if key not in existing:
            keys.append(key)
    diffs: list[FieldDiff] = []
    for key in keys:
        if existing.get(key) != proposed.get(key):
            diffs.append(FieldDiff(record_id, key, existing.get(key), proposed.get(key)))
    return diffs


def _apply_state(bases: list[dict], events: list[dict]) -> list[dict]:
    latest: dict[str, dict] = {}
    for event in events:
        input_id = event.get("input_id")
        if isinstance(input_id, str):
            latest[input_id] = event
    applied: list[dict] = []
    for base in bases:
        item = dict(base)
        event = latest.get(item.get("input_id"))
        if event:
            item["process_state"] = event["process_state"]
            if "last_error" in event:
                item["last_error"] = event["last_error"]
            if "last_cycle_id" in event:
                item["last_cycle_id"] = event["last_cycle_id"]
        applied.append(item)
    return applied


def _split_inputs(records: list[dict]) -> tuple[list[dict], list[dict]]:
    bases: list[dict] = []
    events: list[dict] = []
    for record in records:
        if record.get("record_type") == STATE_RECORD:
            events.append(record)
        else:
            bases.append(record)
    return bases, events


def _append_and_readback(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ensure_appendable(path)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
    last = _last_record(path)
    if last != record:
        record_id = str(record.get("input_id") or record.get("source_id") or path.name)
        raise IndexConflict([FieldDiff(record_id, "<line>", last, record)])


def _ensure_appendable(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("rb") as handle:
        handle.seek(-1, 2)
        if handle.read(1) != b"\n":
            raise ValueError(f"{path.name} must end with a newline")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip() == "":
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} line {line_no} is not json") from exc
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} line {line_no} is not an object")
        records.append(item)
    return records


def _last_record(path: Path) -> dict | None:
    records = _read_jsonl(path)
    return records[-1] if records else None


def _clock(raw: str) -> str:
    moment = inbox_lib.parse_time(raw)
    if moment is None:
        raise ValueError(f"timestamp must include a date: {raw!r}")
    return inbox_lib.format_hk(moment)


def _platform_dir(root: Path, rel: str) -> Path | None:
    for candidate in (root / rel, root / Path(rel).name):
        if candidate.is_dir():
            return candidate
    return None


def _skipped(path: Path, base: Path) -> bool:
    """Index machinery. These paths are not listed in ``skipped``."""

    parts = path.relative_to(base).parts
    return any(part in {"_index", "processed"} or part.startswith(".") for part in parts)


def _non_note_reason(path: Path, base: Path) -> str | None:
    """Return ``not_a_note`` for files that live in a platform tree but are not notes.

    The rule is narrow and explicit:

    - The filename is ``README.md``, compared case-insensitively. Plugin
      folders keep a guide under that name (``📥 Inbox/Snipd/README.md``).
    - A directory component relative to the platform root is exactly
      ``digests``. Generated digests under ``📝 Journal/想法/digests/``
      are not thought notes.

    Anything else is a candidate note. A thought missing 「原话」, or a
    Snipd file other than ``README.md`` with no ``episode_url``, is parsed
    and then skipped with the parser message.
    """

    if path.name.casefold() == "readme.md":
        return NOT_A_NOTE
    if "digests" in path.relative_to(base).parts[:-1]:
        return NOT_A_NOTE
    return None


def _note_ref(path: Path, root: Path) -> str:
    if path.is_relative_to(root):
        return path.relative_to(root).as_posix()
    return path.as_posix()


def _load_received_at_map(path: Path) -> Callable[[str], str | None]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("received-at map must be a JSON object")

    def lookup(item_id: str) -> str | None:
        value = data.get(item_id)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("received-at map values must be timestamps")
        return value

    return lookup


def _emit(payload: dict) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append-only inbox-0.1 source and input index.")
    parser.add_argument("--inbox", required=True, help="Vault root or Inbox directory")
    parser.add_argument("--index", required=True, help="Directory for sources.jsonl and inputs.jsonl")
    parser.add_argument("--now", default=None, help="Index clock, ISO 8601. Default: current Hong Kong time")
    parser.add_argument(
        "--received-at-map",
        default=None,
        help="JSON object of item id to received_at. This command does not run git.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute lines and write nothing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    now = args.now or inbox_lib.format_hk(datetime.now(inbox_lib.HK))
    try:
        lookup = _load_received_at_map(Path(args.received_at_map)) if args.received_at_map else None
        found = discover_notes(Path(args.inbox))
        result = index_notes(
            found.notes,
            Path(args.index),
            now=now,
            received_at_lookup=lookup,
            dry_run=args.dry_run,
        )
    except IndexConflict as exc:
        _emit(
            {
                "ok": False,
                "error": "diff",
                "message": str(exc),
                "diffs": [
                    {
                        "record_id": item.record_id,
                        "field": item.field,
                        "existing": item.existing,
                        "proposed": item.proposed,
                    }
                    for item in exc.diffs
                ],
            }
        )
        return 1
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)})
        return 1
    skipped = [*found.skipped, *result.skipped]
    _emit(
        {
            "ok": True,
            "dry_run": result.dry_run,
            "created_source_ids": result.created_source_ids,
            "created_input_ids": result.created_input_ids,
            "existing_input_ids": result.existing_input_ids,
            "source_count": len(result.sources),
            "input_count": len(result.inputs),
            "skipped": skipped,
            "skipped_count": len(skipped),
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
