#!/usr/bin/env python3
"""Pure inbox-0.1 parsers for synthetic Inbox notes.

Turns note text into Source and Input dicts. No git, no network, and no
DigitalBrain writes. Callers (later, the index) supply receive times.

Snip ``received_at`` (N1)
-------------------------
A Snipd episode is one file, so the file's first commit is not the snip's
receive time. For each snip uuid, in order:

1. ``ParseContext.received_at_lookup(snip_uuid)`` — the commit time where
   that uuid first appears. Return None when that commit is unknown.
   This module does not run git.
2. ``ParseContext.item_first_seen_at(snip_uuid)`` — when the index first
   saw that snip.
3. ``ParseContext.received_at`` — a receive time the caller already resolved.
4. ``ParseContext.first_seen_at`` — note-level fallback. This can equal
   ``Source.first_seen_at``. Pass (1) or (2) for a new snip on an old episode.

X and Instagram notes have no bookmark or save time. ``time_basis`` is
``first_seen`` and ``captured_at`` is set only when the caller supplies a
first-seen time. ``origin=historical_import`` with no capture time uses
``time_basis=unknown`` and leaves ``source_week`` empty.

``parse_frontmatter`` follows ``weekly_intake.parse_frontmatter``. YouTube
摘句 and WeRead 📌 lines follow ``daily_digest`` and also keep each WeRead
highlight as its own Input. Those retired scripts stay in the tree until a
later deletion task.

Parsers raise ``NoteParseError`` when the text is not a usable note.
Context and clock errors stay ``ValueError``.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

SCHEMA_VERSION = "inbox-0.1"
HK = ZoneInfo("Asia/Hong_Kong")

PLATFORMS = ("youtube", "snipd", "weread", "x", "instagram", "thought")
ORIGINS = ("collected", "historical_import")
TIME_BASES = ("platform", "first_seen", "unknown")

# utm_* plus the same class of click identifiers. YouTube ``v`` is not here.
_TRACKING_KEYS = frozenset(
    {
        "fbclid",
        "gclid",
        "gclsrc",
        "dclid",
        "msclkid",
        "igshid",
        "igsh",
        "mc_cid",
        "mc_eid",
        "yclid",
        "twclid",
        "ttclid",
        "si",
        "_ga",
        "ref_src",
    }
)

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_CLOCK_RE = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:[ T](?P<hms>\d{2}:\d{2}(?::\d{2})?))?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2})?"
)
_SNIP_URL_RE = re.compile(
    r"https?://[^\s)]+/snip/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)
_STATUS_URL_RE = re.compile(r"/status/(\d+)")
_STATUS_FILE_RE = re.compile(r"-(\d{6,})$")
_IG_CODE_RE = re.compile(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")
_YT_EMPTY_QUOTE = "（无字幕、听写也没产出句子）"
_VERBATIM_MARK = "\n---\n原话:\n"
_SNIP_TIME_KEYS = ("snip_created_at", "created_at", "noted_at", "snip_time")


@dataclass(frozen=True)
class ParseContext:
    """Index times supplied by the caller. See the module docstring for N1."""

    path: str
    first_seen_at: str | None = None
    received_at: str | None = None
    received_at_lookup: Callable[[str], str | None] | None = None
    item_first_seen_at: Callable[[str], str | None] | None = None
    origin: str = "collected"
    content_revision: int = 1
    canonical_url: str | None = None

    def __post_init__(self) -> None:
        if not self.path or not str(self.path).strip():
            raise ValueError("path is required")
        if self.origin not in ORIGINS:
            raise ValueError(f"origin must be one of {ORIGINS}")
        if self.content_revision < 1:
            raise ValueError("content_revision starts at 1")


def normalize_content(text: str) -> str:
    """NFC, strip, collapse whitespace. Do not lowercase or drop punctuation."""
    normalized = unicodedata.normalize("NFC", text or "")
    normalized = normalized.strip()
    return re.sub(r"\s+", " ", normalized)


def content_fingerprint(text: str) -> str:
    """sha256 of normalized content only, lowercase hex."""
    return hashlib.sha256(normalize_content(text).encode("utf-8")).hexdigest()


def event_key_for(
    platform: str,
    event_type: str,
    content: str,
    external_item_id: str | None,
) -> str:
    """Platform event id, or the platform/type/content sha256 when there is none."""
    if external_item_id:
        return external_item_id
    blob = f"{platform}\n{event_type}\n{normalize_content(content)}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def source_id_for(
    platform: str,
    external_content_id: str | None,
    canonical_url: str,
) -> str:
    if external_content_id:
        return f"src-{platform}-{external_content_id}"
    digest = hashlib.sha1(canonical_url.encode("utf-8")).hexdigest()[:12]
    return f"src-{platform}-u{digest}"


def input_id_for(platform: str, source_id: str, event_key: str) -> str:
    digest = hashlib.sha1(f"{source_id}|{event_key}".encode("utf-8")).hexdigest()[:12]
    return f"in-{platform}-{digest}"


def canonicalize_url(url: str) -> str:
    """Drop utm_* and other click ids. Keep identity params such as YouTube ``v``."""
    raw = (url or "").strip()
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return raw
    kept: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in _TRACKING_KEYS:
            continue
        kept.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), parts.fragment))


def parse_frontmatter(text: str) -> dict[str, str]:
    """Flat ``key: value`` frontmatter. List items are skipped.

    Line rules match ``weekly_intake.parse_frontmatter``.
    """
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


def parse_time(raw: str | None) -> datetime | None:
    """Parse a date or datetime. Naive clocks are Asia/Hong_Kong.

    A media offset such as ``00:12:03`` has no date and returns None.
    ``北京时间`` / ``UTC+8`` labels do not change the clock; both are +08.
    """
    if raw is None:
        return None
    match = _CLOCK_RE.search(raw.strip())
    if not match:
        return None
    hms = match.group("hms") or "00:00:00"
    if hms.count(":") == 1:
        hms = hms + ":00"
    tz = match.group("tz") or "+08:00"
    if tz == "Z":
        tz = "+00:00"
    return datetime.fromisoformat(f"{match.group('date')}T{hms}{tz}")


def format_hk(moment: datetime) -> str:
    return moment.astimezone(HK).isoformat(timespec="seconds")


def format_z(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def source_week_for(captured_at: str | None, time_basis: str) -> str | None:
    if time_basis == "unknown" or not captured_at:
        return None
    moment = parse_time(captured_at)
    if moment is None:
        return None
    iso = moment.astimezone(HK).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


class NoteParseError(ValueError):
    """This text is not a usable note.

    ``inbox_index`` skips that file and continues. A bad ``ParseContext``
    or a bad received-at timestamp stays a plain ``ValueError`` and still
    aborts the run.
    """


def _note_time(raw: str | None) -> datetime | None:
    """``parse_time`` for a clock written inside the note.

    A bad clock in the note (``2026-13-45``) is a ``NoteParseError`` so the
    index skips that one file. Context clocks (received-at map, first-seen)
    still use ``parse_time`` / ``_must_hk`` and still abort the run.
    """
    try:
        return parse_time(raw)
    except ValueError as exc:
        raise NoteParseError(f"bad date in note: {raw!r}") from exc


def parse_note(text: str, platform: str, ctx: ParseContext) -> dict:
    """Parse one note into ``{"source": ..., "inputs": [...]}``."""
    if platform not in PLATFORMS:
        raise ValueError(f"unsupported platform {platform!r}")
    parser = {
        "youtube": parse_youtube,
        "snipd": parse_snipd,
        "weread": parse_weread,
        "x": parse_x,
        "instagram": parse_instagram,
        "thought": parse_thought,
    }[platform]
    return parser(_newlines(text), ctx)


def parse_youtube(text: str, ctx: ParseContext) -> dict:
    text = _newlines(text)
    meta = parse_frontmatter(text)
    source_url = ctx.canonical_url or meta.get("source_url") or _first_http(text)
    if not source_url:
        raise NoteParseError("youtube note has no source_url")
    canonical = canonicalize_url(source_url)
    video_id = _blank_none(meta.get("video_id")) or _query_value(canonical, "v")
    if not video_id:
        raise NoteParseError("youtube note has no video_id")
    like = _note_time(meta.get("like_at"))
    if like is not None:
        captured: str | None = format_hk(like)
        basis = "platform"
        external_item: str | None = f"{video_id}@{format_z(like)}"
    else:
        # Schema leaves ``video_id@like_at`` unspecified when like_at is absent.
        captured, basis = _first_seen_capture(ctx, video_id)
        external_item = None
    quotes = _youtube_quotes(text)
    transcript = (meta.get("transcript") or "").strip().lower()
    if quotes and transcript not in {"", "none"}:
        completeness, missing, content = "full", None, "\n".join(quotes)
    elif quotes:
        completeness, missing, content = "excerpt", "transcript: none", "\n".join(quotes)
    else:
        completeness, missing, content = "metadata_only", "transcript: none", ""
    published = _note_time(meta.get("published_at") or meta.get("publish_date"))
    source = _source(
        ctx,
        platform="youtube",
        external_content_id=video_id,
        canonical_url=canonical,
        title=_blank_none(meta.get("title")),
        author=_blank_none(meta.get("channel") or meta.get("author")),
        published_at=format_hk(published) if published else None,
    )
    item = _input(
        ctx,
        platform="youtube",
        source_id=source["source_id"],
        external_item_id=external_item,
        event_type="like",
        content=content,
        captured_at=captured,
        time_basis=basis,
        source_published_at=source["published_at"],
        completeness=completeness,
        missing_reason=missing,
        anchor="摘句",
    )
    return {"source": source, "inputs": [item]}


def parse_snipd(text: str, ctx: ParseContext) -> dict:
    text = _newlines(text)
    meta = parse_frontmatter(text)
    episode_url = ctx.canonical_url or meta.get("episode_url") or meta.get("url") or ""
    if not episode_url:
        raise NoteParseError("snipd note has no episode_url")
    canonical = canonicalize_url(episode_url)
    episode_id = _blank_none(meta.get("episode_id") or meta.get("episode_uuid"))
    if episode_id is None:
        found = _UUID_RE.findall(canonical)
        episode_id = found[-1] if found else None
    if not episode_id:
        raise NoteParseError("snipd note has no episode uuid")
    published = _note_time(meta.get("episode_publish_date") or meta.get("published_at"))
    source = _source(
        ctx,
        platform="snipd",
        external_content_id=episode_id,
        canonical_url=canonical,
        title=_blank_none(meta.get("episode_title") or meta.get("title")),
        author=_blank_none(meta.get("show_author") or meta.get("author")),
        published_at=format_hk(published) if published else None,
    )
    inputs = []
    for section in _snip_sections(text):
        snip_id = _snip_id(section)
        own = _snip_own_time(section)
        quote = _snip_quote(section)
        if own is not None:
            captured: str | None = format_hk(own)
            basis = "platform"
        else:
            # No snip clock: do not reuse last_snip_date or the episode time.
            captured, basis = _first_seen_capture(ctx, snip_id)
        if quote:
            completeness, missing = "full", None
        else:
            completeness, missing = "metadata_only", "snip: empty"
        inputs.append(
            _input(
                ctx,
                platform="snipd",
                source_id=source["source_id"],
                external_item_id=snip_id,
                event_type="snip",
                content=quote,
                captured_at=captured,
                time_basis=basis,
                source_published_at=source["published_at"],
                completeness=completeness,
                missing_reason=missing,
                anchor=snip_id or "snip",
            )
        )
    return {"source": source, "inputs": inputs}


def parse_weread(text: str, ctx: ParseContext) -> dict:
    text = _newlines(text)
    meta = parse_frontmatter(text)
    book_id = _blank_none(meta.get("bookId") or meta.get("book_id"))
    if not book_id:
        raise NoteParseError("weread note has no bookId")
    raw_url = ctx.canonical_url or meta.get("source_url") or meta.get("url") or meta.get("book_url")
    if not raw_url:
        raw_url = f"https://weread.qq.com/web/reader/{book_id}"
    canonical = canonicalize_url(raw_url)
    published = _note_time(meta.get("published_at") or meta.get("publish_date"))
    source = _source(
        ctx,
        platform="weread",
        external_content_id=book_id,
        canonical_url=canonical,
        title=_blank_none(meta.get("title")),
        author=_blank_none(meta.get("author")),
        published_at=format_hk(published) if published else None,
    )
    inputs = []
    for highlight in _weread_highlights(text):
        block_id = highlight["block_id"]
        when = highlight["time"]
        quote = highlight["text"]
        if when is not None:
            captured: str | None = format_hk(when)
            basis = "platform"
        else:
            captured, basis = _first_seen_capture(ctx, block_id)
        if quote:
            completeness, missing = "full", None
        else:
            completeness, missing = "metadata_only", "highlight: empty"
        inputs.append(
            _input(
                ctx,
                platform="weread",
                source_id=source["source_id"],
                external_item_id=block_id,
                event_type="highlight",
                content=quote,
                captured_at=captured,
                time_basis=basis,
                source_published_at=source["published_at"],
                completeness=completeness,
                missing_reason=missing,
                anchor=block_id or "highlight",
            )
        )
    return {"source": source, "inputs": inputs}


def parse_x(text: str, ctx: ParseContext) -> dict:
    return _parse_social(text, ctx, platform="x", event_type="bookmark")


def parse_instagram(text: str, ctx: ParseContext) -> dict:
    return _parse_social(text, ctx, platform="instagram", event_type="save")


def parse_thought(text: str, ctx: ParseContext) -> dict:
    text = _newlines(text)
    meta = parse_frontmatter(text)
    thought_id = _blank_none(meta.get("id"))
    if not thought_id:
        raise NoteParseError("thought note has no id")
    if _VERBATIM_MARK not in text:
        raise NoteParseError("thought file has no 原话 marker")
    verbatim = text.split(_VERBATIM_MARK, 1)[1]
    raw_url = ctx.canonical_url or meta.get("canonical_url") or meta.get("url")
    if not raw_url:
        raw_url = f"thought://{thought_id}"
    canonical = canonicalize_url(raw_url) if raw_url.startswith(("http://", "https://")) else raw_url
    captured_at = _note_time(meta.get("captured_at"))
    if captured_at is not None:
        captured: str | None = format_hk(captured_at)
        basis = "platform"
    else:
        captured, basis = _first_seen_capture(ctx, thought_id)
    if ctx.origin == "historical_import" and captured is None:
        basis = "unknown"
    source = _source(
        ctx,
        platform="thought",
        external_content_id=None,
        canonical_url=canonical,
        title=_blank_none(meta.get("title")),
        author=_blank_none(meta.get("author")),
        published_at=None,
    )
    if normalize_content(verbatim):
        completeness, missing = "full", None
    else:
        completeness, missing = "missing", "verbatim: empty"
    item = _input(
        ctx,
        platform="thought",
        source_id=source["source_id"],
        external_item_id=thought_id,
        event_type="thought",
        content=verbatim,
        captured_at=captured,
        time_basis=basis,
        source_published_at=None,
        completeness=completeness,
        missing_reason=missing,
        anchor=thought_id,
    )
    return {"source": source, "inputs": [item]}


def _parse_social(text: str, ctx: ParseContext, *, platform: str, event_type: str) -> dict:
    text = _newlines(text)
    fields = _labeled_fields(text)
    heading = _heading(text)
    if platform == "x":
        content_id = _status_id(fields.get("原文链接", ""), ctx.path)
        raw_url = ctx.canonical_url or fields.get("原文链接")
        if not content_id:
            raise NoteParseError("x note has no status id")
        if not raw_url:
            raw_url = f"https://x.com/i/status/{content_id}"
    else:
        raw_url = ctx.canonical_url or fields.get("原文链接")
        content_id = _ig_shortcode(raw_url or "", ctx.path)
        if not content_id:
            raise NoteParseError("instagram note has no shortcode")
        if not raw_url:
            raw_url = f"https://www.instagram.com/p/{content_id}"
    canonical = canonicalize_url(raw_url)
    author = _blank_none(fields.get("作者")) or _author_from_heading(heading)
    title = _blank_none(fields.get("标题")) or _title_from_heading(heading)
    published = _note_time(fields.get("视频发布时间") or fields.get("发布时间"))
    summary = _section(text, "摘要")
    takeaways = _section(text, "Takeaways")
    if summary:
        content, completeness, missing = summary, "full", None
    elif takeaways:
        content, completeness, missing = takeaways, "excerpt", "text: summary missing"
    else:
        content, completeness, missing = "", "metadata_only", "text: none"
    if ctx.origin == "historical_import":
        captured, basis = None, "unknown"
    else:
        captured, basis = _first_seen_capture(ctx, content_id)
    source = _source(
        ctx,
        platform=platform,
        external_content_id=content_id,
        canonical_url=canonical,
        title=title,
        author=author,
        published_at=format_hk(published) if published else None,
    )
    item = _input(
        ctx,
        platform=platform,
        source_id=source["source_id"],
        external_item_id=content_id,
        event_type=event_type,
        content=content,
        captured_at=captured,
        time_basis=basis,
        source_published_at=source["published_at"],
        completeness=completeness,
        missing_reason=missing,
        anchor=content_id,
    )
    return {"source": source, "inputs": [item]}


def _source(
    ctx: ParseContext,
    *,
    platform: str,
    external_content_id: str | None,
    canonical_url: str,
    title: str | None,
    author: str | None,
    published_at: str | None,
) -> dict:
    seen = parse_time(ctx.first_seen_at) if ctx.first_seen_at else None
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id_for(platform, external_content_id, canonical_url),
        "platform": platform,
        "external_content_id": external_content_id,
        "canonical_url": canonical_url,
        "title": title,
        "author": author,
        "published_at": published_at,
        "raw_refs": [ctx.path],
        "content_revision": ctx.content_revision,
        "first_seen_at": format_hk(seen) if seen else None,
    }


def _input(
    ctx: ParseContext,
    *,
    platform: str,
    source_id: str,
    external_item_id: str | None,
    event_type: str,
    content: str,
    captured_at: str | None,
    time_basis: str,
    source_published_at: str | None,
    completeness: str,
    missing_reason: str | None,
    anchor: str,
) -> dict:
    if time_basis not in TIME_BASES:
        raise ValueError(f"time_basis must be one of {TIME_BASES}")
    if time_basis == "unknown":
        captured_at = None
    key = event_key_for(platform, event_type, content, external_item_id)
    inbox_ref = f"{ctx.path}#{anchor}" if anchor else ctx.path
    return {
        "schema_version": SCHEMA_VERSION,
        "input_id": input_id_for(platform, source_id, key),
        "source_id": source_id,
        "external_item_id": external_item_id,
        "event_type": event_type,
        "captured_at": captured_at,
        "time_basis": time_basis,
        "received_at": _resolve_received_at(ctx, external_item_id),
        "source_published_at": source_published_at,
        "source_week": source_week_for(captured_at, time_basis),
        "origin": ctx.origin,
        "content_fingerprint": content_fingerprint(content),
        "completeness": completeness,
        "missing_reason": None if completeness == "full" else missing_reason,
        "process_state": "pending",
        "last_error": None,
        "last_cycle_id": None,
        "topics": None,
        "summary_ref": None,
        "process_version": None,
        "suspected_duplicate_of": None,
        "inbox_ref": inbox_ref,
    }


def _resolve_received_at(ctx: ParseContext, item_id: str | None) -> str | None:
    """N1 order: git-first lookup, then index first-seen, then caller fallbacks."""
    if item_id and ctx.received_at_lookup is not None:
        found = ctx.received_at_lookup(item_id)
        if found:
            return _must_hk(found)
    if item_id and ctx.item_first_seen_at is not None:
        found = ctx.item_first_seen_at(item_id)
        if found:
            return _must_hk(found)
    if ctx.received_at:
        return _must_hk(ctx.received_at)
    if ctx.first_seen_at:
        return _must_hk(ctx.first_seen_at)
    return None


def _first_seen_capture(ctx: ParseContext, item_id: str | None) -> tuple[str | None, str]:
    """``captured_at`` for a note with no platform clock.

    Filled only from a per-item or note-level first-seen time. Otherwise null.
    ``time_basis`` stays ``first_seen`` (``unknown`` is historical-only and is
    chosen by the caller, not here).
    """
    raw = None
    if item_id and ctx.item_first_seen_at is not None:
        raw = ctx.item_first_seen_at(item_id)
    if not raw:
        raw = ctx.first_seen_at
    if not raw:
        return None, "first_seen"
    return _must_hk(raw), "first_seen"


def _must_hk(raw: str) -> str:
    moment = parse_time(raw)
    if moment is None:
        raise ValueError(f"timestamp must include a date: {raw!r}")
    return format_hk(moment)


def _blank_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _first_http(text: str) -> str | None:
    match = re.search(r"https?://[^\s)>]+", text)
    return match.group(0) if match else None


def _query_value(url: str, key: str) -> str | None:
    for name, value in parse_qsl(urlsplit(url).query):
        if name == key and value:
            return value
    return None


def _youtube_quotes(text: str) -> list[str]:
    """Bullet lines under ``## 摘句``. Adapted from ``daily_digest.youtube_thread``."""
    marker = "\n## 摘句"
    index = text.find(marker)
    if index < 0:
        return []
    quotes: list[str] = []
    for line in text[index + len(marker) :].splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("- "):
            continue
        quote = stripped[2:].strip()
        if not quote or quote == _YT_EMPTY_QUOTE:
            continue
        quotes.append(quote)
    return quotes


