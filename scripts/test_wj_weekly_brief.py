#!/usr/bin/env python3
"""Plain asserts for the weekly brief builder. No vault, network, or model calls."""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import weekly_intake  # noqa: E402
import wj_weekly_brief as wj  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "wj_weekly_brief.py"


def entry(entry_id: str, topic: str, link: str, source_week: str, status: str) -> dict:
    return {
        "id": entry_id,
        "topic": topic,
        "source_link": link,
        "source_week": source_week,
        "status": status,
    }


def entry_lines(text: str, entry_id: str) -> list[str]:
    marker = f"- id: {entry_id}"
    start = text.index(marker)
    rest = text[start:]
    lines = []
    for line in rest.splitlines():
        if lines and (line.startswith("- id: ") or line.startswith("### ") or line.startswith("## ")):
            break
        if line == "":
            break
        lines.append(line)
    return lines


def test_iso_weeks() -> None:
    # ISO 8601, same rule as weekly_intake.iso_week.
    # 2026-10-12 is Monday of 2026-W42. 2026-W41 is the week of 2026-10-05.
    assert wj.iso_week_label(dt.date(2026, 10, 12)) == "2026-W42"
    assert wj.iso_week_label(dt.date(2026, 10, 5)) == "2026-W41"
    assert wj.iso_week_label(dt.date(2026, 1, 1)) == "2026-W01"
    assert wj.iso_week_label(dt.date(2027, 1, 1)) == "2026-W53"
    utc = dt.timezone.utc
    # 2026-10-04 16:00 UTC is 2026-10-05 00:00 in Asia/Shanghai (Monday, W41).
    assert wj.iso_week_label(dt.datetime(2026, 10, 4, 15, 59, tzinfo=utc)) == "2026-W40"
    assert wj.iso_week_label(dt.datetime(2026, 10, 4, 16, 0, tzinfo=utc)) == "2026-W41"
    assert wj.iso_week_label(dt.datetime(2026, 10, 5, 0, 30)) == "2026-W41"
    for day in (dt.date(2026, 10, 12), dt.date(2026, 1, 1), dt.date(2027, 1, 1), dt.date(2026, 10, 5)):
        assert wj.iso_week_label(day) == weekly_intake.iso_week(day)


def test_path() -> None:
    assert wj.brief_rel_path("2026-W41") == "📋 Digests/weekly-briefs/2026-W41.md"
    assert wj.brief_rel_path(wj.iso_week_label(dt.date(2026, 10, 12))) == (
        "📋 Digests/weekly-briefs/2026-W42.md"
    )


def test_statuses_and_missing_source() -> None:
    assert wj.STATUSES == {"待讨论", "已讨论", "暂缓", "来源缺失/失败"}
    text = wj.build_brief(
        "2026-W42",
        [
            entry("hold-1", "topic-a", "link-hold", "2026-W42", "暂缓"),
            entry("open-1", "topic-a", "link-open", "2026-W42", "待讨论"),
            entry("done-1", "topic-b", "link-done", "2026-W42", "已讨论"),
            entry("miss-1", "topic-b", "link-miss", "2026-W42", "来源缺失/失败"),
        ],
    )
    for status in ("待讨论", "已讨论", "暂缓", "来源缺失/失败"):
        assert f"状态: {status}" in text
    assert entry_lines(text, "miss-1") == [
        "- id: miss-1",
        "  - 来源周: 2026-W42",
        "  - 来源: link-miss",
        "  - 状态: 来源缺失/失败",
    ]
    assert "摘要" not in text
    assert "总结" not in text
    index, carry = text.split("## 遗留候选", 1)
    assert "miss-1" in index
    assert "miss-1" not in carry
    assert index.index("### topic-a") < index.index("### topic-b")
    assert index.index("- id: hold-1") < index.index("- id: open-1")
    assert index.count("### topic-a") == 1
    try:
        wj.build_brief("2026-W42", [entry("x", "t", "l", "2026-W42", "discussed")])
    except ValueError:
        pass
    else:
        raise AssertionError("unknown status must fail")


