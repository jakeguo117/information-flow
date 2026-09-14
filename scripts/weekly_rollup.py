#!/usr/bin/env python3
"""Roll this week's daily Digests into one 周汇总. Does not call Hermes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PLUGIN_ROOT / "state"

SKIP_NAME = re.compile(r"非正式|演示|历史主题|周汇总|weekly-brief", re.I)
DAILY_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-Digest\.md$")
HEADING = re.compile(r"^## (.+)$")
SNIP_ITEM = re.compile(r"^- \*\*(.+?)\*\* — (.+?)（")
YT_ITEM = re.compile(r"^- \*\*(.+?)\*\* — (.+)$")
WEREAD_ITEM = re.compile(r"^- \*\*(.+?)\*\*\s*$")
WIKI = re.compile(r"\[\[(.+?)\]\]")
QUOTE_LINE = re.compile(r"^  - (?!\[\[)(.+)$")


def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


def iso_week_label(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_bounds(day: dt.date) -> tuple[dt.date, dt.date]:
    start = day - dt.timedelta(days=day.isoweekday() - 1)
    end = start + dt.timedelta(days=6)
    return start, end


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def parse_daily(path: Path) -> dict | None:
    if SKIP_NAME.search(path.name):
        return None
    match = DAILY_NAME.match(path.name)
    if not match:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = parse_frontmatter(text)
    if meta.get("generator") != "journal-daily-digest":
        return None
    day = dt.date.fromisoformat(match.group(1))
    section = None
    items: list[dict] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current:
            items.append(current)
            current = None

    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            flush()
            title = heading.group(1).strip()
            if title.startswith("Snipd"):
                section = "snipd"
            elif title.startswith("WeRead"):
                section = "weread"
            elif title.startswith("YouTube"):
                section = "youtube"
            else:
                section = None
            continue
        if section in {"snipd", "weread", "youtube"} and line.startswith("- **"):
            flush()
            if section == "snipd":
                parsed = SNIP_ITEM.match(line)
                if parsed:
                    current = {
                        "kind": "snipd",
                        "show": parsed.group(1),
                        "title": parsed.group(2),
                        "wiki": None,
                        "quote": None,
                    }
            elif section == "youtube":
                parsed = YT_ITEM.match(line)
                if parsed:
                    current = {
                        "kind": "youtube",
                        "show": parsed.group(1),
                        "title": parsed.group(2),
                        "wiki": None,
                        "quote": None,
                    }
            else:
                parsed = WEREAD_ITEM.match(line)
                if parsed:
                    current = {
                        "kind": "weread",
                        "show": "WeRead",
                        "title": parsed.group(1),
                        "wiki": None,
                        "quote": None,
                    }
            continue
        if current is None:
            continue
        wiki = WIKI.search(line)
        if wiki and not current.get("wiki"):
            current["wiki"] = wiki.group(1)
            continue
        quote = QUOTE_LINE.match(line)
        if quote and not current.get("quote"):
            current["quote"] = quote.group(1).strip()
    flush()
    return {"date": day, "week": meta.get("week") or iso_week_label(day), "items": items, "path": path}


def collect_week(vault: Path, week: str) -> list[dict]:
    root = vault / "📋 Digests"
    if not root.is_dir():
        return []
    days = []
    for path in sorted(root.glob("*-Digest.md")):
        parsed = parse_daily(path)
        if not parsed:
            continue
        if parsed["week"] != week:
            continue
        days.append(parsed)
    return days


def render(week: str, days: list[dict], run_day: dt.date) -> str:
    covers = [d["date"].isoformat() for d in days]
    item_count = sum(len(d["items"]) for d in days)
    lines = [
        "---",
        f"date: {run_day.isoformat()}",
        "type: weekly-brief",
        f"week: {week}",
        f"covers: [{', '.join(covers)}]",
        f"item_count: {item_count}",
        "generator: journal-weekly-rollup",
        "---",
        "",
        f"# 周汇总 — {week}",
        "",
        "本周每日 Digest 收成讨论燃料。一句来源 + 一句划线。原文在各日 Digest 和 vault 链接里。",
        "",
    ]
    if not days:
        lines.append("本周还没有 `journal-daily-digest` 生成的每日篇。")
        lines.append("")
        return "\n".join(lines)

    for day in days:
        lines.append(f"## {day['date'].isoformat()}")
        lines.append("")
        if not day["items"]:
            lines.append("- 无条目")
            lines.append("")
            continue
        for item in day["items"]:
            if item["kind"] == "snipd":
                head = f"- Snipd · {item['show']} — {item['title']}"
            elif item["kind"] == "youtube":
                head = f"- YouTube · {item['show']} — {item['title']}"
            else:
                head = f"- WeRead · {item['title']}"
            lines.append(head)
            if item.get("wiki"):
                lines.append(f"  - [[{item['wiki']}]]")
            if item.get("quote"):
                lines.append(f"  - {item['quote']}")
        lines.append("")
    has_youtube = any(item["kind"] == "youtube" for day in days for item in day["items"])
    if not has_youtube:
        lines.append("YouTube 点赞：本周无新增。")
        lines.append("")
    return "\n".join(lines)


def write_rollup(vault: Path, week: str, text: str, force: bool) -> Path:
    out_dir = vault / "📊 Journal Briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{week}.md"
    if dest.exists() and not force:
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if "generator: journal-weekly-rollup" not in existing:
            raise SystemExit(f"refusing to overwrite non-generated rollup: {dest}")
    dest.write_text(text, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roll daily Digests into one weekly brief")
    parser.add_argument("--date", help="YYYY-MM-DD in the target ISO week (default: today Asia/Shanghai)")
    parser.add_argument("--vault")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    day = dt.date.fromisoformat(args.date) if args.date else today
    week = iso_week_label(day)

    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    days = collect_week(vault, week)
    text = render(week, days, run_day=today)
    dest = write_rollup(vault, week, text, force=args.force)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "weekly-rollup.log").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "ran_at": dt.datetime.now(SHANGHAI).isoformat(),
                    "week": week,
                    "days": [d["date"].isoformat() for d in days],
                    "path": str(dest),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    print(f"wrote {dest} days={len(days)} items={sum(len(d['items']) for d in days)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