def _snip_sections(text: str) -> list[str]:
    start = re.search(r"^##\s+Snips\s*$", text, re.M)
    chunk = text[start.end() :] if start else text
    stop = re.search(r"^##\s+", chunk, re.M)
    if stop:
        chunk = chunk[: stop.start()]
    parts = re.split(r"(?=^###\s+)", chunk, flags=re.M)
    return [part for part in parts if part.startswith("###")]


def _snip_id(section: str) -> str | None:
    match = _SNIP_URL_RE.search(section)
    if match:
        return match.group(1)
    ids = _UUID_RE.findall(section)
    return ids[-1] if ids else None


def _snip_own_time(section: str) -> datetime | None:
    for line in section.splitlines():
        if line.startswith("###"):
            continue
        stripped = line.strip().lstrip("-").strip()
        lowered = stripped.lower()
        for key in _SNIP_TIME_KEYS:
            if lowered.startswith(key):
                return _note_time(stripped.split(":", 1)[-1])
    return None


def _snip_quote(section: str) -> str:
    quotes: list[str] = []
    paragraphs: list[str] = []
    skip = False
    for line in section.splitlines():
        if line.startswith("###"):
            continue
        if re.search(r"key takeaways|^要点", line.strip(), re.I):
            skip = True
            continue
        if skip:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if any(lowered.lstrip("- ").startswith(key) for key in _SNIP_TIME_KEYS):
            continue
        if stripped.startswith(">"):
            quotes.append(stripped.lstrip(">").strip())
            continue
        if "http://" in stripped or "https://" in stripped:
            continue
        if stripped.startswith(("**", "- ")):
            continue
        paragraphs.append(stripped)
    if quotes:
        return "\n".join(quotes)
    return "\n".join(paragraphs)