def test_carryover() -> None:
    previous = wj.build_brief(
        "2026-W41",
        [
            entry("open-1", "topic-a", "link-open", "2026-W41", "待讨论"),
            entry("done-1", "topic-a", "link-done", "2026-W41", "已讨论"),
            entry("hold-1", "topic-b", "link-hold", "2026-W41", "暂缓"),
            entry("miss-old", "topic-c", "link-miss-old", "2026-W41", "来源缺失/失败"),
        ],
    )
    current = wj.build_brief(
        "2026-W42",
        [
            # Same id as a carried row, with a newer week and 已讨论.
            # It must stay a candidate, original week kept, not flipped, not duplicated.
            entry("open-1", "topic-a", "link-open-new", "2026-W42", "已讨论"),
            entry("new-1", "topic-d", "link-new", "2026-W42", "待讨论"),
        ],
        previous_brief=previous,
    )
    index, carry = current.split("## 遗留候选", 1)
    assert "## 遗留候选" in current
    assert "open-1" in carry
    assert "2026-W41" in carry
    assert "link-open" in carry
    assert "link-open-new" not in current
    assert current.count("- id: open-1") == 1
    assert "状态: 待讨论" in entry_lines(current, "open-1")[-1]
    assert "done-1" not in current
    assert "hold-1" in carry
    assert entry_lines(current, "hold-1")[-1] == "  - 状态: 暂缓"
    assert "2026-W41" in "\n".join(entry_lines(current, "hold-1"))
    assert entry_lines(current, "miss-old") == [
        "- id: miss-old",
        "  - 来源周: 2026-W41",
        "  - 来源: link-miss-old",
        "  - 状态: 来源缺失/失败",
    ]
    assert "new-1" in index
    assert "new-1" not in carry
    assert "open-1" not in index

    week40 = wj.build_brief(
        "2026-W40",
        [entry("aged-1", "topic-a", "link-aged", "2026-W40", "待讨论")],
    )
    week41 = wj.build_brief("2026-W41", [], previous_brief=week40)
    week42 = wj.build_brief("2026-W42", [], previous_brief=week41)
    aged = "\n".join(entry_lines(week42, "aged-1"))
    assert "来源周: 2026-W40" in aged
    assert "状态: 待讨论" in aged
    assert week42.count("- id: aged-1") == 1
    assert aged in week42.split("## 遗留候选", 1)[1]


def test_determinism() -> None:
    rows = [
        entry("b", "zeta", "link-b", "2026-W42", "待讨论"),
        entry("a", "zeta", "link-a", "2026-W42", "已讨论"),
        entry("c", "alpha", "link-c", "2026-W42", "暂缓"),
    ]
    previous = wj.build_brief(
        "2026-W41",
        [entry("z", "mid", "link-z", "2026-W41", "待讨论")],
    )
    first = wj.build_brief("2026-W42", rows, previous_brief=previous)
    second = wj.build_brief("2026-W42", list(reversed(rows)), previous_brief=previous)
    assert first == second
    assert first.encode("utf-8") == second.encode("utf-8")


def test_no_writes_and_print() -> None:
    payload = {
        "week_label": "2026-W42",
        "entries": [entry("n1", "topic", "link-n", "2026-W42", "待讨论")],
        "previous_brief": None,
    }
    expected = wj.build_brief(payload["week_label"], payload["entries"], None)
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as raw:
        os.chdir(raw)
        try:
            printed = wj.build_brief(payload["week_label"], payload["entries"], None)
            assert printed == expected
            assert os.listdir(raw) == []
        finally:
            os.chdir(cwd)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=raw,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == expected
        assert os.listdir(raw) == []


def main() -> None:
    test_iso_weeks()
    test_path()
    test_statuses_and_missing_source()
    test_carryover()
    test_determinism()
    test_no_writes_and_print()
    print("ok")


if __name__ == "__main__":
    main()
