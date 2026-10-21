#!/usr/bin/env python3
"""Synthetic inbox-0.1 parser tests. No private notes, no git, no network."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inbox_lib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "skills" / "intake" / "references" / "inbox-schema.md"

MANUAL_TEXT = "合成笔记：这是一条虚构的手工记录。"
MANUAL_URL = "https://example.com/notes/synth-manual-001"
MANUAL_EVENT = "41f8ff5e18a1d296058161f6a6655a562319cea2dca6001c33a53fad21307872"
MANUAL_FINGERPRINT = "d06273963ddfaaf7ab116fef416571570870eefa0afe805ad501e18a82006769"


def ctx(path: str, **kwargs) -> inbox_lib.ParseContext:
    return inbox_lib.ParseContext(path=path, **kwargs)


def test_manual_ids_match_schema_vectors() -> None:
    assert inbox_lib.normalize_content("  a\u3000\nb\t ") == "a b"
    assert inbox_lib.normalize_content("AbC，") == "AbC，"
    assert inbox_lib.content_fingerprint(MANUAL_TEXT) == MANUAL_FINGERPRINT
    event = inbox_lib.event_key_for("manual", "note", MANUAL_TEXT, None)
    assert event == MANUAL_EVENT
    assert event != MANUAL_FINGERPRINT
    source_id = inbox_lib.source_id_for("manual", None, MANUAL_URL)
    assert source_id == "src-manual-u888511f02cc3"
    assert inbox_lib.input_id_for("manual", source_id, event) == "in-manual-25610e98807b"
    kept = inbox_lib.event_key_for("manual", "note", MANUAL_TEXT, "item-1")
    assert kept == "item-1"


def test_canonicalize_url_strips_tracking_and_keeps_v() -> None:
    url = "https://www.youtube.com/watch?utm_source=share&v=exmplvid01&utm_medium=ios&si=TRACK"
    assert inbox_lib.canonicalize_url(url) == "https://www.youtube.com/watch?v=exmplvid01"
    plain = "https://example.com/watch?v=exmplvid01"
    assert inbox_lib.canonicalize_url(plain + "&fbclid=abc") == plain
    assert inbox_lib.canonicalize_url("weread://highlight") == "weread://highlight"


def test_parser_does_not_invoke_git() -> None:
    source = Path(inbox_lib.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "Popen" not in source


def test_schema_n2_n3_wording() -> None:
    text = SCHEMA.read_text(encoding="utf-8")
    assert "指纹（即 event_key；疑似重复用 content_fingerprint）" in text
    section = text.split("### 指纹", 1)[1].split("```text", 1)[0]
    assert section.strip().startswith("PM 10-20 定：规范化：")
    assert "PM 10-20 定：`event_key`" not in section


def test_youtube_schema_sample_and_second_note() -> None:
    path = "📥 Inbox/YouTube-Likes/2026-10-14-exmplvid01.md"
    note = """---
date: 2026-10-14
type: youtube-like
video_id: exmplvid01
title: 虚构标题：示例说明
channel: Example Channel
like_at: 2026-10-14T09:30:00+08:00
source_url: https://example.com/watch?v=exmplvid01&utm_source=share&utm_medium=ios
published_at: 2026-10-01T12:00:00+08:00
transcript: captions
generator: journal-youtube-likes
---

# 虚构标题：示例说明

## 摘句

