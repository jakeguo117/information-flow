#!/usr/bin/env python3
"""本周完整性闸。规则以 skills/discuss-to-resources-ideas/SKILL.md 为准。

这个脚本只判断本周日期篇和归堆正本齐不齐，不写文件，不提炼。
带 ``-gpt`` 的归堆文件不拿来补覆盖。无 Inbox 的工作日必须由调用方用
``--empty-inbox-day`` 明确标出；没标又没有正本的日子按缺漏拦，不算豁免。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

HK = ZoneInfo("Asia/Hong_Kong")
CLUSTER_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:_(?P<span>\d{2}))?(?P<gpt>-gpt)?\.md$"
)
JOURNAL_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2}).*\.md$")
JOURNAL_ROOT = "📝 Journal/"
CLUSTER_ROOT = "📋 Digests/cluster/"
WEEKDAY_NAMES = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

WEEKDAY_BLOCK = "平日不跑。周一至周五，以及 cluster 或 Journal 落盘当下，不跑本技能。不要改到平日补。"
SUNDAY_BLOCK = (
    "周日不是改成只周日跑。只有本周周六因本周完整性闸被拦住时，"
    "同周周日才用同一技能、同一闸补跑。这次没有这个前提，不生成。"
)
REMIND = (
    "补法：日期篇由 Jake 说「写周记」走 journal skill 落盘。"
    "缺的归堆正本按平日 daily-cluster 路径补，不新造职责。"
    "文件入库后再跑本技能、同一道闸。若这次是周六被拦住，同周周日可以补跑。"
    "闸过才生成 idea、resource、plan。"
    "不要在缺的时候调用 write_idea.py，不要做 Resources 正式入库，不要把 plan 清单交给资料管理员。"
)


def hk_date(run_at: dt.datetime) -> dt.date:
    if run_at.tzinfo is None:
        raise ValueError("run-at 必须带时区")
    return run_at.astimezone(HK).date()


def week_monday(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def parse_run_at(raw: str) -> dt.datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("run-at 必须带时区")
    return parsed


def _dates_covered_by_name(name: str) -> frozenset[dt.date]:
    match = CLUSTER_RE.fullmatch(name)
    if match is None or match.group("gpt"):
        return frozenset()
    start = dt.date.fromisoformat(match.group("date"))
    span = match.group("span")
    if span is None:
        return frozenset((start,))
    try:
        end = start.replace(day=int(span))
    except ValueError:
        return frozenset()
    if end <= start:
        return frozenset()
    days: list[dt.date] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += dt.timedelta(days=1)
    return frozenset(days)


def cluster_covered_dates(raw: str) -> frozenset[dt.date]:
    """Dates covered by one 正本. ``-gpt`` and non-cluster paths cover nothing."""
    posix = raw.replace("\\", "/").strip()
    if "Digests/daily" in posix:
        return frozenset()
    if "/" in posix and not posix.startswith(CLUSTER_ROOT):
        return frozenset()
    return _dates_covered_by_name(Path(posix).name)


def journal_day(raw: str) -> dt.date | None:
    """Date of a Journal root file. Subfolders, including 想法/, do not count."""
    posix = raw.replace("\\", "/").strip().lstrip("./")
    if posix.startswith(JOURNAL_ROOT):
        rest = posix[len(JOURNAL_ROOT) :]
        if rest == "" or "/" in rest:
            return None
        name = rest
    elif "/" in posix:
        return None
    else:
        name = posix
    match = JOURNAL_RE.fullmatch(name)
    if match is None:
        return None
    try:
        return dt.date.fromisoformat(match.group("date"))
    except ValueError:
        return None


def _parse_day(raw: str, flag: str) -> dt.date:
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{flag} 必须是 YYYY-MM-DD") from exc


def evaluate(
    *,
    run_at: dt.datetime,
    cluster_names: list[str],
    journal_paths: list[str],
    inbox_days: list[dt.date],
    empty_inbox_days: list[dt.date],
    saturday_blocked: bool,
) -> dict[str, object]:
    """Return the gate result. Does not read the vault and does not write."""
    day = hk_date(run_at)
    monday = week_monday(day)
    sunday = monday + dt.timedelta(days=6)
    weekdays = [monday + dt.timedelta(days=i) for i in range(5)]
    weekday_set = set(weekdays)
    inbox_set = set(inbox_days)
    empty_set = set(empty_inbox_days)
    outside = sorted(day for day in inbox_set | empty_set if day not in weekday_set)
    if outside:
        listed = "、".join(item.isoformat() for item in outside)
        raise ValueError(f"Inbox 日期不在本周周一至周五：{listed}")
    overlap = sorted(inbox_set & empty_set)
    if overlap:
        listed = "、".join(item.isoformat() for item in overlap)
        raise ValueError(f"同一天不能既有 Inbox 又标成无 Inbox：{listed}")

    covered: set[dt.date] = set()
    for name in cluster_names:
        covered |= set(cluster_covered_dates(name))

    journal_hits: list[str] = []
    seen: set[str] = set()
    for raw in journal_paths:
        posix = raw.replace("\\", "/").strip()
        found = journal_day(posix)
        if found is None or not (monday <= found <= sunday):
            continue
        key = posix.lstrip("./")
        if key in seen:
            continue
        seen.add(key)
        journal_hits.append(key)

    hk_weekday = WEEKDAY_NAMES[day.weekday()]
    run_allowed = day.weekday() == 5 or (day.weekday() == 6 and saturday_blocked)
    missing: list[str] = []
    remind = ""
    exempt: list[str] = []

    if day.weekday() <= 4:
        missing.append(WEEKDAY_BLOCK)
        remind = WEEKDAY_BLOCK
    elif day.weekday() == 6 and not saturday_blocked:
        missing.append(SUNDAY_BLOCK)
        remind = SUNDAY_BLOCK
    else:
        if not journal_hits:
            missing.append(
                "本周 📝 Journal/{日期}*.md 为 0 篇。"
                f"需要至少 1 篇，日期落在 {monday.isoformat()} 至 {sunday.isoformat()}"
                "（Asia/Hong_Kong 周一至周日）。不要求必须有周五。📝 Journal/想法/ 不算。"
            )
        for item in weekdays:
            if item in covered:
                continue
            if item in empty_set:
                exempt.append(item.isoformat())
                continue
            if item in inbox_set:
                missing.append(
                    f"缺归堆正本：{item.isoformat()}。这一天有 Inbox，"
                    "没有 📋 Digests/cluster/ 正本盖住。"
                    "单日文件是 YYYY-MM-DD.md，多日是 YYYY-MM-DD_DD.md。"
                    "带 -gpt 的文件不拿来补这个覆盖。"
                )
            else:
                missing.append(
                    f"未查清 Inbox：{item.isoformat()}。这一天没有归堆正本盖住，"
                    "也没有确认是无 Inbox。先不算空日豁免。"
                )
        if missing:
            remind = REMIND

    passed = run_allowed and not missing
    return {
        "passed": passed,
        "produce": passed,
        "run_allowed": run_allowed,
        "hk_date": day.isoformat(),
        "hk_weekday": hk_weekday,
        "week_start": monday.isoformat(),
        "week_end": sunday.isoformat(),
        "weekdays": [item.isoformat() for item in weekdays],
        "journal_count": len(journal_hits),
        "journal_files": journal_hits,
        "exempt_empty_inbox": exempt,
        "missing": missing,
        "remind": remind,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本周完整性闸。只判断，不写文件。")
    parser.add_argument("--run-at", required=True, help="这次运行的时刻，必须带时区")
    parser.add_argument("--cluster-name", action="append", default=[], help="归堆文件名，可重复")
    parser.add_argument("--journal", action="append", default=[], help="Journal 顶层日期篇路径，可重复")
    parser.add_argument("--inbox-day", action="append", default=[], help="确认有 Inbox 的工作日，可重复")
    parser.add_argument("--empty-inbox-day", action="append", default=[], help="确认无 Inbox 的工作日，可重复")
    parser.add_argument(
        "--saturday-blocked",
        action="store_true",
        help="本周周六已因这道闸被拦住。只有周日补跑才需要",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = evaluate(
            run_at=parse_run_at(args.run_at),
            cluster_names=list(args.cluster_name),
            journal_paths=list(args.journal),
            inbox_days=[_parse_day(item, "--inbox-day") for item in args.inbox_day],
            empty_inbox_days=[_parse_day(item, "--empty-inbox-day") for item in args.empty_inbox_day],
            saturday_blocked=bool(args.saturday_blocked),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
