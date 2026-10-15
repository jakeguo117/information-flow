#!/usr/bin/env python3
"""Build one ISO week's digest.md from that week's daily digests.

Week is Asia/Shanghai. The only path this writes is:

    📋 Digests/{YYYY-Wnn}/digest.md

Daily sources, for each calendar day of that week, in this order:

    📋 Digests/daily/YYYY-MM-DD.md
    📋 Digests/YYYY-MM-DD-Digest.md

If the week has no daily digest files, fall back to:

    📋 Digests/{YYYY-Wnn}/intake.md

Usefulness groups (值得讨论的 / 可以引用的 / 可以借用的) are not inferred
from the source channel or from title keywords. An item is grouped only
when a section heading or an explicit `group:` / `分组:` tag says so.
Everything else goes to 待分组. Empty groups are the line 本周无.
IDs are numeric: T-2026W42-1, F-2026W42-1, C-2026W42-1, P-2026W42-1.

An existing digest.md is left untouched unless --force is passed.
When nothing real is found, this writes no file and exits 2.
Stdout is only the relative path and counts, never item text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
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
HASHTAG_RE = re.compile(r"#[^\s#]+")
GROUP_TAG_RE = re.compile(r"^(?:group|分组)\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)
EMPTY_LINES = {
    "没有新到的条目。",
    "这一天五个入口都没有新到的条目。",
    "（还没有条目。）",
    "（无字幕、听写也没产出句子）",
}
GROUPS = (
    ("T", "值得讨论的（thesis）"),
    ("F", "可以引用的"),
    ("C", "可以借用的"),
    ("P", "待分组"),
)
URL_KEYS = ("source_url", "url", "link")
GENERATOR = "information-flow-weekly-digest"
NO_CONTENT_EXIT = 2
EXISTS_EXIT = 3


@dataclass
class DigestItem:
    group: str
    summary: str
    link: str
    key: str
    notes: list[str] = field(default_factory=list)


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


def group_token(label: str) -> str | None:
    """Map an explicit group label. Source names are not groups."""
    text = label.strip().lower()
    if text in {"t", "thesis"} or text.startswith("值得讨论"):
        return "T"
    if text in {"f"} or text.startswith("可以引用"):
        return "F"
    if text in {"c"} or text.startswith("可以借用"):
        return "C"
    if text in {"p"} or text.startswith("待分组"):
        return "P"
    return None


def group_for_heading(title: str) -> str | None:
    return group_token(title)


def clean_summary(body: str) -> str:
    """Keep 「来源 · 频道 — 标题」. Drop hashtags and clash-prone ｜."""
    text = WIKI_RE.sub("", body)
    text = MD_LINK_RE.sub("", text)
    text = BARE_URL_RE.sub("", text)
    text = text.replace("**", "")
    text = re.sub(r"^\s*[—–]\s*", "", text)
    text = text.replace("｜", " / ")
    text = HASHTAG_RE.sub(" ", text)
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) > 180:
        text = text[:177].rstrip() + "…"
    return text


def _bullet_url(body: str) -> str:
    link_match = MD_LINK_RE.search(body)
    if link_match:
        return link_match.group(2)
    bare = BARE_URL_RE.search(body)
    if bare:
        return bare.group(0).rstrip(".,，。")
    return ""


def _is_real_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def inbox_url(vault: Path | None, wiki: str) -> str:
    """URL from an inbox note's frontmatter, when that note is a real file."""
    if vault is None or not wiki.startswith("📥 Inbox/"):
        return ""
    if ".." in Path(wiki).parts:
        return ""
    raw = vault / f"{wiki}.md"
    if not _is_real_file(raw):
        return ""
    try:
        raw.resolve().relative_to(vault.resolve())
    except ValueError:
        return ""
    meta = weekly_intake.parse_frontmatter(raw.read_text(encoding="utf-8", errors="replace"))
    for key in URL_KEYS:
        value = meta.get(key, "").strip()
        if value.startswith(("http://", "https://")):
            return value
    return ""


def render_link(wiki: str, url: str) -> str:
    parts: list[str] = []
    if wiki:
        parts.append(f"[[{wiki}]]")
    if url:
        parts.append(f"[原文]({url})")
    return " ".join(parts)


