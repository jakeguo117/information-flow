#!/usr/bin/env python3
"""Build one ISO week's digest.md from that week's daily digests.

Week is Asia/Shanghai. The only path this writes is:

    📋 Digests/{YYYY-Wnn}/digest.md

Daily sources, for each calendar day of that week, in this order:

    📋 Digests/daily/YYYY-MM-DD.md
    📋 Digests/YYYY-MM-DD-Digest.md

If the week has no daily digest files, fall back to:

    📋 Digests/{YYYY-Wnn}/intake.md

Usefulness groups come from an explicit `group:` / `分组:` tag, a group
heading, or the fixed source-type table in daily_takeaway.SECTION_GROUP
(Snipd/WeRead F, YouTube T, X/Instagram C). Anything else is 待分组.
Empty groups are the line 本周无.
IDs are numeric: T-2026W42-1, F-2026W42-1, C-2026W42-1, P-2026W42-1.

A generated file carries an HTML comment with the generator version and a
sha256 of the body. A later run may refresh it only while that marker is
present and the body hash still matches, which means nobody hand-edited it
and 「我的看法：」 is still empty. Otherwise the file is left in place and the
run exits 3. With only --vault, the current ISO week and the previous ISO
week are both built. When nothing real is found, this writes no file and
exits 2. Stdout is only the relative path and counts, never item text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_takeaway  # noqa: E402
import weekly_intake  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
WEEK_RE = re.compile(r"^(\d{4})-W(0[1-9]|[1-4][0-9]|5[0-3])$")
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
GENERATOR_VERSION = "1"
NO_CONTENT_EXIT = 2
EXISTS_EXIT = 3
DIGEST_MARKER_PATTERN = r"(?:\r?\n)?<!-- information-flow-weekly-digest generator=(\S+) sha256=([0-9a-f]{64}) -->\s*\Z"
DIGEST_MARKER_RE = re.compile(DIGEST_MARKER_PATTERN)


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
    """Map an explicit group label. Source names are handled separately."""
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
    explicit = group_token(title)
    if explicit:
        return explicit
    return daily_takeaway.SECTION_GROUP.get(title.strip())


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
    text = raw.read_text(encoding="utf-8", errors="replace")
    meta = weekly_intake.parse_frontmatter(text)
    for key in URL_KEYS:
        value = meta.get(key, "").strip()
        if value.startswith(("http://", "https://")):
            return value
    for value in meta.values():
        cleaned = value.strip()
        if cleaned.startswith(("http://", "https://")):
            return cleaned
    body = text.split("\n---", 2)[-1] if text.startswith("---") else text
    for line in body.splitlines():
        found = BARE_URL_RE.search(line)
        if not found:
            continue
        url = found.group(0).rstrip(".,，。)")
        if url.startswith(("http://", "https://")):
            return url
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


def previous_week(week: str) -> str:
    year, week_no = parse_week(week)
    monday = dt.date.fromisocalendar(year, week_no, 1)
    return week_from_date(monday - dt.timedelta(days=1))


def stamp(body: str) -> str:
    if not body.endswith("\n"):
        body += "\n"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return (
        body
        + f"<!-- information-flow-weekly-digest generator={GENERATOR_VERSION} sha256={digest} -->\n"
    )


def split_generated(text: str) -> tuple[str, str | None]:
    """Return the body and its recorded sha256, or (text, None) when unmarked."""
    match = DIGEST_MARKER_RE.search(text)
    if not match:
        return text, None
    body = text[: match.start()]
    if not body.endswith("\n"):
        body += "\n"
    return body, match.group(2)


def opinion_filled(text: str) -> bool:
    """True when a 「我的看法：」 line has text after it."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "我的看法：" in line:
            after = line.split("我的看法：", 1)[1]
        elif "我的看法:" in line:
            after = line.split("我的看法:", 1)[1]
        else:
            continue
        if after.strip():
            return True
        if index + 1 < len(lines) and lines[index + 1].startswith((" ", "\t")) and lines[index + 1].strip():
            return True
    return False


def refresh_allowed(existing: str) -> bool:
    body, recorded = split_generated(existing)
    if recorded is None:
        return False
    if hashlib.sha256(body.encode("utf-8")).hexdigest() != recorded:
        return False
    if opinion_filled(body):
        return False
    return True


def combine_codes(codes: list[int]) -> int:
    if any(code == 1 for code in codes):
        return 1
    if any(code == 0 for code in codes):
        return 0
    if any(code == EXISTS_EXIT for code in codes):
        return EXISTS_EXIT
    return NO_CONTENT_EXIT


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
    dest = digest_path(vault, canonical)
    existing = dest.read_text(encoding="utf-8") if _is_real_file(dest) else None
    if existing is not None and not refresh_allowed(existing):
        print(f"已有 digest，不覆盖：{dest.relative_to(vault).as_posix()}", file=sys.stderr)
        return EXISTS_EXIT
    items, source = collect_items(vault, year, week_no)
    if not items:
        print(f"本周 digest 还没有可写入的内容：{canonical}", file=sys.stderr)
        return NO_CONTENT_EXIT
    text = stamp(render_digest(canonical, items))
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
    parser.add_argument(
        "--also-previous",
        action="store_true",
        help="also build the previous ISO week; implied when --week and --date are omitted",
    )
    args = parser.parse_args(argv)
    if args.week and args.date:
        print("pass only one of --week and --date", file=sys.stderr)
        return 1
    vault = Path(args.vault).expanduser()
    try:
        if args.week:
            weeks = [f"{parse_week(args.week)[0]}-W{parse_week(args.week)[1]:02d}"]
            if args.also_previous:
                weeks.append(previous_week(weeks[0]))
        elif args.date:
            weeks = [week_from_date(dt.date.fromisoformat(args.date))]
            if args.also_previous:
                weeks.append(previous_week(weeks[0]))
        else:
            weeks = [week_from_date(shanghai_today())]
            weeks.append(previous_week(weeks[0]))
    except ValueError as exc:
        print(str(exc) if args.week else f"invalid date: {args.date}", file=sys.stderr)
        return 1
    ordered: list[str] = []
    for week in weeks:
        if week not in ordered:
            ordered.append(week)
    return combine_codes([build_week(vault, week) for week in ordered])


if __name__ == "__main__":
    raise SystemExit(main())
