#!/usr/bin/env python3
"""Append new Snipd/WeRead/YouTube into this week's intake.md. No Hermes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from weekly_intake import (  # noqa: E402
    append_items,
    iso_week,
    join_thread,
    new_item,
    parse_frontmatter,
    split_sentences,
    usable_quote,
    wiki_rel,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PLUGIN_ROOT / "state"

WEREAD_PIN = re.compile(r"^>\s*📌\s*\[(.+?)\]")
WEREAD_TIME = re.compile(r"^>\s*⏱\s+(\d{4}-\d{2}-\d{2})")


def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


def snipd_thread(text: str) -> str:
    for line in text.splitlines():
        if "Episode AI description:" not in line:
            continue
        desc = line.split("Episode AI description:", 1)[1].strip()
        parts = split_sentences(desc, 3)
        if parts:
            return join_thread(parts)
    bullets: list[str] = []
    in_snips = False
    for line in text.splitlines():
        if line.startswith("## Snips"):
            in_snips = True
            continue
        if in_snips and line.startswith("## "):
            break
        if not in_snips:
            continue
        stripped = line.strip()
        if stripped.startswith("####") or stripped.startswith(">") or stripped.startswith("**"):
            continue
        if stripped.startswith("- ") and not stripped.startswith("- ["):
            point = stripped[2:].strip()
            if len(point) >= 12:
                bullets.append(point)
        if len(bullets) >= 2:
            break
    return join_thread(bullets[:3])


def collect_snipd(vault: Path, day: dt.date) -> list:
    root = vault / "Snipd" / "Data"
    if not root.is_dir():
        return []
    day_s = day.isoformat()
    items = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        if meta.get("last_snip_date") != day_s:
            continue
        show = meta.get("show_title") or path.parent.name
        title = meta.get("episode_title") or path.stem
        items.append(
            new_item(
                heading=f"Snipd · **{show}** — {title}",
                wiki=wiki_rel(path, vault),
                thread=snipd_thread(text),
                day=day,
                kind="snipd",
            )
        )
    return items


def weread_pins_for_day(text: str, day: dt.date) -> list[str]:
    day_s = day.isoformat()
    pins: list[str] = []
    pending: str | None = None
    for line in text.splitlines():
        pin = WEREAD_PIN.match(line)
        if pin:
            pending = pin.group(1).strip()
            continue
        timed = WEREAD_TIME.match(line)
        if timed and pending and timed.group(1) == day_s:
            pins.append(pending)
            pending = None
            if len(pins) >= 3:
                break
            continue
        if timed:
            pending = None
    return pins


def collect_weread(vault: Path, day: dt.date) -> list:
    root = vault / "📥 Inbox" / "WeRead"
    if not root.is_dir():
        return []
    items = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        pins = weread_pins_for_day(text, day)
        if not pins:
            continue
        meta = parse_frontmatter(text)
        title = meta.get("title") or path.stem
        items.append(
            new_item(
                heading=f"WeRead · **{title}**",
                wiki=wiki_rel(path, vault),
                thread=join_thread(pins[:3]),
                day=day,
                kind="weread",
            )
        )
    return items


def youtube_thread(text: str) -> str:
    idx = text.find("\n## 摘句")
    if idx < 0:
        return ""
    quotes: list[str] = []
    for line in text[idx:].splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("## 摘句"):
            break
        if stripped.startswith("- "):
            quote = stripped[2:].strip()
            if usable_quote(quote):
                quotes.append(quote)
        if len(quotes) >= 3:
            break
    return join_thread(quotes[:3])


def collect_youtube(vault: Path, day: dt.date) -> list:
    root = vault / "📥 Inbox" / "YouTube-Likes"
    items = []
    if not root.is_dir():
        return items
    for path in sorted(root.glob(f"{day.isoformat()}-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        if meta.get("generator") != "journal-youtube-likes":
            continue
        channel = meta.get("channel") or "YouTube"
        title = meta.get("title") or path.stem
        items.append(
            new_item(
                heading=f"YouTube · **{channel}** — {title}",
                wiki=wiki_rel(path, vault),
                thread=youtube_thread(text),
                day=day,
                kind="youtube",
            )
        )
    return items


def collect_day(vault: Path, day: dt.date) -> list:
    return collect_snipd(vault, day) + collect_weread(vault, day) + collect_youtube(vault, day)


def log_run(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "daily-digest.log").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def dates_between(start: dt.date, end: dt.date) -> list[dt.date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += dt.timedelta(days=1)
    return days


def build_one(vault: Path, day: dt.date) -> dict:
    items = collect_day(vault, day)
    result = {
        "date": day.isoformat(),
        "week": iso_week(day),
        "snipd": sum(1 for item in items if item.heading.startswith("Snipd")),
        "weread": sum(1 for item in items if item.heading.startswith("WeRead")),
        "youtube": sum(1 for item in items if item.heading.startswith("YouTube")),
        "added": 0,
        "wrote": False,
        "path": None,
    }
    if not items:
        return result
    week = iso_week(day)
    outcome = append_items(vault, week, items)
    result["added"] = outcome["added"]
    result["wrote"] = outcome["wrote"]
    result["path"] = outcome["path"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append new items into ISO-week intake.md")
    parser.add_argument("--date")
    parser.add_argument("--since")
    parser.add_argument("--vault")
    parser.add_argument("--force", action="store_true", help="ignored; existing items are never rewritten")
    parser.add_argument("--write-empty", action="store_true", help="ignored; empty days never create files")
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    end = dt.date.fromisoformat(args.date) if args.date else today
    start = dt.date.fromisoformat(args.since) if args.since else end
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    results = [build_one(vault, day) for day in dates_between(start, end)]
    log_run({"ran_at": dt.datetime.now(SHANGHAI).isoformat(), "results": results})
    for row in results:
        if row["wrote"]:
            print(
                f"wrote {row['path']} +{row['added']} snipd={row['snipd']} weread={row['weread']} youtube={row['youtube']}"
            )
        elif row["added"] == 0 and row["path"]:
            print(f"skip {row['date']} (already in {row['week']})")
        else:
            print(f"skip {row['date']} (nothing to index)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