def _weread_highlights(text: str) -> list[dict]:
    """Each ``> 📌`` block is one highlight. Block ids look like ``^bookId-章-起-止``."""
    highlights: list[dict] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current and (current["text"] or current["block_id"]):
            highlights.append(current)
        current = None

    for line in text.splitlines():
        pin = re.match(r"^>\s*📌\s*(.*)$", line)
        if pin:
            flush()
            raw = pin.group(1).strip()
            linked = re.match(r"^\[(.*)]\([^)]*\)$", raw)
            body = linked.group(1) if linked else raw
            block = None
            block_match = re.search(r"(\^[^\s#]+)", body)
            if block_match:
                block = block_match.group(1)
                body = (body[: block_match.start()] + body[block_match.end() :]).strip()
            current = {"text": body, "time": None, "block_id": block}
            continue
        if current is None:
            continue
        timed = re.match(r"^>\s*⏱\s+(.+)$", line)
        if timed and current["time"] is None:
            payload = timed.group(1).strip()
            current["time"] = _note_time(payload)
            inline = re.search(r"(\^[^\s#]+)", payload)
            if inline and current["block_id"] is None:
                current["block_id"] = inline.group(1)
            continue
        alone = re.match(r"^\s*(\^[^\s#]+)\s*$", line)
        if alone and current["block_id"] is None:
            current["block_id"] = alone.group(1)
    flush()
    return highlights


