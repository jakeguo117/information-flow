#!/usr/bin/env python3
"""Select one Thursday inbox batch and mark the selection processing.

Writes ``{vault}/📋 Digests/cycles/{cycle_id}/batch.json``. This step only
selects. AI processing is later, so ``process_version`` is null.

``cycle_id`` is ``cy-YYYYMMDD`` and the date must be a Thursday. ``cutoff_at``
defaults to 08:00 Asia/Hong_Kong on that date. ``coverage_start`` is the
previous cycle batch's ``cutoff_at``. When no earlier ``batch.json`` exists,
coverage starts seven days before this cutoff (the previous Thursday 08:00).

An input is selected when ``received_at`` <= ``cutoff_at`` and
``process_state`` is ``pending``, ``retry_pending``, or ``failed``. Scan all
weeks. ``received_at`` after the cutoff is ``late_input_ids`` and is not
selected. ``source_week`` is not written.

The batch file is written before any state line. A later run that finds this
cycle's ``batch.json`` keeps that selection and does not rewrite the file,
including when a fresh scan would now differ because selected rows are already
``processing``. Rows still in a selectable state move to ``processing`` with
``last_cycle_id`` set to this cycle via ``append_state``. An identical state
is not appended again.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import inbox_lib
from inbox_index import append_state, read_index

SELECTABLE = ("pending", "retry_pending", "failed")
STATUS_KEY = "每条记录开始和结束时的状态"
END_STATE = "processing"
CYCLE_RE = re.compile(r"^cy-(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})$")
CYCLES_DIR = Path("📋 Digests") / "cycles"


def process_batch(
    vault: Path,
    index_dir: Path,
    cycle_id: str,
    *,
    cutoff_at: str | None = None,
    at: str | None = None,
) -> dict:
    """Select ``cycle_id`` under ``vault`` from the index in ``index_dir``."""

    cycle_id = _cycle_id(cycle_id)
    cutoff = _stamp(cutoff_at) if cutoff_at else _default_cutoff(cycle_id)
    stamp = _stamp(at) if at else inbox_lib.format_hk(datetime.now(inbox_lib.HK))
    path = batch_path(vault, cycle_id)
    _sources, inputs = read_index(index_dir)
    if path.is_file():
        batch = _existing_batch(path, cycle_id, cutoff)
        _mark_processing(index_dir, inputs, list(batch["selected_input_ids"]), cycle_id, stamp)
        return batch
    selected, late = select_ids(inputs, cutoff)
    batch = _payload(inputs, cycle_id, cutoff, _coverage_start(vault, cycle_id, cutoff), selected, late)
    _write_batch(path, batch)
    _mark_processing(index_dir, inputs, selected, cycle_id, stamp)
    return batch


def batch_path(vault: Path, cycle_id: str) -> Path:
    return vault / CYCLES_DIR / cycle_id / "batch.json"


def select_ids(inputs: list[dict], cutoff_at: str) -> tuple[list[str], list[str]]:
    """Return ``(selected_input_ids, late_input_ids)`` in index order."""

    cutoff = _moment(cutoff_at)
    selected: list[str] = []
    late: list[str] = []
    seen: set[str] = set()
    for item in inputs:
        input_id = item.get("input_id")
        if not isinstance(input_id, str) or not input_id:
            raise ValueError("input is missing input_id")
        if input_id in seen:
            continue
        received = item.get("received_at")
        if not isinstance(received, str):
            raise ValueError(f"input {input_id} has no received_at")
        moment = inbox_lib.parse_time(received)
        if moment is None:
            raise ValueError(f"input {input_id} has no received_at")
        seen.add(input_id)
        if moment > cutoff:
            late.append(input_id)
        elif item.get("process_state") in SELECTABLE:
            selected.append(input_id)
    return selected, late


def _payload(
    inputs: list[dict],
    cycle_id: str,
    cutoff: str,
    coverage: str,
    selected: list[str],
    late: list[str],
) -> dict:
    by_id = {item["input_id"]: item for item in inputs}
    return {
        "cycle_id": cycle_id,
        "cutoff_at": cutoff,
        "coverage_start": coverage,
        "selected_input_ids": selected,
        "late_input_ids": late,
        STATUS_KEY: [
            {
                "input_id": input_id,
                "开始": by_id[input_id].get("process_state"),
                "结束": END_STATE,
            }
            for input_id in selected
        ],
        "process_version": None,
    }


def _mark_processing(
    index_dir: Path,
    inputs: list[dict],
    selected: list[str],
    cycle_id: str,
    at: str,
) -> None:
    by_id = {item["input_id"]: item for item in inputs}
    for input_id in selected:
        item = by_id.get(input_id)
        if item is None:
            raise ValueError(f"unknown input_id: {input_id}")
        if item.get("process_state") not in SELECTABLE:
            continue
        error = item.get("last_error")
        append_state(
            index_dir,
            input_id,
            END_STATE,
            at=at,
            last_error=error if isinstance(error, str) and error else None,
            last_cycle_id=cycle_id,
        )


def _existing_batch(path: Path, cycle_id: str, cutoff: str) -> dict:
    batch = _read_batch(path)
    if batch.get("cycle_id") != cycle_id:
        raise ValueError("batch.json cycle_id conflicts with this run; not rewriting")
    stored = batch.get("cutoff_at")
    if not isinstance(stored, str) or _stamp(stored) != cutoff:
        raise ValueError("batch.json cutoff_at conflicts with this run; not rewriting")
    selected = batch.get("selected_input_ids")
    if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected):
        raise ValueError("batch.json selected_input_ids must be a list of ids")
    return batch


def _coverage_start(vault: Path, cycle_id: str, cutoff: str) -> str:
    current = _cycle_day(cycle_id)
    best_day: datetime | None = None
    best_cutoff: str | None = None
    root = vault / CYCLES_DIR
    if root.is_dir():
        for path in sorted(root.glob("cy-*/batch.json")):
            name = path.parent.name
            if name == cycle_id or CYCLE_RE.match(name) is None:
                continue
            day = _cycle_day(name)
            if day >= current:
                continue
            if best_day is not None and day <= best_day:
                continue
            previous = _read_batch(path).get("cutoff_at")
            if not isinstance(previous, str):
                raise ValueError(f"{path} missing cutoff_at")
            best_day = day
            best_cutoff = _stamp(previous)
    if best_cutoff is not None:
        return best_cutoff
    return inbox_lib.format_hk(_moment(cutoff) - timedelta(days=7))


def _default_cutoff(cycle_id: str) -> str:
    day = _cycle_day(cycle_id)
    return inbox_lib.format_hk(datetime(day.year, day.month, day.day, 8, 0, 0, tzinfo=inbox_lib.HK))


def _cycle_id(cycle_id: str) -> str:
    _cycle_day(cycle_id)
    return cycle_id


def _cycle_day(cycle_id: str) -> datetime:
    match = CYCLE_RE.match(cycle_id)
    if match is None:
        raise ValueError(f"cycle_id must look like cy-YYYYMMDD: {cycle_id}")
    day = datetime(int(match.group("y")), int(match.group("m")), int(match.group("d")))
    if day.weekday() != 3:
        raise ValueError(f"cycle_id must be a Thursday: {cycle_id}")
    return day


def _moment(raw: str) -> datetime:
    moment = inbox_lib.parse_time(raw)
    if moment is None:
        raise ValueError(f"timestamp must include a date: {raw!r}")
    return moment


def _stamp(raw: str) -> str:
    return inbox_lib.format_hk(_moment(raw))


def _read_batch(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} is not json") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} is not an object")
    return data


def _write_batch(path: Path, batch: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select a Thursday inbox batch.")
    parser.add_argument("--vault", required=True, help="Vault root for 📋 Digests/cycles")
    parser.add_argument("--index", required=True, help="Directory with inputs.jsonl")
    parser.add_argument("--cycle-id", required=True, help="cy-YYYYMMDD Thursday")
    parser.add_argument("--cutoff-at", default=None, help="ISO 8601 cutoff. Default: Thursday 08:00 HK")
    parser.add_argument("--at", default=None, help="Clock for state events. Default: now in Hong Kong")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        batch = process_batch(
            Path(args.vault),
            Path(args.index),
            args.cycle_id,
            cutoff_at=args.cutoff_at,
            at=args.at,
        )
    except ValueError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1
    json.dump({"ok": True, "batch": batch}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
