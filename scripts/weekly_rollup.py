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
    idx = text.find("\n## 讨论")
    if idx < 0 and not text.lstrip().startswith("## 讨论"):
        return None
    block = text[idx if idx >= 0 else 0 :]
    start = block.find("## 讨论")
    block = block[start + len("## 讨论") :]
    points: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            point = stripped[2:].strip()
            if point:
                points.append(point)
        elif stripped.startswith("[["):
            continue
    if not points:
        return None
    day = dt.date.fromisoformat(match.group(1))
    return {
        "date": day,
        "week": meta.get("week") or iso_week_label(day),
        "points": points[:7],
        "path": path,
        "wiki": path.stem,
    }


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
    item_count = sum(len(d["points"]) for d in days)
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
        "只收本周已经讨论过的 Digest。没有 ## 讨论 的天不进这里。",
        "",
    ]
    if not days:
        lines.append("本周还没有带讨论的 Digest。")
        lines.append("")
        return "\n".join(lines)

    lines.append("## 能对线的点")
    lines.append("")
    cues = []
    for day in days:
        for point in day["points"]:
            if point not in cues:
                cues.append(point)
            if len(cues) >= 7:
                break
        if len(cues) >= 7:
            break
    for point in cues:
        lines.append(f"- {point}")
    lines.append("")
    for day in days:
        lines.append(f"## {day['date'].isoformat()}")
        lines.append("")
        lines.append(f"- [[{day['wiki']}]]")
        for point in day["points"]:
            lines.append(f"- {point}")
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
    dest = vault / "📊 Journal Briefs" / f"{week}.md"
    if not days:
        if dest.exists():
            existing = dest.read_text(encoding="utf-8", errors="replace")
            if "generator: journal-weekly-rollup" in existing:
                dest.unlink()
                print(f"removed empty {dest}")
        else:
            print(f"skip {week} (no discussed digests)")
        return 0
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
    print(f"wrote {dest} days={len(days)} points={sum(len(d['points']) for d in days)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
