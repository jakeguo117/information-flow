#!/usr/bin/env python3
"""Weekly intake.md helpers. No Hermes. Does not invent life events."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

GENERATOR = "journal-weekly-intake"
DIGESTS_DIR = "📋 Digests"
ITEM_START = re.compile(r"^- \[([ xX])\] (.+)$")
WIKI = re.compile(r"\[\[(.+?)\]\]")
SENTENCE_SPLIT = re.compile(r"(?<=[。！？.!?])\s+")
WEEK_DIR = re.compile(r"^(\d{4})-W(\d{2})$")


def iso_week(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def intake_path(vault: Path, week: str) -> Path:
    return vault / DIGESTS_DIR / week / "intake.md"


def list_intake_weeks(vault: Path) -> list[str]:
    root = vault / DIGESTS_DIR
    if not root.is_dir():
        return []
    weeks: list[str] = []
    for child in root.iterdir():
        if child.is_dir() and WEEK_DIR.match(child.name) and (child / "intake.md").is_file():
            weeks.append(child.name)
    weeks.sort()
    return weeks


def resolve_intake(vault: Path, today: dt.date) -> Path | None:
    """Current ISO week if that intake exists, else the newest existing week."""
    current = intake_path(vault, iso_week(today))
    if current.is_file():
        return current
    weeks = list_intake_weeks(vault)
    if not weeks:
        return None
    return intake_path(vault, weeks[-1])


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


def split_sentences(text: str, limit: int = 3) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    parts = [p.strip() for p in SENTENCE_SPLIT.split(cleaned) if p.strip()]
    if not parts:
        return [cleaned[:240]]
    return parts[:limit]


def join_thread(parts: list[str]) -> str:
    text = " ".join(parts).strip()
    if len(text) > 480:
        text = text[:477].rstrip() + "…"
    return text


def usable_quote(line: str) -> bool:
    text = re.sub(r"\s+", " ", line).strip()
    if not (12 <= len(text) <= 180):
        return False
    if text.endswith((",", "，", "、")):
        return False
    if text[0].isascii() and text[0].islower():
        return False
    return True


@dataclass
class IntakeItem:
    checked: bool
    heading: str
    wiki: str
    extra: list[str] = field(default_factory=list)

    @property
    def briefing_line(self) -> str:
        return self.heading.replace("**", "").strip()


def parse_items(text: str) -> list[IntakeItem]:
    idx = text.find("\n## 条目")
    if idx < 0:
        if text.lstrip().startswith("## 条目"):
            block = text
        else:
            return []
    else:
        block = text[idx + 1 :]
    start = block.find("## 条目")
    block = block[start + len("## 条目") :]
    nxt = re.search(r"\n## ", block)
    if nxt:
        block = block[: nxt.start()]

    items: list[IntakeItem] = []
    heading = ""
    checked = False
    children: list[str] = []

    def flush() -> None:
        nonlocal heading, children
        if not heading:
            return
        wiki = ""
        extra: list[str] = []
        for child in children:
            if not wiki:
                match = WIKI.search(child)
                if match:
                    wiki = match.group(1)
                    continue
            extra.append(child)
        items.append(IntakeItem(checked=checked, heading=heading, wiki=wiki, extra=extra))
        heading = ""
        children = []

    for raw in block.splitlines():
        match = ITEM_START.match(raw)
        if match:
            flush()
            checked = match.group(1).lower() == "x"
            heading = match.group(2).strip()
            continue
        if heading and (raw.startswith("  ") or raw.startswith("\t")):
            children.append(raw.rstrip())
    flush()
    return items


def sink_checked(items: list[IntakeItem]) -> list[IntakeItem]:
    open_items = [item for item in items if not item.checked]
    done_items = [item for item in items if item.checked]
    return open_items + done_items


def render_briefing(items: list[IntakeItem]) -> list[str]:
    open_items = [item for item in items if not item.checked]
    lines = ["## Briefing", ""]
    if not open_items:
        lines.append("本周未讨论条目已清空。")
        lines.append("")
        return lines
    for item in open_items:
        lines.append(f"- {item.briefing_line}")
    lines.append("")
    return lines


def render_item(item: IntakeItem) -> list[str]:
    mark = "x" if item.checked else " "
    lines = [f"- [{mark}] {item.heading}"]
    if item.wiki:
        lines.append(f"  - [[{item.wiki}]]")
    lines.extend(item.extra)
    lines.append("")
    return lines


def render_intake(week: str, items: list[IntakeItem]) -> str:
    items = sink_checked(items)
    open_count = sum(1 for item in items if not item.checked)
    lines = [
        "---",
        f"week: {week}",
        "type: weekly-intake",
        f"item_count: {len(items)}",
        f"open_count: {open_count}",
        f"generator: {GENERATOR}",
        "---",
        "",
        f"# Intake — {week}",
        "",
    ]
    lines.extend(render_briefing(items))
    lines.append("## 条目")
    lines.append("")
    if not items:
        lines.append("（还没有条目。）")
        lines.append("")
    else:
        for item in items:
            lines.extend(render_item(item))
    return "\n".join(lines).rstrip() + "\n"


def load_intake(dest: Path) -> list[IntakeItem]:
    if not dest.is_file():
        return []
    text = dest.read_text(encoding="utf-8", errors="replace")
    if GENERATOR not in text:
        raise SystemExit(f"refusing to overwrite non-generated intake: {dest}")
    return parse_items(text)


def write_intake(dest: Path, week: str, items: list[IntakeItem]) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_intake(week, items), encoding="utf-8")
    return dest


def append_items(vault: Path, week: str, new_items: list[IntakeItem]) -> dict:
    dest = intake_path(vault, week)
    result = {"week": week, "path": str(dest), "added": 0, "wrote": False}
    if not new_items and not dest.exists():
        return result
    existing = load_intake(dest)
    seen = {item.wiki for item in existing if item.wiki}
    added = 0
    for item in new_items:
        if item.wiki and item.wiki in seen:
            continue
        existing.append(item)
        if item.wiki:
            seen.add(item.wiki)
        added += 1
    result["added"] = added
    if added == 0 and dest.exists():
        return result
    if not existing:
        return result
    write_intake(dest, week, existing)
    result["wrote"] = True
    return result


def refresh_intake(vault: Path, week: str) -> dict:
    dest = intake_path(vault, week)
    result = {"week": week, "path": str(dest), "wrote": False}
    if not dest.exists():
        return result
    items = load_intake(dest)
    write_intake(dest, week, items)
    result["wrote"] = True
    result["open_count"] = sum(1 for item in items if not item.checked)
    result["item_count"] = len(items)
    return result


def new_item(heading: str, wiki: str, thread: str, day: dt.date, kind: str) -> IntakeItem:
    extra: list[str] = []
    if thread:
        extra.append(f"  - {thread}")
    extra.append(f"  - 摄入：{day.isoformat()} · {kind}")
    return IntakeItem(checked=False, heading=heading, wiki=wiki, extra=extra)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve the current weekly intake.md")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--date", help="YYYY-MM-DD (default: today Asia/Shanghai)")
    args = parser.parse_args(argv)
    vault = Path(args.vault).expanduser()
    today = (
        dt.date.fromisoformat(args.date)
        if args.date
        else dt.datetime.now(ZoneInfo("Asia/Shanghai")).date()
    )
    dest = resolve_intake(vault, today)
    if dest is None:
        print("no weekly intake", file=sys.stderr)
        return 1
    print(dest.relative_to(vault).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