- 合成摘录：示例频道用虚构情节说明一个观点。
"""
    parsed = inbox_lib.parse_note(
        note,
        "youtube",
        ctx(path, first_seen_at="2026-10-14T10:00:00+08:00", received_at="2026-10-14T10:00:00+08:00"),
    )
    assert parsed["source"]["source_id"] == "src-youtube-exmplvid01"
    assert parsed["source"]["canonical_url"] == "https://example.com/watch?v=exmplvid01"
    assert parsed["source"]["first_seen_at"] == "2026-10-14T10:00:00+08:00"
    assert len(parsed["inputs"]) == 1
    item = parsed["inputs"][0]
    assert item["input_id"] == "in-youtube-47bf2f2062fa"
    assert item["external_item_id"] == "exmplvid01@2026-10-14T01:30:00Z"
    assert item["event_type"] == "like"
    assert item["captured_at"] == "2026-10-14T09:30:00+08:00"
    assert item["time_basis"] == "platform"
    assert item["received_at"] == "2026-10-14T10:00:00+08:00"
    assert item["source_week"] == "2026-W42"
    assert item["content_fingerprint"] == "3941d306060eb0f4160e6bc95d62d2e44496b32cd678be59ae92dd99f03fe86c"
    assert item["completeness"] == "full"
    assert item["missing_reason"] is None
    assert item["process_state"] == "pending"
    assert item["inbox_ref"] == path + "#摘句"
    assert item["topics"] is None

    empty = """---
video_id: exmplvid02
title: 虚构标题：没有字幕
channel: Example Channel Two
like_at: 2026-10-02T08:00:00+08:00
source_url: https://www.youtube.com/watch?v=exmplvid02&utm_source=share&si=TRACK
transcript: none
generator: journal-youtube-likes
---

## 摘句

- （无字幕、听写也没产出句子）
"""
    second = inbox_lib.parse_youtube(
        empty,
        ctx("📥 Inbox/YouTube-Likes/2026-10-02-exmplvid02.md", first_seen_at="2026-10-02T09:00:00+08:00"),
    )
    assert second["source"]["canonical_url"] == "https://www.youtube.com/watch?v=exmplvid02"
    assert second["source"]["external_content_id"] == "exmplvid02"
    only = second["inputs"][0]
    assert only["time_basis"] == "platform"
    assert only["external_item_id"] == "exmplvid02@2026-10-02T00:00:00Z"
    assert only["completeness"] == "metadata_only"
    assert only["missing_reason"] == "transcript: none"
    assert only["content_fingerprint"] == inbox_lib.content_fingerprint("")


def test_snipd_schema_sample_and_multi_snip_n1() -> None:
    path = "📥 Inbox/Snipd/example-show/synth-episode.md"
    note = """---
episode_title: 虚构标题：示例播客一集
show_title: Example Show
show_author: Example Host
episode_publish_date: 2026-09-01T08:00:00+08:00
last_snip_date: 2026-08-29
episode_url: https://example.com/snipd/episodes/11111111-1111-4111-8111-111111111111?utm_source=share
snips_count: 1
from_snipd: true
---

## Snips

