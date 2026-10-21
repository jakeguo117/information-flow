#!/usr/bin/env python3
"""Synthetic cycle digests. No private notes, no git, no network."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_digest_v2  # noqa: E402
import inbox_index  # noqa: E402
import process_batch  # noqa: E402

CYCLE = "cy-20261015"
AT = "2026-10-15T20:00:00+08:00"
SOURCE_ID = "src-manual-usynth0000001"
SOURCE_URL = "https://example.com/notes/synth-manual-001"


def row(
    input_id: str,
    *,
    received_at: str,
    source_week: str | None = "2026-W42",
    process_state: str = "pending",
    topics: list[str] | None = None,
    summary_ref: str | None = "合成一句话",
    completeness: str = "full",
    origin: str = "collected",
    source_id: str = SOURCE_ID,
) -> dict:
    return {
        "schema_version": "inbox-0.1",
        "input_id": input_id,
        "source_id": source_id,
        "external_item_id": None,
        "event_type": "note",
        "captured_at": "2026-10-14T09:30:00+08:00",
        "time_basis": "platform",
        "received_at": received_at,
        "source_published_at": None,
        "source_week": source_week,
        "origin": origin,
        "content_fingerprint": "synthetic",
        "completeness": completeness,
        "missing_reason": None,
        "process_state": process_state,
        "last_error": None,
        "last_cycle_id": None,
        "topics": topics,
        "summary_ref": summary_ref,
        "process_version": None,
        "suspected_duplicate_of": None,
        "inbox_ref": f"📥 Inbox/manual/{input_id}.md#note",
    }


def source(
    source_id: str = SOURCE_ID,
    *,
    platform: str = "manual",
    url: str = SOURCE_URL,
) -> dict:
    return {
        "schema_version": "inbox-0.1",
        "source_id": source_id,
        "platform": platform,
        "canonical_url": url,
    }


def seed(index: Path, rows: list[dict], sources: list[dict] | None = None) -> None:
    index.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows)
    (index / inbox_index.INPUTS_NAME).write_text(text, encoding="utf-8")
    payload = sources if sources is not None else [source()]
    blob = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in payload)
    (index / inbox_index.SOURCES_NAME).write_text(blob, encoding="utf-8")


def section(text: str, title: str) -> str:
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, title
    return match.group(1)


def test_counts_reconcile(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    done = [f"in-manual-done000000{n}" for n in (1, 2, 3)]
    failed = "in-manual-fail0000001"
    pending = "in-manual-pend0000001"
    ids = done + [failed, pending]
    seed(
        index,
        [
            row(done[0], received_at="2026-10-14T10:00:00+08:00", summary_ref="合成摘要一"),
            row(done[1], received_at="2026-10-14T11:00:00+08:00", summary_ref="合成摘要二"),
            row(done[2], received_at="2026-10-14T12:00:00+08:00", summary_ref="合成摘要三"),
            row(failed, received_at="2026-10-14T13:00:00+08:00", summary_ref="合成失败"),
            row(pending, received_at="2026-10-14T14:00:00+08:00", summary_ref="合成待处理"),
        ],
    )
    batch = process_batch.process_batch(vault, index, CYCLE, at="2026-10-15T08:00:01+08:00")
    assert batch["selected_input_ids"] == ids
    batch_bytes = process_batch.batch_path(vault, CYCLE).read_bytes()
    for input_id in done:
        inbox_index.append_state(index, input_id, "completed", at="2026-10-15T18:00:00+08:00")
    inbox_index.append_state(
        index,
        failed,
        "failed",
        at="2026-10-15T18:00:00+08:00",
        last_error="synthetic failure",
    )
    inbox_index.append_state(index, pending, "pending", at="2026-10-15T18:00:00+08:00")
    index_bytes = (index / inbox_index.INPUTS_NAME).read_bytes()

    digest = build_digest_v2.build_digest(vault, index, CYCLE, at=AT)
    text = Path(digest["path"]).read_text(encoding="utf-8")
    counts = digest["counts"]
    state_sum = sum(counts[state] for state in inbox_index.PROCESS_STATES)
    assert digest["input_ids"] == ids
    assert counts["completed"] == 3
    assert counts["failed"] == 1
    assert counts["pending"] == 1
    assert counts["processing"] == 0
    assert counts["retry_pending"] == 0
    assert state_sum == counts["total"] == len(digest["input_ids"]) == 5
    assert digest["schema_version"] == "digest-2.0"
    assert digest["type"] == "cycle-digest"
    assert digest["digest_id"] == f"dg-{CYCLE}"
    assert digest["snapshot_revision"] == 1
    assert digest["source_weeks"] == {"2026-W42": 5}
    assert digest["late_or_cross_week"] == []
    untagged = section(text, "待归类")
    for number, input_id in enumerate(ids, start=1):
        d_id = f"D-{CYCLE}-{number:02d}"
        assert d_id in untagged
        assert input_id in text.split("---", 2)[1]
    failed_section = section(text, "失败和不完整")
    assert f"D-{CYCLE}-04" in failed_section
    assert "failed" in failed_section
    assert f"D-{CYCLE}-01" not in failed_section
    assert "completed" not in failed_section
    zeros = section(text, "本批来源统计（哪个来源是 0）")
    assert "youtube: 0" in zeros
    assert "manual: 5" in zeros
    assert process_batch.batch_path(vault, CYCLE).read_bytes() == batch_bytes
    assert (index / inbox_index.INPUTS_NAME).read_bytes() == index_bytes


def test_new_revision_keeps_r1(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    input_id = "in-manual-rev0000001"
    seed(index, [row(input_id, received_at="2026-10-14T10:00:00+08:00")])
    process_batch.process_batch(vault, index, CYCLE, at="2026-10-15T08:00:01+08:00")

    first = build_digest_v2.build_digest(vault, index, CYCLE, at=AT)
    r1 = Path(first["path"])
    frozen = r1.read_bytes()
    assert r1.name == "r1.md"
    assert first["snapshot_revision"] == 1
    assert first["written"] is True
    assert f"D-{CYCLE}-01" in frozen.decode("utf-8")

    again = build_digest_v2.build_digest(vault, index, CYCLE, at="2026-10-15T21:00:00+08:00")
    assert again["written"] is False
    assert again["snapshot_revision"] == 1
    assert again["path"] == str(r1)
    assert r1.read_bytes() == frozen
    assert list(r1.parent.glob("r*.md")) == [r1]

    inbox_index.append_state(index, input_id, "completed", at="2026-10-15T22:00:00+08:00")
    second = build_digest_v2.build_digest(vault, index, CYCLE, at="2026-10-15T22:30:00+08:00")
    r2 = Path(second["path"])
    assert second["written"] is True
    assert second["snapshot_revision"] == 2
    assert r2.name == "r2.md"
    assert r1.read_bytes() == frozen
    assert r2.read_bytes() != frozen
    r1_text = frozen.decode("utf-8")
    r2_text = r2.read_text(encoding="utf-8")
    assert f"D-{CYCLE}-01｜合成一句话｜`{SOURCE_URL}`｜processing｜否" in r1_text
    assert f"D-{CYCLE}-01｜合成一句话｜`{SOURCE_URL}`｜completed｜否" in r2_text
    assert "snapshot_revision: 1" in r1_text
    assert "snapshot_revision: 2" in r2_text
    assert second["counts"]["completed"] == 1
    assert first["counts"]["processing"] == 1


def test_untagged_items_under_daigui(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    themed = "in-manual-theme000001"
    bare = "in-manual-bare0000001"
    empty_topics = "in-manual-empty000001"
    note = vault / "📥 Inbox" / "manual" / "bare.md"
    note.parent.mkdir(parents=True)
    note.write_text("---\ntitle: skip\n---\n# 标题\n合成划线\n", encoding="utf-8")
    seed(
        index,
        [
            row(
                themed,
                received_at="2026-10-14T10:00:00+08:00",
                topics=["合成主题"],
                summary_ref="合成一句话",
            ),
            row(
                bare,
                received_at="2026-10-14T11:00:00+08:00",
                topics=None,
                summary_ref="📥 Inbox/manual/bare.md#note",
                completeness="excerpt",
            ),
            row(
                empty_topics,
                received_at="2026-10-14T12:00:00+08:00",
                topics=[],
                summary_ref="没有主题",
            ),
        ],
    )
    process_batch.process_batch(vault, index, CYCLE, at="2026-10-15T08:00:01+08:00")
    digest = build_digest_v2.build_digest(vault, index, CYCLE, at=AT)
    text = Path(digest["path"]).read_text(encoding="utf-8")
    themed_section = section(text, "合成主题")
    untagged = section(text, "待归类")
    assert f"D-{CYCLE}-01" in themed_section
    assert "合成一句话" in themed_section
    assert f"D-{CYCLE}-01" not in untagged
    assert f"D-{CYCLE}-02" in untagged
    assert "合成划线" in untagged
    assert f"D-{CYCLE}-03" in untagged
    assert "没有主题" in untagged
    failed = section(text, "失败和不完整")
    assert f"D-{CYCLE}-02" in failed
    assert f"D-{CYCLE}-01" not in failed
    assert f"D-{CYCLE}-03" not in failed


def test_cross_week_history_and_zero_sources(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    index = tmp_path / "_index"
    current = "in-youtube-current0001"
    older = "in-weread-older000001"
    late = "in-x-late000000001"
    youtube = "src-youtube-exmplvid01"
    weread = "src-weread-synthbook001"
    x_source = "src-x-exmplstatus01"
    youtube_url = "https://example.com/watch?v=exmplvid01"
    weread_url = "https://example.com/weread/book/synthbook001"
    seed(
        index,
        [
            row(
                current,
                received_at="2026-10-14T10:00:00+08:00",
                source_week="2026-W42",
                source_id=youtube,
                summary_ref="合成一句话",
            ),
            row(
                older,
                received_at="2026-10-01T10:00:00+08:00",
                source_week="2026-W40",
                source_id=weread,
                origin="historical_import",
                summary_ref="合成旧材料",
            ),
            row(
                late,
                received_at="2026-10-15T08:05:00+08:00",
                source_week="2026-W42",
                source_id=x_source,
                summary_ref="合成迟到",
            ),
        ],
        [
            source(youtube, platform="youtube", url=youtube_url),
            source(weread, platform="weread", url=weread_url),
            source(x_source, platform="x", url="https://example.com/x/status/1000000000000000001"),
        ],
    )
    batch = process_batch.process_batch(vault, index, CYCLE, at="2026-10-15T08:00:01+08:00")
    assert batch["selected_input_ids"] == [current, older]
    assert batch["late_input_ids"] == [late]
    digest = build_digest_v2.build_digest(vault, index, CYCLE, at=AT)
    text = Path(digest["path"]).read_text(encoding="utf-8")
    assert digest["input_ids"] == [current, older]
    assert late not in digest["input_ids"]
    assert digest["late_or_cross_week"] == [older]
    assert digest["source_weeks"] == {"2026-W40": 1, "2026-W42": 1}
    untagged = section(text, "待归类")
    assert f"D-{CYCLE}-01｜合成一句话｜`{youtube_url}`｜processing｜否" in untagged
    assert f"D-{CYCLE}-02｜合成旧材料｜`{weread_url}`｜processing｜是" in untagged
    assert late not in text
    history = section(text, "历史关联（只放链接）")
    assert weread_url in history
    assert "D-" not in history
    assert "合成旧材料" not in history
    zeros = section(text, "本批来源统计（哪个来源是 0）")
    assert "youtube: 1" in zeros
    assert "weread: 1" in zeros
    assert "snipd: 0" in zeros
    assert "x: 0" in zeros
    assert "instagram: 0" in zeros
    assert "thought: 0" in zeros
