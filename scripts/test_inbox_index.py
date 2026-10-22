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


README_PATH = "📥 Inbox/Snipd/README.md"
README_TEXT = """# Snipd

合成说明：这是插件指南，不是一条笔记。
"""
THOUGHT_BAD_PATH = "📝 Journal/想法/2026-W42/thought-20261014-1749.md"
THOUGHT_BAD = """---
id: thought-20261014-1749
type: thought
title: 虚构想法：缺少原话标记
---

合成正文，没有原话标记。
"""
DIGEST_PATH = "📝 Journal/想法/digests/digest-journal-20261011-101900-jake.md"
DIGEST_TEXT = """---
type: digest
title: 虚构汇总
---

合成摘要，没有想法 id。
"""
VALID_THOUGHT_PATH = "📝 Journal/想法/2026-W42/thought-20261014-1800.md"
VALID_THOUGHT = """---
id: thought-20261014-1800
type: thought
captured_at: 2026-10-14T18:00:00+08:00
---
原话:
合成原话：这条应该被索引。
"""
SNIP = "22222222-2222-4222-8222-222222222222"
EPISODE = "11111111-1111-4111-8111-111111111111"
SNIPD_PATH = "📥 Inbox/Snipd/example-show/synth-episode.md"
SNIPD = f"""---
episode_title: 虚构标题：示例播客一集
show_author: Example Host
episode_publish_date: 2026-09-01T08:00:00+08:00
episode_url: https://example.com/snipd/episodes/{EPISODE}
---

## Snips

### [00:12:03] 虚构片段
[🎧 Play snip](https://share.snipd.com/snip/{SNIP})

> 合成摘录：示例播客里的一句虚构原话。
"""
SKIPPED_PATHS = (README_PATH, THOUGHT_BAD_PATH, DIGEST_PATH)


