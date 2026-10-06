#!/usr/bin/env python3
"""Write yesterday's five-source takeaway. Does not append weekly intake.md."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_digest  # noqa: E402
from weekly_intake import new_item, parse_frontmatter, wiki_rel  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
SECTIONS = (
    ("Snipd", "snipd"),
    ("WeRead", "weread"),
    ("YouTube", "youtube"),
    ("Instagram", "instagram"),
    ("X", "x"),
)


def heading_title(text: str, path: Path) -> str:
    meta = parse_frontmatter(text)
    titled = meta.get("title")
    if titled:
        return titled
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def collect_named(vault: Path, day: dt.date, folder: str, kind: str) -> list:
    root = vault / "📥 Inbox" / folder
    if not root.is_dir():
        return []
    prefix = day.isoformat() + "-"
    items = []
    for path in sorted(root.glob(prefix + "*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        items.append(
            new_item(
                heading=f"{kind} · **{heading_title(text, path)}**",
                wiki=wiki_rel(path, vault),
                thread="",
                day=day,
                kind=kind.lower(),
            )
        )
    return items


def collect_all(vault: Path, day: dt.date) -> dict[str, list]:
    return {
        "snipd": daily_digest.collect_snipd(vault, day),
        "weread": daily_digest.collect_weread(vault, day),
        "youtube": daily_digest.collect_youtube(vault, day),
        "instagram": collect_named(vault, day, "Instagram-Saves", "Instagram"),
        "x": collect_named(vault, day, "X-Bookmarks", "X"),
    }


def render(day: dt.date, groups: dict[str, list]) -> str:
    total = sum(len(items) for items in groups.values())
    lines = [
        "---",
        "generator: information-flow-daily-takeaway",
        f"date: {day.isoformat()}",
        "---",
        "",
        f"# {day.isoformat()}",
        "",
    ]
    if total == 0:
        lines.append("这一天五个入口都没有新到的条目。")
        lines.append("")
    for title, key in SECTIONS:
        lines.append(f"## {title}")
        lines.append("")
        items = groups[key]
        if not items:
            lines.append("没有新到的条目。")
            lines.append("")
            continue
        for item in items:
            lines.append(f"- [[{item.wiki}]] — {item.briefing_line}")
            for line in item.extra:
                if line.strip().startswith("- 摄入："):
                    continue
                lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def takeaway_path(vault: Path, day: dt.date) -> Path:
    return vault / "📋 Digests" / "daily" / f"{day.isoformat()}.md"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one Shanghai day's inbox takeaway")
    parser.add_argument("--date", help="the day to summarize; default is yesterday in Shanghai")
    parser.add_argument("--vault")
    args = parser.parse_args(argv)
    vault = daily_digest.vault_path(args.vault)
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1
    if args.date:
        day = dt.date.fromisoformat(args.date)
    else:
        day = dt.datetime.now(SHANGHAI).date() - dt.timedelta(days=1)
    dest = takeaway_path(vault, day)
    dest.parent.mkdir(parents=True, exist_ok=True)
    groups = collect_all(vault, day)
    dest.write_text(render(day, groups), encoding="utf-8")
    counts = " ".join(f"{key}={len(groups[key])}" for _, key in SECTIONS)
    print(f"wrote {dest} {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
