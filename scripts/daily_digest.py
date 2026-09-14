#!/usr/bin/env python3
"""Build a daily Digest from local vault sources. Does not call Hermes."""

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
MAX_QUOTES = 2
MAX_WEREAD = 3

SNIP_QUOTE = re.compile(r"^>\s+(.+?)\s*$")
WEREAD_PIN = re.compile(r"^>\s*📌\s*\[(.+?)\]")
WEREAD_TIME = re.compile(r"^>\s*⏱\s+(\d{4}-\d{2}-\d{2})")


def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


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


def unique_quotes(text: str, limit: int = MAX_QUOTES) -> list[str]:
    seen: set[str] = set()
    quotes: list[str] = []
    in_snips = False
    for line in text.splitlines():
        if line.strip() == "## Snips":
            in_snips = True
            continue
        if not in_snips:
            continue
        match = SNIP_QUOTE.match(line)
        if not match:
            continue
        quote = match.group(1).strip()
        if quote.startswith("<") or quote.startswith("—") or quote.startswith("!["):
            continue
        if quote in seen:
            continue
        seen.add(quote)
        quotes.append(quote)
        if len(quotes) >= limit:
            break
    return quotes


def wiki_rel(path: Path, vault: Path) -> str:
    rel = path.relative_to(vault).as_posix()
    if rel.endswith(".md"):
        rel = rel[:-3]
    return rel


def collect_snipd(vault: Path, day: dt.date) -> list[dict]:
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
        items.append(
            {
                "show": meta.get("show_title") or path.parent.name,
                "title": meta.get("episode_title") or path.stem,
                "snips": meta.get("snips_count") or "?",
                "quotes": unique_quotes(text),
                "wiki": wiki_rel(path, vault),
            }
        )
    return items


def collect_weread(vault: Path, day: dt.date) -> list[dict]:
    root = vault / "📥 Inbox" / "WeRead"
    if not root.is_dir():
        return []
    day_s = day.isoformat()
    items = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        lines = text.splitlines()
        highlights: list[str] = []
        pending: str | None = None
        for line in lines:
            pin = WEREAD_PIN.match(line)
            if pin:
                pending = pin.group(1).strip()
                continue
            timed = WEREAD_TIME.match(line)
            if timed and pending and timed.group(1) == day_s:
                highlights.append(pending)
                pending = None
                if len(highlights) >= MAX_WEREAD:
                    break
            elif timed:
                pending = None
        if not highlights:
            continue
        items.append(
            {
                "title": meta.get("title") or path.stem,
                "highlights": highlights,
                "wiki": wiki_rel(path, vault),
            }
        )
    return items


