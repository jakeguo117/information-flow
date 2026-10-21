#!/usr/bin/env python3
"""Synthetic inbox index tests. No private notes, no git, no network."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inbox_index  # noqa: E402
import inbox_lib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inbox_index.py"

YT_PATH = "📥 Inbox/YouTube-Likes/2026-10-14-exmplvid01.md"
YT = """---
video_id: exmplvid01
title: 虚构标题：示例说明
channel: Example Channel
like_at: 2026-10-14T09:30:00+08:00
source_url: https://example.com/watch?v=exmplvid01&utm_source=share
transcript: captions
---

## 摘句

- 合成摘录：示例频道用虚构情节说明一个观点。
"""
YT_NOW = "2026-10-14T10:00:00+08:00"

WEREAD_PATH = "📥 Inbox/WeRead/synthbook001.md"
WEREAD_FRONT = """---
doc_type: weread-highlights-reviews
bookId: synthbook001
title: 虚构书名：示例手册
author: 示例作者
published_at: 2020-01-01T00:00:00+08:00
source_url: https://example.com/weread/book/synthbook001?utm_campaign=share
---

## 第一章

"""
WEREAD_ONE = (
    WEREAD_FRONT
    + """> 📌 [合成划线：这是一句虚构的书中句子。](weread://highlight)
> ⏱ 2026-10-12 21:05:00
^synthbook001-1-10-20
"""
)
WEREAD_TWO = (
    WEREAD_ONE
    + """
> 📌 [合成划线：第二条虚构句子，单独成条。](weread://highlight)
> ⏱ 2026-10-13 09:00:00
^synthbook001-2-1-8
"""
)

X_PATH = "📥 Inbox/X-Bookmarks/2026-10-15-example-user.md"
X_NOTE = """# @example_user：虚构短帖：示例标题

- 原文链接：https://example.com/x/status/1000000000000000001?utm_source=x
- 作者：example_user
- 发布时间：2026-10-10 12:00（北京时间）
- 类型：帖子

## 摘要

合成帖文：这是一条虚构的短帖。
"""
W42 = "2026-10-15T08:00:00+08:00"
W43 = "2026-10-22T08:00:00+08:00"

IG_OLD_PATH = "📥 Inbox/Instagram-Saves/2021-12-01-example-author.md"
IG_OLD = """# @example_author：虚构短视频：历史导入示例

- 原文链接：https://example.com/p/EXMPLHIST01
- 作者：example_author
- 视频发布时间：2021-12-01 12:00

## 摘要

合成收藏：这是一条虚构的历史导入说明。
"""
IG_NEW_PATH = "📥 Inbox/Instagram-Saves/2026-10-01-example-author.md"
IG_NEW = """# @example_author：虚构短视频：示例说明

- 原文链接：https://example.com/p/EXMPL00001
- 作者：example_author
- 视频发布时间：2026-10-01 18:00

## 摘要

合成收藏：这是一条虚构的短视频说明。
"""
CURRENT = "2026-10-21T08:00:00+08:00"


def note(path: str, text: str, platform: str) -> inbox_index.InboxNote:
    return inbox_index.InboxNote(path, text, platform)


def lines(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def snapshot(index: Path) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    if not index.exists():
        return found
    for path in sorted(index.rglob("*")):
        if path.is_file():
            found[path.relative_to(index).as_posix()] = path.read_bytes()
    return found


def test_same_sync_twice(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    item = note(YT_PATH, YT, "youtube")
    first = inbox_index.index_notes([item], index, now=YT_NOW)
    assert first.created_source_ids
    assert len(first.created_input_ids) == 1
    input_id = first.created_input_ids[0]
    assert len(lines(index / inbox_index.SOURCES_NAME)) == 1
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 1
    before = snapshot(index)

    second = inbox_index.index_notes([item], index, now=YT_NOW)
    assert second.created_source_ids == []
    assert second.created_input_ids == []
    assert second.existing_input_ids == [input_id]
    assert second.inputs[0]["input_id"] == input_id
    assert len(second.sources) == 1
    assert len(second.inputs) == 1
    assert snapshot(index) == before


def test_new_highlight_reuses_source(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    now = "2026-10-13T08:00:00+08:00"
    first = inbox_index.index_notes([note(WEREAD_PATH, WEREAD_ONE, "weread")], index, now=now)
    assert len(first.sources) == 1
    assert len(first.inputs) == 1
    source_id = first.sources[0]["source_id"]
    kept = snapshot(index)[inbox_index.SOURCES_NAME]

    second = inbox_index.index_notes([note(WEREAD_PATH, WEREAD_TWO, "weread")], index, now=now)
    assert second.created_source_ids == []
    assert len(second.created_input_ids) == 1
    assert len(lines(index / inbox_index.SOURCES_NAME)) == 1
    assert (index / inbox_index.SOURCES_NAME).read_bytes() == kept
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 2
    assert len({item["source_id"] for item in second.inputs}) == 1
    assert second.inputs[0]["source_id"] == source_id
    added = next(item for item in second.inputs if item["input_id"] == second.created_input_ids[0])
    assert added["process_state"] == "pending"
    assert added["event_type"] == "highlight"
    assert added["external_item_id"] == "^synthbook001-2-1-8"
    assert added["input_id"] != first.inputs[0]["input_id"]


def test_cross_week_same_content(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    item = note(X_PATH, X_NOTE, "x")
    first = inbox_index.index_notes([item], index, now=W42)
    assert len(first.inputs) == 1
    input_id = first.inputs[0]["input_id"]
    assert first.inputs[0]["source_week"] == "2026-W42"
    assert [row["input_id"] for row in inbox_index.inputs_for_week(first.inputs, "2026-W42")] == [input_id]
    before = snapshot(index)

    second = inbox_index.index_notes([item], index, now=W43)
    assert second.created_input_ids == []
    assert second.existing_input_ids == [input_id]
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 1
    assert second.inputs[0]["source_week"] == "2026-W42"
    assert inbox_index.inputs_for_week(second.inputs, "2026-W43") == []
    assert snapshot(index) == before

    other_path = "📥 Inbox/X-Bookmarks/2026-10-22-example-user.md"
    third = inbox_index.index_notes([note(other_path, X_NOTE, "x")], index, now=W43)
    assert third.created_input_ids == []
    assert third.existing_input_ids == [input_id]
    assert third.inputs[0]["source_week"] == "2026-W42"
    assert third.inputs[0]["inbox_ref"].startswith(X_PATH)
    assert inbox_index.inputs_for_week(third.inputs, "2026-W43") == []
    assert snapshot(index) == before


def test_historical_no_date(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    result = inbox_index.index_notes(
        [note(IG_OLD_PATH, IG_OLD, "instagram"), note(IG_NEW_PATH, IG_NEW, "instagram")],
        index,
        now=CURRENT,
    )
    old = next(item for item in result.inputs if item["external_item_id"] == "EXMPLHIST01")
    current = next(item for item in result.inputs if item["external_item_id"] == "EXMPL00001")
    assert old["origin"] == "historical_import"
    assert old["time_basis"] == "unknown"
    assert old["captured_at"] is None
    assert old["source_week"] is None
    assert current["origin"] == "collected"
    assert current["time_basis"] == "first_seen"
    assert current["source_week"] == "2026-W43"
    week_ids = [item["input_id"] for item in inbox_index.inputs_for_week(result.inputs, "2026-W43")]
    assert old["input_id"] not in week_ids
    assert week_ids == [current["input_id"]]


def test_resume(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    item = note(YT_PATH, YT, "youtube")
    planned = inbox_index.index_notes([item], index, now=YT_NOW, dry_run=True)
    assert planned.planned_sources and planned.planned_inputs
    assert not index.exists()

    index.mkdir()
    (index / inbox_index.SOURCES_NAME).write_text(
        json.dumps(planned.planned_sources[0], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (index / inbox_index.INPUTS_NAME).write_text(
        json.dumps(planned.planned_inputs[0], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    before = snapshot(index)
    input_id = planned.planned_inputs[0]["input_id"]

    resumed = inbox_index.index_notes([item], index, now=YT_NOW)
    assert resumed.existing_input_ids == [input_id]
    assert resumed.created_input_ids == []
    assert resumed.created_source_ids == []
    assert snapshot(index) == before

    changed = note(
        YT_PATH,
        YT.replace("合成摘录：示例频道用虚构情节说明一个观点。", "合成摘录：另一句虚构句子。"),
        "youtube",
    )
    try:
        inbox_index.index_notes([changed], index, now=YT_NOW)
    except inbox_index.IndexConflict as exc:
        assert exc.diffs
        assert any(item.field == "content_fingerprint" for item in exc.diffs)
        assert "differs" in str(exc)
    else:
        raise AssertionError("expected a diff")
    assert snapshot(index) == before
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 1


def test_dry_run_writes_no_files(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    note_path = vault / YT_PATH
    note_path.parent.mkdir(parents=True)
    note_path.write_text(YT, encoding="utf-8")
    index = vault / "📥 Inbox" / "_index"
    note_bytes = note_path.read_bytes()

    api = inbox_index.index_notes(
        [note(YT_PATH, YT, "youtube")],
        index,
        now=YT_NOW,
        dry_run=True,
    )
    assert api.dry_run is True
    assert api.created_input_ids
    assert not index.exists()
    assert note_path.read_bytes() == note_bytes

    dry = subprocess.run(
        [sys.executable, str(SCRIPT), "--inbox", str(vault), "--index", str(index), "--now", YT_NOW, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dry.returncode == 0, dry.stderr
    payload = json.loads(dry.stdout)
    assert payload["dry_run"] is True
    assert payload["created_input_ids"]
    assert not index.exists()
    assert note_path.read_bytes() == note_bytes
    assert [path for path in vault.rglob("*") if path.is_file()] == [note_path]

    real = subprocess.run(
        [sys.executable, str(SCRIPT), "--inbox", str(vault), "--index", str(index), "--now", YT_NOW],
        check=False,
        capture_output=True,
        text=True,
    )
    assert real.returncode == 0, real.stderr
    assert (index / inbox_index.SOURCES_NAME).is_file()
    assert (index / inbox_index.INPUTS_NAME).is_file()
    before = snapshot(index)
    again = subprocess.run(
        [sys.executable, str(SCRIPT), "--inbox", str(vault), "--index", str(index), "--now", YT_NOW, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert again.returncode == 0, again.stderr
    assert json.loads(again.stdout)["dry_run"] is True
    assert snapshot(index) == before
    assert note_path.read_bytes() == note_bytes


def test_received_at_lookup_wired(tmp_path: Path) -> None:
    snip = "22222222-2222-4222-8222-222222222222"
    snip_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    episode = "11111111-1111-4111-8111-111111111111"
    path = "📥 Inbox/Snipd/example-show/synth-episode.md"
    body = f"""---
episode_title: 虚构标题：示例播客一集
show_author: Example Host
episode_publish_date: 2026-09-01T08:00:00+08:00
episode_url: https://example.com/snipd/episodes/{episode}
---

## Snips

### [00:12:03] 虚构片段
[🎧 Play snip](https://share.snipd.com/snip/{snip})

> 合成摘录：示例播客里的一句虚构原话。
"""
    later_body = body + f"""
### [00:20:00] 后加的片段
[🎧 Play snip](https://share.snipd.com/snip/{snip_b})

> 合成摘录：这是后加的一句虚构原话。
"""
    git_time = "2026-09-01T01:02:03+08:00"
    now = "2026-10-18T08:15:00+08:00"
    later = "2026-10-19T09:00:00+08:00"
    calls: list[str] = []

    def lookup(item_id: str) -> str | None:
        calls.append(item_id)
        if item_id == snip:
            return git_time
        return None

    index = tmp_path / "_index"
    first = inbox_index.index_notes([note(path, body, "snipd")], index, now=now, received_at_lookup=lookup)
    assert calls == [snip]
    assert first.inputs[0]["received_at"] == git_time
    assert first.inputs[0]["captured_at"] == now
    assert first.inputs[0]["time_basis"] == "first_seen"
    assert first.sources[0]["first_seen_at"] == now

    def lookup_gone(_item_id: str) -> str | None:
        return None

    second = inbox_index.index_notes(
        [note(path, body, "snipd")],
        index,
        now=later,
        received_at_lookup=lookup_gone,
    )
    assert second.created_input_ids == []
    assert second.inputs[0]["received_at"] == git_time
    assert second.inputs[0]["captured_at"] == now
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 1

    third = inbox_index.index_notes(
        [note(path, later_body, "snipd")],
        index,
        now=later,
        received_at_lookup=lookup_gone,
    )
    assert len(lines(index / inbox_index.SOURCES_NAME)) == 1
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 2
    by_id = {item["external_item_id"]: item for item in third.inputs}
    assert by_id[snip]["received_at"] == git_time
    assert by_id[snip]["captured_at"] == now
    assert by_id[snip_b]["received_at"] == later
    assert by_id[snip_b]["captured_at"] == later
    assert by_id[snip_b]["captured_at"] != third.sources[0]["first_seen_at"]
    assert third.sources[0]["first_seen_at"] == now


def test_lookalike_keeps_both(tmp_path: Path) -> None:
    other = YT.replace("exmplvid01", "exmplvid02").replace(
        "2026-10-14T09:30:00+08:00",
        "2026-10-14T11:00:00+08:00",
    )
    index = tmp_path / "_index"
    result = inbox_index.index_notes(
        [
            note(YT_PATH, YT, "youtube"),
            note("📥 Inbox/YouTube-Likes/2026-10-14-exmplvid02.md", other, "youtube"),
        ],
        index,
        now=YT_NOW,
    )
    assert len(result.sources) == 2
    assert len(result.inputs) == 2
    first, second = result.inputs
    assert second["suspected_duplicate_of"] == first["input_id"]
    assert first["suspected_duplicate_of"] is None
    assert second["input_id"] != first["input_id"]
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 2


def test_state_event_latest_wins(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    indexed = inbox_index.index_notes([note(YT_PATH, YT, "youtube")], index, now=YT_NOW)
    input_id = indexed.inputs[0]["input_id"]
    before = (index / inbox_index.INPUTS_NAME).read_bytes()

    dry = inbox_index.append_state(
        index,
        input_id,
        "completed",
        at="2026-10-16T08:00:00+08:00",
        dry_run=True,
    )
    assert dry["would_write"] is True
    assert dry["written"] is False
    assert (index / inbox_index.INPUTS_NAME).read_bytes() == before

    wrote = inbox_index.append_state(index, input_id, "completed", at="2026-10-16T08:00:00+08:00")
    assert wrote["written"] is True
    raw = lines(index / inbox_index.INPUTS_NAME)
    assert raw[0]["process_state"] == "pending"
    assert "record_type" not in raw[0]
    assert raw[1]["record_type"] == "state"
    assert raw[1]["process_state"] == "completed"
    _sources, effective = inbox_index.read_index(index)
    assert effective[0]["process_state"] == "completed"
    assert effective[0]["input_id"] == input_id

    again = inbox_index.append_state(index, input_id, "completed", at="2026-10-16T09:00:00+08:00")
    assert again["written"] is False
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 2

    failed = inbox_index.append_state(
        index,
        input_id,
        "failed",
        at="2026-10-16T10:00:00+08:00",
        last_error="synthetic failure",
    )
    assert failed["written"] is True
    _sources, effective = inbox_index.read_index(index)
    assert effective[0]["process_state"] == "failed"
    assert effective[0]["last_error"] == "synthetic failure"
    assert lines(index / inbox_index.INPUTS_NAME)[0]["process_state"] == "pending"
    assert len(lines(index / inbox_index.INPUTS_NAME)) == 3


def test_index_does_not_invoke_git() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "Popen" not in source
    lib = Path(inbox_lib.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in lib