def _labeled_fields(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        stripped = line.strip().lstrip("-").strip()
        sep = "：" if "：" in stripped else ":" if ":" in stripped else ""
        if not sep:
            continue
        key, value = stripped.split(sep, 1)
        key = key.strip()
        value = value.strip()
        if key and value and key not in found:
            found[key] = value
    return found


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.M)
    if not match:
        return ""
    rest = text[match.end() :]
    nxt = re.search(r"^##\s+", rest, re.M)
    chunk = rest[: nxt.start()] if nxt else rest
    return chunk.strip()


def _heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _author_from_heading(heading: str) -> str | None:
    match = re.match(r"^@(\S+?)[：:]", heading)
    return match.group(1) if match else None


def _title_from_heading(heading: str) -> str | None:
    if not heading:
        return None
    for sep in ("：", ":"):
        if sep in heading:
            title = heading.split(sep, 1)[1].strip()
            return title or None
    return heading


def _status_id(url: str, path: str) -> str | None:
    match = _STATUS_URL_RE.search(url)
    if match:
        return match.group(1)
    file_match = _STATUS_FILE_RE.search(Path(path).stem)
    return file_match.group(1) if file_match else None


def _ig_shortcode(url: str, path: str) -> str | None:
    match = _IG_CODE_RE.search(url)
    if match:
        return match.group(1)
    tail = Path(path).stem.rsplit("-", 1)[-1]
    # Shortcodes mix letters and digits (EXMPL00001). A bare author slug does not.
    if re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9_-]{6,}", tail):
        return tail
    return None
