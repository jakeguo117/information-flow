#!/usr/bin/env python3
"""Build one ISO week's digest.md from that week's daily digests.

Week is Asia/Shanghai. The only path this writes is:

    📋 Digests/{YYYY-Wnn}/digest.md

Daily sources, for each calendar day of that week, in this order:

    📋 Digests/daily/YYYY-MM-DD.md
    📋 Digests/YYYY-MM-DD-Digest.md

If the week has no daily digest files, fall back to:

    📋 Digests/{YYYY-Wnn}/intake.md

Real items become numbered lines (T/F/C-YYYYWww-n) with a one-line summary
and a link. Groups come from headings (值得讨论的 / 可以引用的 / 可以借用的).
An unlabeled item is 值得讨论的. Empty placeholder days are not items.
When nothing real is found, this writes no file and exits 2.
Stdout is only the relative path and counts, never item text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import weekly_intake  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
WIKI_RE = re.compile(r"\[\[(.+?)\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BARE_URL_RE = re.compile(r"https?://[^\s)>\]]+")
CHECKBOX_RE = re.compile(r"^\[[ xX]\]\s*")
EMPTY_LINES = {
    "没有新到的条目。",
    "这一天五个入口都没有新到的条目。",
    "（还没有条目。）",
}
GROUPS = (
    ("T", "值得讨论的（thesis）"),
    ("F", "可以引用的"),
    ("C", "可以借用的"),
)
GENERATOR = "information-flow-weekly-digest"
NO_CONTENT_EXIT = 2


@dataclass
class DigestItem:
    group: str
    summary: str
    link: str
    key: str


def shanghai_today(now: dt.datetime | None = None) -> dt.date:
    if now is None:
        current = dt.datetime.now(SHANGHAI)
    elif now.tzinfo is None:
        current = now.replace(tzinfo=SHANGHAI)
    else:
        current = now.astimezone(SHANGHAI)
    return current.date()


def week_from_date(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def parse_week(text: str) -> tuple[int, int]:
    match = WEEK_RE.match(text.strip())
    if not match:
        raise ValueError(f"invalid ISO week: {text}")
    year, week = int(match.group(1)), int(match.group(2))
    dt.date.fromisocalendar(year, week, 1)
    return year, week


def week_days(year: int, week: int) -> list[dt.date]:
    monday = dt.date.fromisocalendar(year, week, 1)
    return [monday + dt.timedelta(days=offset) for offset in range(7)]


def id_token(year: int, week: int) -> str:
    return f"{year}W{week:02d}"


def group_for_heading(title: str) -> str | None:
    lowered = title.lower()
    if "值得讨论" in title or "thesis" in lowered:
        return "T"
    if "可以引用" in title or "摘句" in title:
        return "F"
    if "可以借用" in title:
        return "C"
    return None


def _clean_summary(body: str) -> str:
    text = WIKI_RE.sub(" ", body)
    text = MD_LINK_RE.sub(" ", text)
    text = BARE_URL_RE.sub(" ", text)
    text = text.replace("**", " ")
    text = text.replace("—", " ").replace("–", " ")
    text = re.sub(r"\s+", " ", text).strip(" \t-|｜")
    if len(text) > 180:
        text = text[:177].rstrip() + "…"
    return text


def parse_bullet(line: str, group: str) -> DigestItem | None:
    body = CHECKBOX_RE.sub("", line[2:].strip())
    if not body or body in EMPTY_LINES or body.startswith("没有新到的条目"):
        return None
    wiki_match = WIKI_RE.search(body)
    wiki = wiki_match.group(1).strip() if wiki_match else ""
    link_match = MD_LINK_RE.search(body)
    if link_match:
        url = link_match.group(2)
    else:
        bare = BARE_URL_RE.search(body)
        url = bare.group(0).rstrip(".,，。") if bare else ""
    summary = _clean_summary(body)
    if url:
        link = f"[原文]({url})"
        key = url
    elif wiki:
        link = f"[[{wiki}]]"
        key = wiki
    else:
        return None
    if not summary:
        summary = Path(wiki).name if wiki else url
    if not summary:
        return None
    return DigestItem(group=group, summary=summary, link=link, key=key)


def parse_digest_markdown(text: str) -> list[DigestItem]:
    group = "T"
    items: list[DigestItem] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            mapped = group_for_heading(line[3:].strip())
            group = mapped if mapped else "T"
            continue
        if not line.startswith("- "):
            continue
        item = parse_bullet(line, group)
        if item is not None:
            items.append(item)
    return items


def parse_intake(text: str) -> list[DigestItem]:
    items: list[DigestItem] = []
    for entry in weekly_intake.parse_items(text):
        summary = _clean_summary(entry.briefing_line)
        wiki = entry.wiki.strip()
        if not summary or not wiki or summary in EMPTY_LINES:
            continue
        items.append(DigestItem(group="T", summary=summary, link=f"[[{wiki}]]", key=wiki))
    return items


def _is_real_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def daily_candidates(vault: Path, day: dt.date) -> list[Path]:
    name = day.isoformat()
    root = vault / "📋 Digests"
    return [
        root / "daily" / f"{name}.md",
        root / f"{name}-Digest.md",
    ]


def collect_items(vault: Path, year: int, week: int) -> tuple[list[DigestItem], str]:
    paths: list[Path] = []
    for day in week_days(year, week):
        for path in daily_candidates(vault, day):
            if _is_real_file(path):
                paths.append(path)
    source = "daily"
    items: list[DigestItem] = []
    if paths:
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            items.extend(parse_digest_markdown(text))
    else:
        source = "intake"
        intake = weekly_intake.intake_path(vault, f"{year}-W{week:02d}")
        if _is_real_file(intake):
            text = intake.read_text(encoding="utf-8", errors="replace")
            items.extend(parse_intake(text))
    deduped: list[DigestItem] = []
    seen: set[str] = set()
    for item in items:
        if item.key in seen:
            continue
        seen.add(item.key)
        deduped.append(item)
    return deduped, source


def render_digest(week: str, items: list[DigestItem]) -> str:
    year, week_no = parse_week(week)
    token = id_token(year, week_no)
    lines = [
        "---",
        f"week: {week}",
        f"generator: {GENERATOR}",
        "---",
        "",
        f"# 本周 digest（{week}）",
        "",
    ]
    for prefix, title in GROUPS:
        grouped = [item for item in items if item.group == prefix]
        if not grouped:
            continue
        lines.append(f"## {title}")
        lines.append("")
        for number, item in enumerate(grouped, start=1):
            lines.append(f"- **{prefix}-{token}-{number}**｜{item.summary}｜{item.link}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def digest_path(vault: Path, week: str) -> Path:
    return vault / "📋 Digests" / week / "digest.md"


def build_week(vault: Path, week: str) -> int:
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1
    try:
        year, week_no = parse_week(week)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    canonical = f"{year}-W{week_no:02d}"
    items, source = collect_items(vault, year, week_no)
    if not items:
        print(f"本周 digest 还没有可写入的内容：{canonical}", file=sys.stderr)
        return NO_CONTENT_EXIT
    text = render_digest(canonical, items)
    dest = digest_path(vault, canonical)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_suffix(".md.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(dest)
    counts = " ".join(
        f"{prefix}={sum(1 for item in items if item.group == prefix)}" for prefix, _ in GROUPS
    )
    print(f"wrote {dest.relative_to(vault).as_posix()} source={source} {counts}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build 📋 Digests/{YYYY-Wnn}/digest.md")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--week", help="ISO week YYYY-Wnn evaluated in Asia/Shanghai")
    parser.add_argument("--date", help="YYYY-MM-DD; use the ISO week of this calendar date")
    args = parser.parse_args(argv)
    if args.week and args.date:
        print("pass only one of --week and --date", file=sys.stderr)
        return 1
    vault = Path(args.vault).expanduser()
    if args.week:
        week = args.week
    elif args.date:
        try:
            week = week_from_date(dt.date.fromisoformat(args.date))
        except ValueError:
            print(f"invalid date: {args.date}", file=sys.stderr)
            return 1
    else:
        week = week_from_date(shanghai_today())
    return build_week(vault, week)


if __name__ == "__main__":
    raise SystemExit(main())