def write_tree(vault: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def run_index(vault: Path, index: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--inbox",
            str(vault),
            "--index",
            str(index),
            "--now",
            YT_NOW,
            *extra,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_discover_skips_readme_and_digest_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_tree(
        vault,
        {
            README_PATH: README_TEXT,
            "📥 Inbox/Snipd/readme.md": "合成说明：小写文件名同样不是笔记。\n",
            "📥 Inbox/Snipd/_index/secret.md": "合成索引，不该出现。\n",
            DIGEST_PATH: DIGEST_TEXT,
            "📝 Journal/想法/digests/thought-looking.md": VALID_THOUGHT,
            SNIPD_PATH: SNIPD,
            VALID_THOUGHT_PATH: VALID_THOUGHT,
            "📝 Journal/想法/digests.md": VALID_THOUGHT,
        },
    )
    found = inbox_index.discover_notes(vault)
    notes = {item.path: item.platform for item in found.notes}
    skipped = {item["path"]: item["reason"] for item in found.skipped}
    assert notes[SNIPD_PATH] == "snipd"
    assert notes[VALID_THOUGHT_PATH] == "thought"
    assert notes["📝 Journal/想法/digests.md"] == "thought"
    assert skipped[README_PATH] == inbox_index.NOT_A_NOTE
    assert skipped["📥 Inbox/Snipd/readme.md"] == inbox_index.NOT_A_NOTE
    assert skipped[DIGEST_PATH] == inbox_index.NOT_A_NOTE
    assert skipped["📝 Journal/想法/digests/thought-looking.md"] == inbox_index.NOT_A_NOTE
    assert "📥 Inbox/Snipd/_index/secret.md" not in notes
    assert "📥 Inbox/Snipd/_index/secret.md" not in skipped
    assert all(not Path(item["path"]).is_absolute() for item in found.skipped)


def test_index_notes_skips_thought_without_verbatim(tmp_path: Path) -> None:
    index = tmp_path / "_index"
    control = tmp_path / "control"
    good = note(VALID_THOUGHT_PATH, VALID_THOUGHT, "thought")
    bad = note(THOUGHT_BAD_PATH, THOUGHT_BAD, "thought")
    result = inbox_index.index_notes([bad, good], index, now=YT_NOW)
    alone = inbox_index.index_notes([good], control, now=YT_NOW)
    assert result.skipped == [
        {"path": THOUGHT_BAD_PATH, "reason": "thought file has no 原话 marker"}
    ]
    assert result.created_input_ids == alone.created_input_ids
    assert result.sources[0]["raw_refs"] == [VALID_THOUGHT_PATH]
    assert set(result.sources[0]) == set(alone.sources[0])
    assert set(result.inputs[0]) == set(alone.inputs[0])
    blob = (index / inbox_index.SOURCES_NAME).read_text(encoding="utf-8")
    blob += (index / inbox_index.INPUTS_NAME).read_text(encoding="utf-8")
    assert THOUGHT_BAD_PATH not in blob
    assert VALID_THOUGHT_PATH in blob


def test_plain_snipd_file_without_episode_url_is_a_parse_skip(tmp_path: Path) -> None:
    loose = "📥 Inbox/Snipd/loose.md"
    result = inbox_index.index_notes(
        [
            note(loose, "# 合成\n\n不是 README，也没有 episode_url。\n", "snipd"),
            note(YT_PATH, YT, "youtube"),
        ],
        tmp_path / "_index",
        now=YT_NOW,
    )
    assert result.skipped == [{"path": loose, "reason": "snipd note has no episode_url"}]
    assert len(result.created_input_ids) == 1
    assert result.inputs[0]["inbox_ref"].startswith(YT_PATH)


def test_cli_skips_three_bad_files_and_indexes_the_rest(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    files = {
        README_PATH: README_TEXT,
        THOUGHT_BAD_PATH: THOUGHT_BAD,
        DIGEST_PATH: DIGEST_TEXT,
        SNIPD_PATH: SNIPD,
        VALID_THOUGHT_PATH: VALID_THOUGHT,
        YT_PATH: YT,
    }
    write_tree(vault, files)
    index = tmp_path / "_index"
    received = tmp_path / "map.json"
    received.write_text("{}\n", encoding="utf-8")
    dry = run_index(vault, index, "--received-at-map", str(received), "--dry-run")
    assert dry.returncode == 0, dry.stderr
    payload = json.loads(dry.stdout)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    reasons = {item["path"]: item["reason"] for item in payload["skipped"]}
    assert reasons[README_PATH] == inbox_index.NOT_A_NOTE
    assert reasons[THOUGHT_BAD_PATH] == "thought file has no 原话 marker"
    assert reasons[DIGEST_PATH] == inbox_index.NOT_A_NOTE
    assert payload["skipped_count"] == 3
    assert len(payload["skipped"]) == 3
    assert len(payload["created_input_ids"]) == 3
    assert payload["source_count"] == 3
    assert not index.exists()
    for item in payload["skipped"]:
        assert not Path(item["path"]).is_absolute()
        assert str(vault) not in item["path"]

    real = run_index(vault, index, "--received-at-map", str(received))
    assert real.returncode == 0, real.stderr
    written = json.loads(real.stdout)
    assert written["skipped_count"] == 3
    blob = (index / inbox_index.SOURCES_NAME).read_text(encoding="utf-8")
    blob += (index / inbox_index.INPUTS_NAME).read_text(encoding="utf-8")
    for bad in SKIPPED_PATHS:
        assert bad not in blob
    for good in (SNIPD_PATH, VALID_THOUGHT_PATH, YT_PATH):
        assert good in blob
    control = inbox_index.index_notes([note(YT_PATH, YT, "youtube")], tmp_path / "control", now=YT_NOW)
    stored_sources = lines(index / inbox_index.SOURCES_NAME)
    stored_inputs = lines(index / inbox_index.INPUTS_NAME)
    youtube = next(item for item in stored_sources if item["platform"] == "youtube")
    youtube_input = next(item for item in stored_inputs if str(item["inbox_ref"]).startswith(YT_PATH))
    assert set(youtube) == set(control.sources[0])
    assert set(youtube_input) == set(control.inputs[0])

    again = run_index(vault, index, "--dry-run")
    assert again.returncode == 0, again.stderr
    second = json.loads(again.stdout)
    assert second["created_input_ids"] == []
    assert second["created_source_ids"] == []
    assert {item["path"] for item in second["skipped"]} == set(SKIPPED_PATHS)
    assert second["skipped_count"] == 3


def test_only_skipped_files_exit_zero(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_tree(
        vault,
        {
            README_PATH: README_TEXT,
            THOUGHT_BAD_PATH: THOUGHT_BAD,
            DIGEST_PATH: DIGEST_TEXT,
        },
    )
    proc = run_index(vault, tmp_path / "_index", "--dry-run")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["created_input_ids"] == []
    assert payload["created_source_ids"] == []
    assert payload["skipped_count"] == 3
    assert {item["path"] for item in payload["skipped"]} == set(SKIPPED_PATHS)


def test_bad_received_at_map_still_aborts(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    write_tree(vault, {SNIPD_PATH: SNIPD, YT_PATH: YT})
    index = tmp_path / "_index"
    bad_value = tmp_path / "bad-value.json"
    bad_value.write_text(json.dumps({SNIP: 1}), encoding="utf-8")
    looked_up = run_index(vault, index, "--received-at-map", str(bad_value), "--dry-run")
    assert looked_up.returncode == 1, looked_up.stdout
    payload = json.loads(looked_up.stdout)
    assert payload == {"ok": False, "error": "received-at map values must be timestamps"}
    assert not index.exists()

    bad_shape = tmp_path / "bad-shape.json"
    bad_shape.write_text("[]\n", encoding="utf-8")
    shaped = run_index(vault, index, "--received-at-map", str(bad_shape))
    assert shaped.returncode == 1
    assert json.loads(shaped.stdout) == {"ok": False, "error": "received-at map must be a JSON object"}
    assert not index.exists()


YT_BAD_DATE_PATH = "📥 Inbox/YouTube-Likes/2026-10-20-badclock01.md"
YT_BAD_DATE = """---
video_id: badclock01
title: 虚构标题：日期写坏了
like_at: 2026-13-45T09:30:00+08:00
source_url: https://example.com/watch?v=badclock01
---
"""
WEREAD_BAD_CLOCK_PATH = "📥 Inbox/WeRead/synthbook002.md"
WEREAD_BAD_CLOCK = (
    WEREAD_FRONT.replace("synthbook001", "synthbook002")
    + """> 📌 [合成划线：时间戳写坏了。](weread://highlight)
> ⏱ 2026-02-30 21:05:00
^synthbook002-1-10-20
"""
)


def test_bad_date_inside_one_note_is_a_parse_skip(tmp_path: Path) -> None:
    """T44a: a bad clock written in one note skips that note, not the run."""
    vault = tmp_path / "vault"
    write_tree(
        vault,
        {
            YT_BAD_DATE_PATH: YT_BAD_DATE,
            WEREAD_BAD_CLOCK_PATH: WEREAD_BAD_CLOCK,
            YT_PATH: YT,
            SNIPD_PATH: SNIPD,
        },
    )
    index = tmp_path / "_index"
    proc = run_index(vault, index)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    reasons = {item["path"]: item["reason"] for item in payload["skipped"]}
    assert set(reasons) == {YT_BAD_DATE_PATH, WEREAD_BAD_CLOCK_PATH}
    assert all(reason.startswith("bad date in note") for reason in reasons.values())
    assert payload["skipped_count"] == 2
    assert len(payload["created_input_ids"]) == 2
    blob = (index / inbox_index.INPUTS_NAME).read_text(encoding="utf-8")
    assert YT_PATH in blob and SNIPD_PATH in blob
    assert YT_BAD_DATE_PATH not in blob and WEREAD_BAD_CLOCK_PATH not in blob


def test_bad_received_at_value_still_aborts(tmp_path: Path) -> None:
    """Context clocks are not note content: a malformed map timestamp still fails the run."""
    vault = tmp_path / "vault"
    write_tree(vault, {SNIPD_PATH: SNIPD, YT_PATH: YT})
    bad = tmp_path / "bad-clock.json"
    bad.write_text(json.dumps({SNIP: "2026-13-45T09:00:00+08:00"}), encoding="utf-8")
    proc = run_index(vault, tmp_path / "_index", "--received-at-map", str(bad), "--dry-run")
    assert proc.returncode == 1, proc.stdout
    assert json.loads(proc.stdout)["ok"] is False


def test_digests_rule_only_hits_thought_digest_folder(tmp_path: Path) -> None:
    """Only 📝 Journal/想法/digests/<file> is not_a_note. Other digests folders are notes."""
    vault = tmp_path / "vault"
    x_in_digests = "📥 Inbox/X-Bookmarks/digests/2026-10-20-example-user.md"
    nested_thought = "📝 Journal/想法/2026-W43/digests/thought-20261020-0900.md"
    write_tree(
        vault,
        {
            DIGEST_PATH: DIGEST_TEXT,
            x_in_digests: X_NOTE,
            nested_thought: VALID_THOUGHT.replace("thought-20261014-1800", "thought-20261020-0900"),
        },
    )
    found = inbox_index.discover_notes(vault)
    notes = {item.path: item.platform for item in found.notes}
    skipped = {item["path"]: item["reason"] for item in found.skipped}
    assert skipped == {DIGEST_PATH: inbox_index.NOT_A_NOTE}
    assert notes[x_in_digests] == "x"
    assert notes[nested_thought] == "thought"


X_REPEAT_W43_PATH = "📥 Inbox/X-Bookmarks/2026-10-22-example-user.md"


def test_ac03_cross_week_repeat_via_cli_with_skips(tmp_path: Path) -> None:
    """AC03 through the CLI: W42 post shows up again in W43 next to a skipped file."""
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    write_tree(vault, {X_PATH: X_NOTE, README_PATH: README_TEXT})
    first = run_index(vault, index, "--now", W42)
    assert first.returncode == 0, first.stdout
    one = json.loads(first.stdout)
    assert len(one["created_input_ids"]) == 1
    input_id = one["created_input_ids"][0]
    before = snapshot(index)

    write_tree(vault, {X_REPEAT_W43_PATH: X_NOTE})
    second = run_index(vault, index, "--now", W43)
    assert second.returncode == 0, second.stdout
    two = json.loads(second.stdout)
    assert two["created_input_ids"] == []
    assert two["created_source_ids"] == []
    assert input_id in two["existing_input_ids"]
    assert [item["path"] for item in two["skipped"]] == [README_PATH]
    assert snapshot(index) == before
    stored = lines(index / inbox_index.INPUTS_NAME)
    assert len(stored) == 1
    assert stored[0]["source_week"] == "2026-W42"
    assert inbox_index.inputs_for_week(stored, "2026-W43") == []


def test_ac03_same_run_cross_week_repeat(tmp_path: Path) -> None:
    """AC03 on a first build: the W42 file and its W43 repeat are indexed in one run."""
    index = tmp_path / "_index"
    result = inbox_index.index_notes(
        [note(X_PATH, X_NOTE, "x"), note(X_REPEAT_W43_PATH, X_NOTE, "x")],
        index,
        now=W43,
    )
    assert len(result.created_input_ids) == 1
    assert result.existing_input_ids == result.created_input_ids
    stored = lines(index / inbox_index.INPUTS_NAME)
    assert len(stored) == 1
    assert stored[0]["inbox_ref"].startswith(X_PATH)


# T44b. Invented episode and snip ids only. Same episode_url, renamed title.
T44B_EPISODE = "c44b1001-1111-4111-8111-111111111101"
T44B_SNIP_KEPT = "c44b1002-2222-4222-8222-222222222202"
T44B_SNIP_NEW = "c44b1003-3333-4333-8333-333333333303"
T44B_SNIP_SKIPPED = "c44b1004-4444-4444-8444-444444444404"
T44B_TITLE_KEPT = "虚构标题：先登记的一集"
T44B_TITLE_SEEN = "虚构标题：播客后来改的名字"
T44B_PUBLISHED = "2026-09-01T08:00:00+08:00"
T44B_PUBLISHED_OTHER = "2026-10-02T08:00:00+08:00"
T44B_PATH_FIRST = "📥 Inbox/Snipd/example-show/a-first.md"
T44B_PATH_SECOND = "📥 Inbox/Snipd/example-show/b-renamed.md"


def t44b_snipd(title: str, snips: list[tuple[str, str]], published: str = T44B_PUBLISHED) -> str:
    sections = []
    for snip_id, quote in snips:
        sections.append(
            f"### [00:12:03] 虚构片段\n"
            f"[🎧 Play snip](https://share.snipd.com/snip/{snip_id})\n"
            f"\n"
            f"> {quote}\n"
        )
    return (
        "---\n"
        f"episode_title: {title}\n"
        "show_author: Example Host\n"
        f"episode_publish_date: {published}\n"
        f"episode_url: https://example.com/snipd/episodes/{T44B_EPISODE}\n"
        "---\n"
        "\n"
        "## Snips\n"
        "\n" + "\n".join(sections)
    )


def test_t44b_keeps_existing_title_and_appends_new_snips(tmp_path: Path) -> None:
    """Indexed Source keeps its title. A renamed export appends new snips and reports the conflict."""
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    original = t44b_snipd(T44B_TITLE_KEPT, [(T44B_SNIP_KEPT, "合成摘录：原文件里的一句虚构原话。")])
    renamed = t44b_snipd(
        T44B_TITLE_SEEN,
        [(T44B_SNIP_NEW, "合成摘录：改名文件里新出现的一句虚构原话。")],
    )
    write_tree(vault, {T44B_PATH_FIRST: original})
    first = run_index(vault, index)
    assert first.returncode == 0, first.stdout
    sources_bytes = (index / inbox_index.SOURCES_NAME).read_bytes()
    stored_source = lines(index / inbox_index.SOURCES_NAME)[0]
    assert stored_source["title"] == T44B_TITLE_KEPT
    assert stored_source["source_id"] == f"src-snipd-{T44B_EPISODE}"

    write_tree(vault, {T44B_PATH_SECOND: renamed})
    second = run_index(vault, index)
    assert second.returncode == 0, second.stdout
    payload = json.loads(second.stdout)
    assert payload["ok"] is True
    assert payload["skipped_count"] == 0
    assert payload["conflict_count"] == 1
    assert payload["conflicts"] == [
        {
            "path": T44B_PATH_SECOND,
            "source_id": stored_source["source_id"],
            "rule": "kept_existing_title",
            "fields": [{"field": "title", "kept": T44B_TITLE_KEPT, "seen": T44B_TITLE_SEEN}],
        }
    ]
    assert (index / inbox_index.SOURCES_NAME).read_bytes() == sources_bytes
    stored_inputs = lines(index / inbox_index.INPUTS_NAME)
    assert {item["external_item_id"] for item in stored_inputs} == {T44B_SNIP_KEPT, T44B_SNIP_NEW}
    created = next(item for item in stored_inputs if item["external_item_id"] == T44B_SNIP_NEW)
    assert created["input_id"] in payload["created_input_ids"]
    before = snapshot(index)

    again = run_index(vault, index)
    assert again.returncode == 0, again.stdout
    repeated = json.loads(again.stdout)
    assert repeated["conflict_count"] == 1
    assert repeated["conflicts"] == payload["conflicts"]
    assert repeated["created_source_ids"] == []
    assert repeated["created_input_ids"] == []
    assert snapshot(index) == before


def test_t44b_first_path_sorted_note_registers_source(tmp_path: Path) -> None:
    """Empty index: the path-sorted first note owns the Source. The later title is a conflict."""
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    first_body = t44b_snipd(T44B_TITLE_KEPT, [(T44B_SNIP_KEPT, "合成摘录：路径排序靠前的一句虚构原话。")])
    second_body = t44b_snipd(T44B_TITLE_SEEN, [(T44B_SNIP_NEW, "合成摘录：路径排序靠后的一句虚构原话。")])
    write_tree(vault, {T44B_PATH_SECOND: second_body, T44B_PATH_FIRST: first_body})
    proc = run_index(vault, index)
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(proc.stdout)
    stored = lines(index / inbox_index.SOURCES_NAME)
    assert len(stored) == 1
    assert stored[0]["title"] == T44B_TITLE_KEPT
    assert stored[0]["source_id"] == f"src-snipd-{T44B_EPISODE}"
    assert payload["created_source_ids"] == [stored[0]["source_id"]]
    assert payload["conflict_count"] == 1
    assert payload["conflicts"] == [
        {
            "path": T44B_PATH_SECOND,
            "source_id": stored[0]["source_id"],
            "rule": "kept_existing_title",
            "fields": [{"field": "title", "kept": T44B_TITLE_KEPT, "seen": T44B_TITLE_SEEN}],
        }
    ]
    assert {item["external_item_id"] for item in lines(index / inbox_index.INPUTS_NAME)} == {
        T44B_SNIP_KEPT,
        T44B_SNIP_NEW,
    }

    control = tmp_path / "control"
    alone = tmp_path / "alone"
    write_tree(alone, {T44B_PATH_FIRST: first_body})
    control_run = run_index(alone, control)
    assert control_run.returncode == 0, control_run.stdout
    assert lines(index / inbox_index.SOURCES_NAME)[0] == lines(control / inbox_index.SOURCES_NAME)[0]


def test_t44b_hard_source_mismatch_skips_note(tmp_path: Path) -> None:
    """Title plus published_at skips the note. None of its Inputs are written. Exit 0."""
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    original = t44b_snipd(T44B_TITLE_KEPT, [(T44B_SNIP_KEPT, "合成摘录：已入库的一句虚构原话。")])
    mismatch = t44b_snipd(
        T44B_TITLE_SEEN,
        [(T44B_SNIP_SKIPPED, "合成摘录：这条不该入库的虚构原话。")],
        published=T44B_PUBLISHED_OTHER,
    )
    write_tree(vault, {T44B_PATH_FIRST: original})
    first = run_index(vault, index)
    assert first.returncode == 0, first.stdout
    before = snapshot(index)
    source_id = lines(index / inbox_index.SOURCES_NAME)[0]["source_id"]
    kept_published = lines(index / inbox_index.SOURCES_NAME)[0]["published_at"]

    write_tree(vault, {T44B_PATH_SECOND: mismatch})
    proc = run_index(vault, index)
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["created_input_ids"] == []
    assert payload["created_source_ids"] == []
    assert payload["skipped_count"] == 0
    assert payload["conflict_count"] == 1
    conflict = payload["conflicts"][0]
    assert conflict["path"] == T44B_PATH_SECOND
    assert conflict["source_id"] == source_id
    assert conflict["rule"] == "skipped_source_mismatch"
    fields = {item["field"]: item for item in conflict["fields"]}
    assert set(fields) == {"title", "published_at"}
    assert fields["title"] == {"field": "title", "kept": T44B_TITLE_KEPT, "seen": T44B_TITLE_SEEN}
    assert fields["published_at"]["kept"] == kept_published
    assert fields["published_at"]["seen"] != kept_published
    assert snapshot(index) == before
    blob = (index / inbox_index.INPUTS_NAME).read_text(encoding="utf-8")
    assert T44B_SNIP_SKIPPED not in blob
    assert T44B_PATH_SECOND not in blob


def test_t44b_dry_run_reports_conflicts_without_writing(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    write_tree(
        vault,
        {
            T44B_PATH_SECOND: t44b_snipd(
                T44B_TITLE_SEEN,
                [(T44B_SNIP_NEW, "合成摘录：试跑里后到的一句虚构原话。")],
            ),
            T44B_PATH_FIRST: t44b_snipd(
                T44B_TITLE_KEPT,
                [(T44B_SNIP_KEPT, "合成摘录：试跑里先到的一句虚构原话。")],
            ),
        },
    )
    proc = run_index(vault, index, "--dry-run")
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    assert payload["conflict_count"] == 1
    assert payload["conflicts"][0]["rule"] == "kept_existing_title"
    assert payload["conflicts"][0]["path"] == T44B_PATH_SECOND
    assert len(payload["conflicts"]) == payload["conflict_count"]
    assert payload["skipped_count"] == 0
    assert not index.exists()
    written = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*") if path.is_file())
    assert written == [T44B_PATH_FIRST, T44B_PATH_SECOND]


def test_t44b_input_diff_and_bad_index_still_exit_1(tmp_path: Path) -> None:
    """Input field changes, a bad received-at map, and bad jsonl still abort."""
    vault = tmp_path / "content"
    index = tmp_path / "content-index"
    write_tree(vault, {YT_PATH: YT})
    first = run_index(vault, index)
    assert first.returncode == 0, first.stdout
    before = snapshot(index)
    changed = YT.replace("合成摘录：示例频道用虚构情节说明一个观点。", "合成摘录：另一句虚构句子。")
    write_tree(vault, {YT_PATH: changed})
    diffed = run_index(vault, index)
    assert diffed.returncode == 1, diffed.stdout
    body = json.loads(diffed.stdout)
    assert body["ok"] is False
    assert body["error"] == "diff"
    assert any(item["field"] == "content_fingerprint" for item in body["diffs"])
    assert snapshot(index) == before

    map_vault = tmp_path / "map-vault"
    write_tree(map_vault, {SNIPD_PATH: SNIPD})
    bad_map = tmp_path / "bad-map.json"
    bad_map.write_text(json.dumps({SNIP: 1}), encoding="utf-8")
    mapped = run_index(map_vault, tmp_path / "map-index", "--received-at-map", str(bad_map))
    assert mapped.returncode == 1, mapped.stdout
    assert json.loads(mapped.stdout) == {"ok": False, "error": "received-at map values must be timestamps"}
    assert not (tmp_path / "map-index").exists()

    bare = tmp_path / "newline-vault"
    newline_index = tmp_path / "newline-index"
    write_tree(bare, {YT_PATH: YT})
    built = run_index(bare, newline_index)
    assert built.returncode == 0, built.stdout
    sources_path = newline_index / inbox_index.SOURCES_NAME
    sources_path.write_text(sources_path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
    inputs_before = (newline_index / inbox_index.INPUTS_NAME).read_bytes()
    missing_nl = run_index(bare, newline_index)
    assert missing_nl.returncode == 1, missing_nl.stdout
    assert "newline" in json.loads(missing_nl.stdout)["error"]
    assert (newline_index / inbox_index.INPUTS_NAME).read_bytes() == inputs_before

    invalid_vault = tmp_path / "invalid-vault"
    invalid_index = tmp_path / "invalid-index"
    write_tree(invalid_vault, {YT_PATH: YT})
    built = run_index(invalid_vault, invalid_index)
    assert built.returncode == 0, built.stdout
    sources_path = invalid_index / inbox_index.SOURCES_NAME
    sources_path.write_text(sources_path.read_text(encoding="utf-8") + "{not json}\n", encoding="utf-8")
    inputs_before = (invalid_index / inbox_index.INPUTS_NAME).read_bytes()
    invalid = run_index(invalid_vault, invalid_index)
    assert invalid.returncode == 1, invalid.stdout
    assert "not json" in json.loads(invalid.stdout)["error"]
    assert (invalid_index / inbox_index.INPUTS_NAME).read_bytes() == inputs_before


def test_t44b_walk_order_does_not_pick_the_source(tmp_path: Path, monkeypatch) -> None:
    """Empty index, 4 notes for one episode, 3 conflicts. Any filesystem walk order gives the same result."""
    import random

    vault = tmp_path / "vault"
    third = "📥 Inbox/Snipd/example-show/c-third.md"
    fourth = "📥 Inbox/Snipd/example-show/d-fourth.md"
    snips = [f"c44b10{i:02d}-5555-4555-8555-5555555555{i:02d}" for i in range(10, 14)]
    write_tree(
        vault,
        {
            fourth: t44b_snipd("虚构标题：第四个", [(snips[3], "合成：四")], published=T44B_PUBLISHED_OTHER),
            third: t44b_snipd("虚构标题：第三个", [(snips[2], "合成：三")]),
            T44B_PATH_SECOND: t44b_snipd(T44B_TITLE_SEEN, [(snips[1], "合成：二")]),
            T44B_PATH_FIRST: t44b_snipd(T44B_TITLE_KEPT, [(snips[0], "合成：一")]),
        },
    )
    real_rglob = Path.rglob
    outcomes = set()
    for seed in ("reversed", 0, 1, 2, 3, 4, 5, 6, 7):

        def walk(self, pattern, _seed=seed):
            items = list(real_rglob(self, pattern))
            if _seed == "reversed":
                items.sort(reverse=True)
            else:
                random.Random(_seed).shuffle(items)
            return iter(items)

        monkeypatch.setattr(Path, "rglob", walk)
        found = inbox_index.discover_notes(vault)
        monkeypatch.setattr(Path, "rglob", real_rglob)
        result = inbox_index.index_notes(found.notes, tmp_path / f"idx-{seed}", now=YT_NOW, dry_run=True)
        assert [item.path for item in found.notes] == [T44B_PATH_FIRST, T44B_PATH_SECOND, third, fourth]
        assert [source["title"] for source in result.planned_sources] == [T44B_TITLE_KEPT]
        assert [(item["path"], item["rule"]) for item in result.conflicts] == [
            (T44B_PATH_SECOND, "kept_existing_title"),
            (third, "kept_existing_title"),
            (fourth, "skipped_source_mismatch"),
        ]
        assert {item["external_item_id"] for item in result.planned_inputs} == set(snips[:3])
        outcomes.add(json.dumps([result.created_input_ids, result.conflicts], ensure_ascii=False, sort_keys=True))
    assert len(outcomes) == 1
