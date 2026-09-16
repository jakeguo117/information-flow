#!/usr/bin/env python3
"""Index-style daily Digest. No Hermes. Does not invent life events."""

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

WEREAD_PIN = re.compile(r"^>\s*📌\s*\[(.+?)\]")
WEREAD_TIME = re.compile(r"^>\s*⏱\s+(\d{4}-\d{2}-\d{2})")
DISCUSSION_MARK = "\n## 讨论"


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


def wiki_rel(path: Path, vault: Path) -> str:
    rel = path.relative_to(vault).as_posix()
    return rel[:-3] if rel.endswith(".md") else rel


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
        pending: str | None = None
        hit = False
        for line in text.splitlines():
            pin = WEREAD_PIN.match(line)
            if pin:
                pending = pin.group(1).strip()
                continue
            timed = WEREAD_TIME.match(line)
            if timed and pending and timed.group(1) == day_s:
                hit = True
                break
            if timed:
                pending = None
        if not hit:
            continue
        items.append({"title": meta.get("title") or path.stem, "wiki": wiki_rel(path, vault)})
    return items


def collect_youtube(vault: Path, day: dt.date) -> list[dict]:
    root = vault / "📥 Inbox" / "YouTube-Likes"
    items: list[dict] = []
    if not root.is_dir():
        return items
    for path in sorted(root.glob(f"{day.isoformat()}-*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        meta = parse_frontmatter(text)
        if meta.get("generator") != "journal-youtube-likes":
            continue
        items.append(
            {
                "title": meta.get("title") or path.stem,
                "channel": meta.get("channel") or "",
                "wiki": wiki_rel(path, vault),
            }
        )
    return items


def iso_week(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def existing_discussion(dest: Path) -> str:
    if not dest.is_file():
        return ""
    text = dest.read_text(encoding="utf-8", errors="replace")
    idx = text.find("\n## 讨论")
    if idx < 0:
        return ""
    return text[idx + 1 :].rstrip() + "\n"


def render(day: dt.date, snipd: list, weread: list, youtube: list) -> str:
    sources = []
    if snipd:
        sources.append("snipd")
    if weread:
        sources.append("weread")
    if youtube:
        sources.append("youtube")
    count = len(snipd) + len(weread) + len(youtube)
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
        f"# Digest — {day.isoformat()}",
        "",
        f"索引 · {iso_week(day)} · {count} 条。讨论后再 append，不在这里堆原文。",
        "",
    ]
    if snipd or weread or youtube:
        lines.append("## 内容")
        lines.append("")
        for item in snipd:
            lines.append(f"- Snipd · **{item['show']}** — {item['title']}")
            lines.append(f"  - [[{item['wiki']}]]")
        for item in weread:
            lines.append(f"- WeRead · **{item['title']}**")
            lines.append(f"  - [[{item['wiki']}]]")
        for item in youtube:
            channel = item.get("channel") or "YouTube"
            lines.append(f"- YouTube · **{channel}** — {item['title']}")
            if item.get("wiki"):
                lines.append(f"  - [[{item['wiki']}]]")
        lines.append("")
    return "\n".join(lines)


def write_digest(vault: Path, day: dt.date, text: str, force: bool) -> Path:
    out_dir = vault / "📋 Digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{day.isoformat()}-Digest.md"
    discussion = ""
    if dest.exists():
        existing = dest.read_text(encoding="utf-8", errors="replace")
        if "generator: journal-daily-digest" not in existing:
            raise SystemExit(f"refusing to overwrite non-generated digest: {dest}")
        if not force:
            return dest
        discussion = existing_discussion(dest)
    body = text.rstrip() + "\n"
    if discussion:
        body = body + "\n" + discussion
        if not body.endswith("\n"):
            body += "\n"
    dest.write_text(body, encoding="utf-8")
    return dest


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


def build_one(vault: Path, day: dt.date, force: bool, write_empty: bool) -> dict:
    snipd = collect_snipd(vault, day)
    weread = collect_weread(vault, day)
    youtube = collect_youtube(vault, day)
    count = len(snipd) + len(weread) + len(youtube)
    result = {
        "date": day.isoformat(),
        "snipd": len(snipd),
        "weread": len(weread),
        "youtube": len(youtube),
        "wrote": False,
        "path": None,
    }
    dest = vault / "📋 Digests" / f"{day.isoformat()}-Digest.md"
    if count == 0 and not write_empty:
        if dest.exists():
            existing = dest.read_text(encoding="utf-8", errors="replace")
            if "generator: journal-daily-digest" in existing and "## 讨论" not in existing:
                dest.unlink()
                result["path"] = f"removed empty {dest.name}"
        return result
    text = render(day, snipd, weread, youtube)
    path = write_digest(vault, day, text, force=force)
    result["wrote"] = True
    result["path"] = str(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate index-style daily Digest")
    parser.add_argument("--date")
    parser.add_argument("--since")
    parser.add_argument("--vault")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--write-empty", action="store_true")
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    end = dt.date.fromisoformat(args.date) if args.date else today
    start = dt.date.fromisoformat(args.since) if args.since else end
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    results = [build_one(vault, day, force=args.force, write_empty=args.write_empty) for day in dates_between(start, end)]
    log_run({"ran_at": dt.datetime.now(SHANGHAI).isoformat(), "results": results})
    for row in results:
        if row["wrote"]:
            print(
                f"wrote {row['path']} snipd={row['snipd']} weread={row['weread']} youtube={row['youtube']}"
            )
        elif row.get("path"):
            print(row["path"])
        else:
            print(f"skip {row['date']} (nothing to index)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