### [00:12:03] 虚构片段
[🎧 Play snip](https://share.snipd.com/snip/22222222-2222-4222-8222-222222222222)

> 合成摘录：示例播客里的一句虚构原话。
"""
    seen = "2026-10-18T08:15:00+08:00"
    parsed = inbox_lib.parse_snipd(note, ctx(path, first_seen_at=seen, received_at=seen))
    assert parsed["source"]["source_id"] == "src-snipd-11111111-1111-4111-8111-111111111111"
    assert parsed["source"]["canonical_url"].endswith("11111111-1111-4111-8111-111111111111")
    assert "utm_source" not in parsed["source"]["canonical_url"]
    assert len(parsed["inputs"]) == 1
    item = parsed["inputs"][0]
    assert item["input_id"] == "in-snipd-6875f3fc2eff"
    assert item["external_item_id"] == "22222222-2222-4222-8222-222222222222"
    assert item["time_basis"] == "first_seen"
    assert item["captured_at"] == seen
    assert item["received_at"] == seen
    assert item["captured_at"] != "2026-08-29T00:00:00+08:00"
    assert item["content_fingerprint"] == "7418d4c958935036356c13ff5569e8c424e976b4cfdb424b92059a6f2e5a964c"
    assert item["inbox_ref"] == path + "#22222222-2222-4222-8222-222222222222"

    snip_a = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    snip_b = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    snip_c = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    git_a = "2026-10-01T01:00:00+08:00"
    index_a = "2026-10-18T09:00:00+08:00"
    index_b = "2026-10-19T09:30:00+08:00"
    own_c = "2026-10-19T11:00:00+08:00"
    source_seen = "2026-09-01T00:00:00+08:00"
    multi = f"""---
episode_title: 虚构标题：多条 snip
show_author: Host Two
episode_publish_date: 2026-09-15T08:00:00+08:00
last_snip_date: 1999-01-01
episode_url: https://example.com/snipd/episodes/33333333-3333-4333-8333-333333333333
---

## Snips

### [00:01:00] 没有自己的时间
[🎧 Play snip](https://share.snipd.com/snip/{snip_a})

> 合成摘录：第一条没有 snip 时间。

### [00:02:00] 索引才看到
[🎧 Play snip](https://share.snipd.com/snip/{snip_b})

> 合成摘录：第二条也没有 snip 时间。

### [00:03:00] 自带时间
[🎧 Play snip](https://share.snipd.com/snip/{snip_c})
created_at: {own_c}

> 合成摘录：第三条用 snip 自己的时间。
"""

    def lookup(item_id: str) -> str | None:
        if item_id == snip_a:
            return git_a
        return None

    def item_seen(item_id: str) -> str | None:
        return {snip_a: index_a, snip_b: index_b, snip_c: "2026-10-19T12:00:00+08:00"}[item_id]

    parsed = inbox_lib.parse_note(
        multi,
        "snipd",
        ctx(
            "📥 Inbox/Snipd/example-show/multi.md",
            first_seen_at=source_seen,
            received_at_lookup=lookup,
            item_first_seen_at=item_seen,
        ),
    )
    assert len(parsed["inputs"]) == 3
    assert parsed["source"]["source_id"] == "src-snipd-33333333-3333-4333-8333-333333333333"
    assert parsed["source"]["first_seen_at"] == source_seen
    by_id = {item["external_item_id"]: item for item in parsed["inputs"]}
    assert by_id[snip_a]["received_at"] == git_a
    assert by_id[snip_a]["time_basis"] == "first_seen"
    assert by_id[snip_a]["captured_at"] == index_a
    assert by_id[snip_a]["captured_at"] != source_seen
    assert by_id[snip_b]["received_at"] == index_b
    assert by_id[snip_b]["captured_at"] == index_b
    assert by_id[snip_b]["received_at"] != source_seen
    assert by_id[snip_c]["time_basis"] == "platform"
    assert by_id[snip_c]["captured_at"] == own_c
    assert by_id[snip_c]["source_id"] == by_id[snip_a]["source_id"]
    assert len({item["input_id"] for item in parsed["inputs"]}) == 3
    for item in parsed["inputs"]:
        assert not item["captured_at"].startswith("1999-")
        assert not item["received_at"].startswith("1999-")


def test_weread_one_highlight_per_input_reuses_source() -> None:
    path = "📥 Inbox/WeRead/synthbook001.md"
    one = """---
doc_type: weread-highlights-reviews
bookId: synthbook001
title: 虚构书名：示例手册
author: 示例作者
published_at: 2020-01-01T00:00:00+08:00
source_url: https://example.com/weread/book/synthbook001?utm_campaign=share
---

## 第一章

> 📌 [合成划线：这是一句虚构的书中句子。](weread://highlight)
> ⏱ 2026-10-12 21:05:00
^synthbook001-1-10-20
"""
    parsed = inbox_lib.parse_weread(
        one,
        ctx(path, first_seen_at="2026-10-13T08:00:00+08:00", received_at="2026-10-13T08:00:00+08:00"),
    )
    assert len(parsed["inputs"]) == 1
    assert parsed["source"]["source_id"] == "src-weread-synthbook001"
    assert parsed["source"]["canonical_url"] == "https://example.com/weread/book/synthbook001"
    item = parsed["inputs"][0]
    assert item["input_id"] == "in-weread-6d560828fc45"
    assert item["external_item_id"] == "^synthbook001-1-10-20"
    assert item["event_type"] == "highlight"
    assert item["captured_at"] == "2026-10-12T21:05:00+08:00"
    assert item["time_basis"] == "platform"
    assert item["source_week"] == "2026-W42"
    assert item["content_fingerprint"] == "793c679661f6af6016f35a7f0fe7e0c695c2e64b3f68b261feb032b908920574"
    assert item["inbox_ref"] == path + "#^synthbook001-1-10-20"

    two = """---
bookId: synthbook001
title: 虚构书名：示例手册
author: 示例作者
source_url: https://example.com/weread/book/synthbook001
---

> 📌 [合成划线：这是一句虚构的书中句子。](weread://highlight)
> ⏱ 2026-10-12 21:05:00
^synthbook001-1-10-20

> 📌 [合成划线：第二条虚构句子，单独成条。](weread://highlight)
> ⏱ 2026-10-13 09:00:00
^synthbook001-2-1-8
"""
    again = inbox_lib.parse_note(
        two,
        "weread",
        ctx(path, first_seen_at="2026-10-13T08:00:00+08:00", received_at="2026-10-14T08:00:00+08:00"),
    )
    assert again["source"]["source_id"] == parsed["source"]["source_id"]
    assert len(again["inputs"]) == 2
    assert again["inputs"][0]["input_id"] == item["input_id"]
    assert again["inputs"][1]["external_item_id"] == "^synthbook001-2-1-8"
    assert again["inputs"][1]["input_id"] != item["input_id"]
    assert again["inputs"][1]["source_id"] == again["source"]["source_id"]
    assert again["inputs"][1]["event_type"] == "highlight"
    assert again["inputs"][1]["time_basis"] == "platform"

    other = """---
bookId: synthbook002
title: 虚构书名：另一本
author: 另一位
source_url: https://example.com/weread/book/synthbook002
---

> 📌 [合成划线：另一本书的一句。](weread://highlight)
> ⏱ 2026-10-11 10:00:00 ^synthbook002-1-1-4
"""
    second_book = inbox_lib.parse_weread(
        other,
        ctx("📥 Inbox/WeRead/synthbook002.md", first_seen_at="2026-10-11T12:00:00+08:00"),
    )
    assert second_book["source"]["source_id"] == "src-weread-synthbook002"
    assert len(second_book["inputs"]) == 1
    assert second_book["inputs"][0]["external_item_id"] == "^synthbook002-1-1-4"
    assert second_book["source"]["source_id"] != parsed["source"]["source_id"]


def test_x_and_instagram_first_seen_without_save_time() -> None:
    x_path = "📥 Inbox/X-Bookmarks/2026-10-15-example-user.md"
    x_note = """# @example_user：虚构短帖：示例标题

- 原文链接：https://example.com/x/status/1000000000000000001?utm_source=x
- 作者：example_user
- 发布时间：2026-10-10 12:00（北京时间）
- 类型：帖子
- Takeaway 生成日期：2026-10-15

## 摘要

合成帖文：这是一条虚构的短帖。

## Takeaways

- 不进入指纹
"""
    seen = "2026-10-15T08:05:00+08:00"
    parsed = inbox_lib.parse_x(x_note, ctx(x_path, first_seen_at=seen, received_at=seen))
    assert parsed["source"]["platform"] == "x"
    assert parsed["source"]["source_id"] == "src-x-1000000000000000001"
    assert parsed["source"]["canonical_url"] == "https://example.com/x/status/1000000000000000001"
    assert parsed["source"]["published_at"] == "2026-10-10T12:00:00+08:00"
    item = parsed["inputs"][0]
    assert item["input_id"] == "in-x-bda5d173b6da"
    assert item["external_item_id"] == "1000000000000000001"
    assert item["event_type"] == "bookmark"
    assert item["time_basis"] == "first_seen"
    assert item["captured_at"] == seen
    assert item["captured_at"] != item["source_published_at"]
    assert item["source_week"] == "2026-W42"
    assert item["content_fingerprint"] == "5fe0dd5f05ab1de6e5e9248977f4ed6a381ca4395bc0355a0ac2e2213cc076e4"
    assert "不进入指纹" not in item["content_fingerprint"]

    unnamed = """# @other_user：另一条虚构短帖

- 作者：other_user
- 发布时间：2026-10-11 09:00（北京时间）

## 摘要

合成帖文：第二条没有收藏时间。
"""
    file_id = "1000000000000000002"
    second = inbox_lib.parse_note(
        unnamed,
        "x",
        ctx(
            f"📥 Inbox/X-Bookmarks/2026-10-16-other_user-{file_id}.md",
            first_seen_at="2026-10-16T08:00:00+08:00",
        ),
    )
    assert second["source"]["external_content_id"] == file_id
    assert second["source"]["canonical_url"] == f"https://x.com/i/status/{file_id}"
    assert second["inputs"][0]["time_basis"] == "first_seen"
    assert second["inputs"][0]["captured_at"] == "2026-10-16T08:00:00+08:00"
    assert second["inputs"][0]["event_type"] == "bookmark"

    missing_seen = inbox_lib.parse_x(unnamed, ctx(f"📥 Inbox/X-Bookmarks/2026-10-16-other_user-{file_id}.md"))
    assert missing_seen["inputs"][0]["time_basis"] == "first_seen"
    assert missing_seen["inputs"][0]["captured_at"] is None
    assert missing_seen["inputs"][0]["source_week"] is None
    assert missing_seen["inputs"][0]["received_at"] is None

    ig_path = "📥 Inbox/Instagram-Saves/2026-10-01-example-author.md"
    ig = """# @example_author：虚构短视频：示例说明

- 原文链接：https://example.com/p/EXMPL00001?utm_medium=copy
- 作者：example_author
- 作者主页：https://www.instagram.com/example_author/
- 视频发布时间：2026-10-01 18:00
- Takeaway 生成日期：2026-10-16

## 摘要

合成收藏：这是一条虚构的短视频说明。
"""
    ig_seen = "2026-10-16T19:40:00+08:00"
    saved = inbox_lib.parse_instagram(ig, ctx(ig_path, first_seen_at=ig_seen, received_at=ig_seen))
    assert saved["source"]["source_id"] == "src-instagram-EXMPL00001"
    assert saved["source"]["published_at"] == "2026-10-01T18:00:00+08:00"
    assert saved["source"]["canonical_url"] == "https://example.com/p/EXMPL00001"
    ig_item = saved["inputs"][0]
    assert ig_item["input_id"] == "in-instagram-4f845a930248"
    assert ig_item["event_type"] == "save"
    assert ig_item["time_basis"] == "first_seen"
    assert ig_item["captured_at"] == ig_seen
    assert ig_item["source_week"] == "2026-W42"
    assert ig_item["origin"] == "collected"
    assert ig_item["content_fingerprint"] == "27d7702cdc2e0564f3ea74a7713209ab36886b0ac32122ac6dbfc6619daacf9c"

    historical = """# @example_author：虚构短视频：历史导入示例

- 原文链接：https://example.com/p/EXMPLHIST01
- 作者：example_author
- 视频发布时间：2021-12-01 12:00

## 摘要

合成收藏：这是一条虚构的历史导入说明。
"""
    hist_path = "📥 Inbox/Instagram-Saves/2021-12-01-example-author.md"
    hist_seen = "2026-10-17T08:00:00+08:00"
    old = inbox_lib.parse_note(
        historical,
        "instagram",
        ctx(hist_path, first_seen_at=hist_seen, received_at=hist_seen, origin="historical_import"),
    )
    old_item = old["inputs"][0]
    assert old["source"]["source_id"] == "src-instagram-EXMPLHIST01"
    assert old["source"]["published_at"] == "2021-12-01T12:00:00+08:00"
    assert old_item["input_id"] == "in-instagram-781395e78b4b"
    assert old_item["time_basis"] == "unknown"
    assert old_item["captured_at"] is None
    assert old_item["source_week"] is None
    assert old_item["origin"] == "historical_import"
    assert old_item["received_at"] == hist_seen
    assert old_item["content_fingerprint"] == "14bcf404f642b673353c104f639f77cdc0cc1ce62767e802569528dcca86c27b"

    second_ig = """# @other：虚构短视频：另一条

- 原文链接：https://www.instagram.com/reel/EXMPL00002/?utm_source=ig
- 视频发布时间：2026-10-02 10:00

## 摘要

合成收藏：第二条没有收藏时间。
"""
    other = inbox_lib.parse_instagram(
        second_ig,
        ctx("📥 Inbox/Instagram-Saves/2026-10-02-other-EXMPL00002.md", first_seen_at="2026-10-18T08:00:00+08:00"),
    )
    assert other["source"]["external_content_id"] == "EXMPL00002"
    assert other["source"]["canonical_url"] == "https://www.instagram.com/reel/EXMPL00002/"
    assert other["inputs"][0]["time_basis"] == "first_seen"
    assert other["inputs"][0]["captured_at"] == "2026-10-18T08:00:00+08:00"
    assert other["inputs"][0]["captured_at"] != other["source"]["published_at"]
    assert other["source"]["author"] == "other"


def test_thought_schema_sample_and_second_note() -> None:
    path = "📝 Journal/想法/thought-20261020-example.md"
    note = """---
id: thought-20261020-example
type: thought
tags:
  - thought
captured_at: 2026-10-20T09:00:00+08:00
week: 2026-W43
verbatim_sha256: ignored
title: 虚构原话：示例一则
url: https://example.com/thoughts/thought-20261020-example
---
原话:
合成原话：这是一句虚构的随手记。
"""
    seen = "2026-10-20T09:05:00+08:00"
    parsed = inbox_lib.parse_thought(note, ctx(path, first_seen_at=seen, received_at=seen))
    assert parsed["source"]["source_id"] == "src-thought-ua07dea66a1be"
    assert parsed["source"]["platform"] == "thought"
    assert parsed["source"]["external_content_id"] is None
    assert parsed["source"]["author"] is None
    assert parsed["source"]["published_at"] is None
    item = parsed["inputs"][0]
    assert item["input_id"] == "in-thought-1c47920095d4"
    assert item["external_item_id"] == "thought-20261020-example"
    assert item["event_type"] == "thought"
    assert item["time_basis"] == "platform"
    assert item["captured_at"] == "2026-10-20T09:00:00+08:00"
    assert item["source_week"] == "2026-W43"
    assert item["content_fingerprint"] == "3ae699348b0d289c10e328d4a24b90be5409496cf0a9bad2d25170645e74bdb1"
    assert item["inbox_ref"] == path + "#thought-20261020-example"

    second = """---
id: thought-20261021-0900
type: thought
captured_at: 2026-10-21T09:00:00+08:00
week: 2026-W43
verbatim_sha256: abc
---
原话:
第二条虚构原话，用来确认 platform 时间。
"""
    other = inbox_lib.parse_note(
        second,
        "thought",
        ctx("📝 Journal/想法/thought-20261021-0900.md", first_seen_at="2026-10-21T09:05:00+08:00"),
    )
    assert other["source"]["canonical_url"] == "thought://thought-20261021-0900"
    assert other["source"]["external_content_id"] is None
    assert other["source"]["source_id"] == inbox_lib.source_id_for(
        "thought", None, "thought://thought-20261021-0900"
    )
    assert other["inputs"][0]["time_basis"] == "platform"
    assert other["inputs"][0]["captured_at"] == "2026-10-21T09:00:00+08:00"
    assert other["inputs"][0]["event_type"] == "thought"
    assert other["inputs"][0]["completeness"] == "full"


def test_context_rejects_bad_origin() -> None:
    try:
        ctx("📥 Inbox/x.md", origin="imported")
    except ValueError as exc:
        assert "origin" in str(exc)
    else:
        raise AssertionError("expected ValueError")