def collect_youtube(vault: Path, day: dt.date) -> tuple[str, list[dict]]:
    """Return (status, items) from journal-youtube-likes source notes."""
    root = vault / "📥 Inbox" / "YouTube-Likes"
    items: list[dict] = []
    if root.is_dir():
        for path in sorted(root.glob(f"{day.isoformat()}-*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            meta = parse_frontmatter(text)
            if meta.get("generator") != "journal-youtube-likes":
                continue
            quotes: list[str] = []
            in_quotes = False
            for line in text.splitlines():
                if line.strip() == "## 摘句":
                    in_quotes = True
                    continue
                if in_quotes and line.startswith("## "):
                    break
                if in_quotes and line.startswith("- "):
                    quote = line[2:].strip()
                    if quote and not quote.startswith("（"):
                        quotes.append(quote)
                    if len(quotes) >= 3:
                        break
            items.append(
                {
                    "title": meta.get("title") or path.stem,
                    "channel": meta.get("channel") or "",
                    "quotes": quotes,
                    "wiki": wiki_rel(path, vault),
                }
            )
    if items:
        return "ready", items
    return "empty", []


def iso_week(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def render(day: dt.date, snipd: list, weread: list, youtube_status: str, youtube: list) -> str:
    count = len(snipd) + len(weread) + len(youtube)
    sources = []
    if snipd:
        sources.append("snipd")
    if weread:
        sources.append("weread")
    if youtube:
        sources.append("youtube")
    src_yaml = "[" + ", ".join(sources) + "]" if sources else "[]"
    lines = [
        "---",
        f"date: {day.isoformat()}",
        "type: digest",
        f"week: {iso_week(day)}",
        f"sources: {src_yaml}",
        f"item_count: {count}",
        "generator: journal-daily-digest",
        "---",
        "",
        f"# 📋 Digest — {day.isoformat()}",
        "",
        f"**本日新增** · {iso_week(day)} · {count} 条 · 给周记当讨论燃料，不是原文替代",
        "",
    ]
    if snipd:
        lines.append("## Snipd / podcast")
        lines.append("")
        for item in snipd:
            lines.append(f"- **{item['show']}** — {item['title']}（{item['snips']} 条划线）")
            lines.append(f"  - [[{item['wiki']}]]")
            for quote in item["quotes"]:
                lines.append(f"  - {quote}")
        lines.append("")
    if weread:
        lines.append("## WeRead")
        lines.append("")
        for item in weread:
            lines.append(f"- **{item['title']}**")
            lines.append(f"  - [[{item['wiki']}]]")
            for hl in item["highlights"]:
                lines.append(f"  - {hl}")
        lines.append("")
    lines.append("## YouTube 点赞")
    lines.append("")
    if youtube_status == "empty":
        lines.append("- 本日无新增点赞。")
    else:
        for item in youtube:
            channel = item.get("channel") or "YouTube"
            lines.append(f"- **{channel}** — {item['title']}")
            if item.get("wiki"):
                lines.append(f"  - [[{item['wiki']}]]")
            for quote in item.get("quotes") or []:
                lines.append(f"  - {quote}")
    lines.append("")
    return "\n".join(lines)


def write_digest(vault: Path, day: dt.date, text: str, force: bool) -> Path:
    out_dir = vault / "📋 Digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{day.isoformat()}-Digest.md"
    if dest.exists():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if "generator: journal-daily-digest" not in existing:
            raise SystemExit(f"refusing to overwrite non-generated digest: {dest}")
        if not force:
            return dest
    dest.write_text(text, encoding="utf-8")
    return dest


def log_run(payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log = STATE_DIR / "daily-digest.log"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def dates_between(start: dt.date, end: dt.date) -> list[dt.date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += dt.timedelta(days=1)
    return days


def build_one(vault: Path, day: dt.date, force: bool, write_empty: bool) -> dict:
    snipd = collect_snipd(vault, day)
    weread = collect_weread(vault, day)
    youtube_status, youtube = collect_youtube(vault, day)
    count = len(snipd) + len(weread) + len(youtube)
    result = {
        "date": day.isoformat(),
        "snipd": len(snipd),
        "weread": len(weread),
        "youtube": youtube_status,
        "wrote": False,
        "path": None,
    }
    if count == 0 and not write_empty:
        return result
    text = render(day, snipd, weread, youtube_status, youtube)
    path = write_digest(vault, day, text, force=force)
    result["wrote"] = True
    result["path"] = str(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate daily Digest from local vault sources")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today Asia/Shanghai)")
    parser.add_argument("--since", help="Generate each day from this date through --date/today")
    parser.add_argument("--vault", help="DigitalBrain vault root")
    parser.add_argument("--force", action="store_true", help="Overwrite generated digest")
    parser.add_argument(
        "--write-empty",
        action="store_true",
        help="Write a digest even when all sources are empty",
    )
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    end = dt.date.fromisoformat(args.date) if args.date else today
    start = dt.date.fromisoformat(args.since) if args.since else end

    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    results = []
    for day in dates_between(start, end):
        results.append(build_one(vault, day, force=args.force, write_empty=args.write_empty))

    log_run(
        {
            "ran_at": dt.datetime.now(SHANGHAI).isoformat(),
            "results": results,
        }
    )
    for row in results:
        if row["wrote"]:
            print(f"wrote {row['path']} snipd={row['snipd']} weread={row['weread']} youtube={row['youtube']}")
        else:
            print(f"skip {row['date']} (no new items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
