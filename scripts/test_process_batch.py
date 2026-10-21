#!/usr/bin/env python3
"""Synthetic Thursday batch selection. No private notes, no git, no network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inbox_index  # noqa: E402
import process_batch  # noqa: E402

STATUS = "每条记录开始和结束时的状态"


def row(
    input_id: str,
    *,
    received_at: str,
    source_week: str | None = "2026-W42",
    process_state: str = "pending",
) -> dict:
    return {
        "schema_version": "inbox-0.1",
        "input_id": input_id,
        "source_id": "src-manual-usynth0000001",
        "external_item_id": None,
        "event_type": "note",
        "captured_at": "2026-10-14T09:30:00+08:00",
        "time_basis": "platform",
        "received_at": received_at,
        "source_published_at": None,
        "source_week": source_week,
        "origin": "collected",
        "content_fingerprint": "synthetic",
        "completeness": "full",
        "missing_reason": None,
        "process_state": process_state,
        "last_error": None,
        "last_cycle_id": None,
        "topics": None,
        "summary_ref": None,
        "process_version": None,
        "suspected_duplicate_of": None,
        "inbox_ref": f"📥 Inbox/manual/{input_id}.md#note",
    }


def seed(index: Path, rows: list[dict]) -> None:
    index.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows)
    (index / inbox_index.INPUTS_NAME).write_text(text, encoding="utf-8")
    (index / inbox_index.SOURCES_NAME).write_text("", encoding="utf-8")


def records(index: Path) -> list[dict]:
    path = index / inbox_index.INPUTS_NAME
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def by_id(index: Path) -> dict[str, dict]:
    _sources, inputs = inbox_index.read_index(index)
    return {item["input_id"]: item for item in inputs}


def test_after_cutoff_next_batch(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    early = "in-manual-early000001"
    on_time = "in-manual-ontime00001"
    late = "in-manual-late0000001"
    seed(
        index,
        [
            row(early, received_at="2026-10-14T10:00:00+08:00"),
            row(on_time, received_at="2026-10-15T08:00:00+08:00"),
            row(late, received_at="2026-10-15T08:05:00+08:00"),
        ],
    )
    batch = process_batch.process_batch(
        vault,
        index,
        "cy-20261015",
        cutoff_at="2026-10-15T08:00:00+08:00",
        at="2026-10-15T08:00:01+08:00",
    )
    assert batch["selected_input_ids"] == [early, on_time]
    assert batch["late_input_ids"] == [late]
    assert late not in batch["selected_input_ids"]
    assert batch["coverage_start"] == "2026-10-08T08:00:00+08:00"
    assert batch["process_version"] is None
    states = by_id(index)
    assert states[early]["process_state"] == "processing"
    assert states[early]["last_cycle_id"] == "cy-20261015"
    assert states[late]["process_state"] == "pending"
    assert states[late]["last_cycle_id"] is None

    nxt = process_batch.process_batch(
        vault,
        index,
        "cy-20261022",
        cutoff_at="2026-10-22T08:00:00+08:00",
        at="2026-10-22T08:00:01+08:00",
    )
    assert nxt["selected_input_ids"] == [late]
    assert early not in nxt["selected_input_ids"]
    assert on_time not in nxt["selected_input_ids"]
    assert nxt["late_input_ids"] == []
    assert nxt["coverage_start"] == "2026-10-15T08:00:00+08:00"
    assert by_id(index)[late]["process_state"] == "processing"
    assert by_id(index)[late]["last_cycle_id"] == "cy-20261022"


def test_failed_carried(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    failed = "in-manual-failed00001"
    retry = "in-manual-retry000001"
    done = "in-manual-done0000001"
    busy = "in-manual-busy0000001"
    fresh = "in-manual-fresh000001"
    seed(
        index,
        [
            row(failed, received_at="2026-10-13T08:00:00+08:00", source_week="2026-W42"),
            row(retry, received_at="2026-10-10T08:00:00+08:00", source_week="2026-W41"),
            row(done, received_at="2026-10-13T09:00:00+08:00"),
            row(busy, received_at="2026-10-13T10:00:00+08:00"),
            row(fresh, received_at="2026-10-20T09:00:00+08:00", source_week="2026-W43"),
        ],
    )
    inbox_index.append_state(
        index,
        failed,
        "failed",
        at="2026-10-16T08:00:00+08:00",
        last_error="synthetic failure",
        last_cycle_id="cy-20261015",
    )
    inbox_index.append_state(
        index,
        retry,
        "retry_pending",
        at="2026-10-16T08:00:00+08:00",
        last_cycle_id="cy-20261015",
    )
    inbox_index.append_state(
        index,
        done,
        "completed",
        at="2026-10-16T08:00:00+08:00",
        last_cycle_id="cy-20261015",
    )
    inbox_index.append_state(
        index,
        busy,
        "processing",
        at="2026-10-16T08:00:00+08:00",
        last_cycle_id="cy-20261015",
    )
    batch = process_batch.process_batch(vault, index, "cy-20261022", at="2026-10-22T08:00:01+08:00")
    assert batch["selected_input_ids"] == [failed, retry, fresh]
    assert done not in batch["selected_input_ids"]
    assert busy not in batch["selected_input_ids"]
    assert batch["late_input_ids"] == []
    started = {item["input_id"]: item for item in batch[STATUS]}
    assert started[failed] == {"input_id": failed, "开始": "failed", "结束": "processing"}
    assert started[retry]["开始"] == "retry_pending"
    states = by_id(index)
    assert states[failed]["process_state"] == "processing"
    assert states[failed]["last_cycle_id"] == "cy-20261022"
    assert states[failed]["last_error"] == "synthetic failure"
    assert states[done]["process_state"] == "completed"
    assert states[busy]["process_state"] == "processing"
    assert states[busy]["last_cycle_id"] == "cy-20261015"
    assert states[fresh]["source_week"] == "2026-W43"


def test_late_process_keeps_week(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    input_id = "in-manual-w42kept001"
    kept = row(input_id, received_at="2026-10-14T10:00:00+08:00", source_week="2026-W42")
    kept["captured_at"] = "2026-10-14T09:30:00+08:00"
    seed(index, [kept])
    base_line = (index / inbox_index.INPUTS_NAME).read_bytes().splitlines()[0]
    batch = process_batch.process_batch(vault, index, "cy-20261022", at="2026-10-22T20:00:00+08:00")
    assert batch["cycle_id"] == "cy-20261022"
    assert batch["selected_input_ids"] == [input_id]
    raw = records(index)
    assert raw[0]["source_week"] == "2026-W42"
    assert (index / inbox_index.INPUTS_NAME).read_bytes().splitlines()[0] == base_line
    assert all("source_week" not in item for item in raw[1:])
    visible = by_id(index)[input_id]
    assert visible["source_week"] == "2026-W42"
    assert visible["process_state"] == "processing"
    assert visible["last_cycle_id"] == "cy-20261022"


def test_resume_does_not_duplicate_select(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    first = "in-manual-resume0001"
    second = "in-manual-resume0002"
    seed(
        index,
        [
            row(first, received_at="2026-10-14T10:00:00+08:00"),
            row(second, received_at="2026-10-14T11:00:00+08:00"),
        ],
    )
    real = process_batch.append_state
    calls = {"n": 0}

    def interrupt(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("interrupted")
        return real(*args, **kwargs)

    monkeypatch.setattr(process_batch, "append_state", interrupt)
    try:
        process_batch.process_batch(vault, index, "cy-20261015", at="2026-10-15T08:00:01+08:00")
    except RuntimeError as exc:
        assert str(exc) == "interrupted"
    else:
        raise AssertionError("expected interrupt")

    path = process_batch.batch_path(vault, "cy-20261015")
    frozen = path.read_bytes()
    stored = json.loads(frozen)
    assert stored["selected_input_ids"] == [first, second]
    assert stored[STATUS][0]["开始"] == "pending"
    assert stored[STATUS][0]["结束"] == "processing"
    assert [item["input_id"] for item in records(index) if item.get("record_type") == "state"] == [first]

    monkeypatch.setattr(process_batch, "append_state", real)
    again = process_batch.process_batch(vault, index, "cy-20261015", at="2026-10-15T09:00:00+08:00")
    assert again["selected_input_ids"] == [first, second]
    assert path.read_bytes() == frozen
    state_ids = [item["input_id"] for item in records(index) if item.get("record_type") == "state"]
    assert state_ids == [first, second]
    assert by_id(index)[first]["process_state"] == "processing"
    assert by_id(index)[second]["process_state"] == "processing"

    settled = (index / inbox_index.INPUTS_NAME).read_bytes()
    third = process_batch.process_batch(vault, index, "cy-20261015", at="2026-10-15T10:00:00+08:00")
    assert third["selected_input_ids"] == [first, second]
    assert path.read_bytes() == frozen
    assert (index / inbox_index.INPUTS_NAME).read_bytes() == settled