def _child_text(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped[2:].strip()
    return stripped


def parse_digest_markdown(text: str, vault: Path | None = None) -> list[DigestItem]:
    heading_group: str | None = None
    items: list[DigestItem] = []
    pending: dict | None = None

    def flush() -> None:
        nonlocal pending
        if pending is None:
            return
        item = _finish_item(pending, vault)
        pending = None
        if item is not None:
            items.append(item)

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            flush()
            heading_group = group_for_heading(line[3:].strip())
            continue
        if line.startswith("- "):
            flush()
            pending = _start_bullet(line, heading_group)
            continue
        if pending is not None and (raw.startswith("  ") or raw.startswith("\t")):
            _attach_child(pending, _child_text(line))
    flush()
    return items


def _start_bullet(line: str, heading_group: str | None) -> dict | None:
    body = CHECKBOX_RE.sub("", line[2:].strip())
    if not body or body in EMPTY_LINES or body.startswith("没有新到的条目"):
        return None
    wiki_match = WIKI_RE.search(body)
    wiki = wiki_match.group(1).strip() if wiki_match else ""
    url = _bullet_url(body)
    summary = clean_summary(body)
    if not summary and not wiki and not url:
        return None
    return {
        "group": heading_group,
        "summary": summary,
        "wiki": wiki,
        "url": url,
        "notes": [],
    }


def _attach_child(pending: dict, text: str) -> None:
    if not text or text in EMPTY_LINES or text.startswith("没有新到的条目") or text.startswith("摄入："):
        return
    tag = GROUP_TAG_RE.match(text)
    if tag:
        mapped = group_token(tag.group(1))
        if mapped:
            pending["group"] = mapped
            return
    pending["notes"].append(text)


def _finish_item(pending: dict, vault: Path | None) -> DigestItem | None:
    wiki = pending["wiki"]
    url = pending["url"] or inbox_url(vault, wiki)
    summary = pending["summary"]
    if not summary:
        summary = Path(wiki).name if wiki else url
    if not summary or (not wiki and not url):
        return None
    group = pending["group"] or "P"
    key = wiki or url
    return DigestItem(
        group=group,
        summary=summary,
        link=render_link(wiki, url),
        key=key,
        notes=list(pending["notes"]),
    )


def parse_intake(text: str, vault: Path | None = None) -> list[DigestItem]:
    items: list[DigestItem] = []
    for entry in weekly_intake.parse_items(text):
        summary = clean_summary(entry.briefing_line)
        wiki = entry.wiki.strip()
        if not summary or not wiki or summary in EMPTY_LINES:
            continue
        url = inbox_url(vault, wiki)
        items.append(
            DigestItem(group="P", summary=summary, link=render_link(wiki, url), key=wiki)
        )
    return items


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
            items.extend(parse_digest_markdown(text, vault))
    else:
        source = "intake"
        intake = weekly_intake.intake_path(vault, f"{year}-W{week:02d}")
        if _is_real_file(intake):
            text = intake.read_text(encoding="utf-8", errors="replace")
            items.extend(parse_intake(text, vault))
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
        lines.append(f"## {title}")
        lines.append("")
        grouped = [item for item in items if item.group == prefix]
        if not grouped:
            lines.append("本周无")
            lines.append("")
            continue
        for number, item in enumerate(grouped, start=1):
            lines.append(f"- **{prefix}-{token}-{number}**｜{item.summary}｜{item.link}")
            for note in item.notes:
                lines.append(f"  - {note}")
            if prefix == "T":
                lines.append("  - 我的看法：")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def digest_path(vault: Path, week: str) -> Path:
    return vault / "📋 Digests" / week / "digest.md"


def build_week(vault: Path, week: str, force: bool = False) -> int:
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1
    try:
        year, week_no = parse_week(week)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    canonical = f"{year}-W{week_no:02d}"
    dest = digest_path(vault, canonical)
    if dest.exists() and not force:
        print(f"已有 digest，不覆盖：{dest.relative_to(vault).as_posix()}（加 --force 才重写）", file=sys.stderr)
        return EXISTS_EXIT
    items, source = collect_items(vault, year, week_no)
    if not items:
        print(f"本周 digest 还没有可写入的内容：{canonical}", file=sys.stderr)
        return NO_CONTENT_EXIT
    text = render_digest(canonical, items)
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
    parser.add_argument("--force", action="store_true", help="overwrite an existing digest.md")
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
    return build_week(vault, week, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
