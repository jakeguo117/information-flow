#!/usr/bin/env python3
"""Deterministic weekly discussion-brief builder.

Pure computation: no vault writes, no network, no model calls.
The brief is a discussion draft. External author views are not Jake's beliefs.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
BRIEFS_DIR = "📋 Digests/weekly-briefs"

STATUSES = {"待讨论", "已讨论", "暂缓", "来源缺失/失败"}
DISCUSSED = "已讨论"
SOURCE_FAILED = "来源缺失/失败"

INDEX_HEADING = "本周索引"
CARRY_HEADING = "遗留候选"

_ENTRY_KEYS = ("id", "topic", "source_link", "source_week", "status")


def iso_week_label(day: dt.date) -> str:
    """Return ``YYYY-Www`` for an ISO week (Monday start).

    ``datetime.date`` is used as a calendar date. Aware datetimes are converted
    to Asia/Shanghai first. Naive datetimes are Shanghai wall time.
    """
    if isinstance(day, dt.datetime):
        if day.tzinfo is None:
            day = day.replace(tzinfo=SHANGHAI)
        else:
            day = day.astimezone(SHANGHAI)
        day = day.date()
    year, week, _weekday = day.isocalendar()
    return f"{year}-W{week:02d}"


def brief_rel_path(week_label: str) -> str:
    """Vault-relative path of the brief. This does not create the file."""
    return f"{BRIEFS_DIR}/{week_label}.md"


def _cell(value: object) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _normalize(raw: dict) -> dict:
    missing = [key for key in _ENTRY_KEYS if key not in raw]
    if missing:
        raise ValueError(f"entry missing fields: {', '.join(missing)}")
    entry = {key: _cell(raw[key]) for key in _ENTRY_KEYS}
    if not entry["id"]:
        raise ValueError("entry id is empty")
    if entry["status"] not in STATUSES:
        raise ValueError(f"unknown status: {entry['status']}")
    return entry


def _sort_key(entry: dict) -> tuple[str, str, str, str, str]:
    return (
        entry["topic"],
        entry["id"],
        entry["source_week"],
        entry["status"],
        entry["source_link"],
    )


def _dedupe(entries: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for entry in entries:
        current = best.get(entry["id"])
        if current is None or _sort_key(entry) < _sort_key(current):
            best[entry["id"]] = entry
    return sorted(best.values(), key=_sort_key)


def parse_brief_entries(text: str) -> list[dict]:
    """Read entries this builder previously printed. Invalid rows are skipped."""
    topic = ""
    current: dict | None = None
    found: list[dict] = []

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        if current["status"] in STATUSES and current["id"]:
            found.append(current)
        current = None

    for line in text.splitlines():
        if line.startswith("### "):
            flush()
            topic = line[4:].strip()
            continue
        if line.startswith("## "):
            flush()
            continue
        if line.startswith("- id: "):
            flush()
            current = {
                "id": line[len("- id: ") :].strip(),
                "topic": topic,
                "source_link": "",
                "source_week": "",
                "status": "",
            }
            continue
        if current is None or not line.startswith("  - "):
            continue
        body = line[len("  - ") :]
        if body.startswith("来源周: "):
            current["source_week"] = body[len("来源周: ") :].strip()
        elif body.startswith("来源: "):
            current["source_link"] = body[len("来源: ") :].strip()
        elif body.startswith("状态: "):
            current["status"] = body[len("状态: ") :].strip()
    flush()
    return found


def _carryover(previous_brief: str | None) -> dict[str, dict]:
    """Undiscussed rows from the previous brief, original source week kept.

    A row marked 已讨论 is not a candidate. Anything still 待讨论, 暂缓, or
    来源缺失/失败 is kept, and is not rewritten to 已讨论.
    """
    if not previous_brief:
        return {}
    discussed: set[str] = set()
    kept: dict[str, dict] = {}
    for entry in parse_brief_entries(previous_brief):
        if entry["status"] == DISCUSSED:
            discussed.add(entry["id"])
            kept.pop(entry["id"], None)
            continue
        if entry["id"] in discussed or entry["id"] in kept:
            continue
        kept[entry["id"]] = entry
    return kept


def _render_entry(entry: dict) -> list[str]:
    lines = [
        f"- id: {entry['id']}",
        f"  - 来源周: {entry['source_week']}",
        f"  - 来源: {entry['source_link']}",
    ]
    # Failed sources get no discussion slot and no summary. Nothing is invented.
    if entry["status"] != SOURCE_FAILED:
        lines.append("  - 讨论线索:")
    lines.append(f"  - 状态: {entry['status']}")
    return lines


def _render_section(heading: str, entries: list[dict]) -> str:
    lines = [f"## {heading}", ""]
    ordered = _dedupe(entries)
    if not ordered:
        lines.append("（无）")
        return "\n".join(lines)
    topic: str | None = None
    for entry in ordered:
        if entry["topic"] != topic:
            if topic is not None:
                lines.append("")
            topic = entry["topic"]
            lines.append(f"### {topic}")
            lines.append("")
        lines.extend(_render_entry(entry))
    return "\n".join(lines)


def build_brief(week_label: str, entries: list[dict], previous_brief: str | None = None) -> str:
    """Build one week's brief text. Does not read or write the vault.

    Current-week rows (``source_week`` equal to ``week_label``) are indexed by
    topic. Undiscussed rows from ``previous_brief``, and undiscussed rows whose
    ``source_week`` is an earlier week, go under ``## 遗留候选`` with the
    original source week, link, and status. Discussed rows are not carried.
    The same id is never listed as both fresh and carried. Ordering is by
    topic, then id.
    """
    week_label = _cell(week_label)
    if not week_label:
        raise ValueError("week_label is empty")
    if previous_brief is not None and not isinstance(previous_brief, str):
        raise TypeError("previous_brief must be a string or None")

    carried = _carryover(previous_brief)
    fresh: list[dict] = []
    for entry in _dedupe([_normalize(raw) for raw in entries]):
        if entry["id"] in carried:
            continue
        prior_week = entry["source_week"] != week_label
        if prior_week and entry["status"] != DISCUSSED:
            carried[entry["id"]] = entry
            continue
        fresh.append(entry)

    parts = [
        f"# {week_label}",
        "",
        "> 讨论草稿。外部作者观点不是 Jake 的信念。",
        "",
        _render_section(INDEX_HEADING, fresh),
        "",
        _render_section(CARRY_HEADING, list(carried.values())),
        "",
    ]
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    """Print a brief from stdin JSON. Does not read or write files."""
    del argv
    if sys.stdin.isatty():
        print(
            "wj_weekly_brief reads JSON on stdin and prints a brief; it does not write files",
            file=sys.stderr,
        )
        return 2
    raw = sys.stdin.read()
    if not raw.strip():
        print("expected JSON on stdin", file=sys.stderr)
        return 2
    payload = json.loads(raw)
    text = build_brief(
        payload["week_label"],
        payload.get("entries") or [],
        payload.get("previous_brief"),
    )
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
