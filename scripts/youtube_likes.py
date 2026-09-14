#!/usr/bin/env python3
"""Sync today's YouTube likes into vault sources for Digest. No Hermes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)
SECRETS_DIR = (
    Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/.secrets/youtube"
)
CLIENT_PATH = SECRETS_DIR / "google_client_secret.json"
TOKEN_PATH = SECRETS_DIR / "youtube_token.json"
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = PLUGIN_ROOT / "state" / "youtube-likes.json"
MODEL_PATH = PLUGIN_ROOT / "models" / "ggml-small.bin"
LIKES_DIRNAME = "📥 Inbox/YouTube-Likes"
MAX_QUOTES = 5
WHISPER_TIMEOUT_S = 1200
CAPTION_LANGS = "zh-Hans,zh-Hant,en,en-orig"
TAG_RE = re.compile(r"<[^>]+>")
TS_RE = re.compile(r"<\d{2}:\d{2}:\d{2}[.\d]*>")
def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


def which(name: str) -> str | None:
    return shutil.which(name)


def shanghai_date(iso_z: str) -> dt.date:
    stamp = dt.datetime.fromisoformat(iso_z.replace("Z", "+00:00")).astimezone(SHANGHAI)
    return stamp.date()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    path.chmod(0o600)


def load_client() -> dict:
    if not CLIENT_PATH.is_file():
        raise SystemExit(f"missing OAuth client: {CLIENT_PATH}")
    data = load_json(CLIENT_PATH)
    installed = data.get("installed") or data.get("web")
    if not installed:
        raise SystemExit("OAuth client JSON missing installed/web")
    return installed


def load_token() -> dict:
    if not TOKEN_PATH.is_file():
        raise SystemExit(f"missing YouTube token; run youtube_oauth.py first: {TOKEN_PATH}")
    return load_json(TOKEN_PATH)


def refresh_token(client: dict, token: dict) -> dict:
    body = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        new = json.loads(resp.read().decode())
    token["access_token"] = new["access_token"]
    token["expires_in"] = new.get("expires_in")
    if new.get("refresh_token"):
        token["refresh_token"] = new["refresh_token"]
    save_json(TOKEN_PATH, token)
    return token


def api_get(token: dict, client: dict, url: str) -> dict:
    def once(access: str) -> dict:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    try:
        return once(token["access_token"])
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise
        token = refresh_token(client, token)
        return once(token["access_token"])


def fetch_liked_since(client: dict, token: dict, start: dt.date) -> list[dict]:
    items: list[dict] = []
    page = None
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": "LL",
            "maxResults": "50",
        }
        if page:
            params["pageToken"] = page
        data = api_get(
            token,
            client,
            "https://www.googleapis.com/youtube/v3/playlistItems?" + urllib.parse.urlencode(params),
        )
        stop = False
        for raw in data.get("items") or []:
            sn = raw.get("snippet") or {}
            cd = raw.get("contentDetails") or {}
            title = sn.get("title") or ""
            video_id = cd.get("videoId") or (sn.get("resourceId") or {}).get("videoId")
            like_at = sn.get("publishedAt")
            if not video_id or not like_at or title in {"Private video", "Deleted video"}:
                continue
            liked_day = shanghai_date(like_at)
            if liked_day < start:
                stop = True
                break
            items.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "channel": sn.get("videoOwnerChannelTitle") or "unknown",
                    "like_at": like_at,
                    "liked_day": liked_day.isoformat(),
                    "video_published_at": cd.get("videoPublishedAt") or "",
                }
            )
        if stop:
            break
        page = data.get("nextPageToken")
        if not page:
            break
    return items


def clean_vtt(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line or line.isdigit():
            continue
        if TS_RE.search(line):
            continue
        line = TAG_RE.sub("", line).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 8:
            continue
        if lines and line == lines[-1]:
            continue
        if lines and line in lines[-1]:
            continue
        if lines and lines[-1] in line:
            lines[-1] = line
            continue
        lines.append(line)
    return lines


def pick_quotes(lines: list[str], limit: int = MAX_QUOTES) -> list[str]:
    if not lines:
        return []
    start = max(1, len(lines) // 12)

    def ok(ln: str) -> bool:
        if not (12 <= len(ln) <= 180):
            return False
        if ln.endswith((",", "，", "、")):
            return False
        if ln[0].isascii() and ln[0].islower():
            return False
        return True

    usable = [ln for ln in lines[start:] if ok(ln)]
    if not usable:
        usable = lines[start:] or lines
    if len(usable) <= limit:
        return usable[:limit]
    quotes = []
    for i in range(limit):
        idx = int((i + 0.5) * (len(usable) - 1) / limit)
        candidate = usable[idx]
        if candidate not in quotes:
            quotes.append(candidate)
    return quotes[:limit]


def run_yt_dlp(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    binary = which("yt-dlp")
    if not binary:
        raise SystemExit("yt-dlp missing")
    return subprocess.run(
        [binary, "--no-warnings", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def fetch_captions(video_id: str, tmp: Path) -> list[str]:
    dest = tmp / video_id
    args = [
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang",
        CAPTION_LANGS,
        "--sub-format",
        "vtt",
        "--skip-download",
        "-o",
        str(dest),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    result = run_yt_dlp(args)
    if result.returncode != 0 and "429" in (result.stderr or ""):
        import time

        time.sleep(3)
        result = run_yt_dlp(args)
    vtts = sorted(tmp.glob(f"{video_id}*.vtt"))
    preferred = [p for p in vtts if ".zh" in p.name] or [p for p in vtts if ".en" in p.name] or vtts
    if not preferred:
        return []
    return clean_vtt(preferred[0].read_text(encoding="utf-8", errors="replace"))


def whisper_transcribe(video_id: str, tmp: Path) -> list[str]:
    cli = which("whisper-cli")
    if not cli or not MODEL_PATH.is_file():
        return []
    audio = tmp / f"{video_id}.wav"
    result = run_yt_dlp(
        [
            "-x",
            "--audio-format",
            "wav",
            "--postprocessor-args",
            "ffmpeg:-ar 16000 -ac 1",
            "-o",
            str(tmp / f"{video_id}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        timeout=300,
    )
    if result.returncode != 0 or not audio.is_file():
        matches = list(tmp.glob(f"{video_id}*.wav"))
        if not matches:
            return []
        audio = matches[0]
    out_prefix = tmp / f"{video_id}-whisper"
    proc = subprocess.run(
        [cli, "-m", str(MODEL_PATH), "-f", str(audio), "-l", "auto", "-otxt", "-of", str(out_prefix), "-np"],
        capture_output=True,
        text=True,
        timeout=WHISPER_TIMEOUT_S,
    )
    text_path = Path(str(out_prefix) + ".txt")
    if proc.returncode != 0 or not text_path.is_file():
        return []
    lines = []
    for raw in text_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if len(line) >= 8:
            lines.append(line)
    return lines


def wiki_rel(path: Path, vault: Path) -> str:
    rel = path.relative_to(vault).as_posix()
    return rel[:-3] if rel.endswith(".md") else rel


def write_source(vault: Path, item: dict, quotes: list[str], method: str) -> Path:
    out_dir = vault / LIKES_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"{item['liked_day']}-{item['video_id']}.md"
    url = f"https://www.youtube.com/watch?v={item['video_id']}"
    lines = [
        "---",
        f"date: {item['liked_day']}",
        "type: youtube-like",
        f"video_id: {item['video_id']}",
        f"title: {item['title']}",
        f"channel: {item['channel']}",
        f"like_at: {item['like_at']}",
        f"source_url: {url}",
        f"transcript: {method}",
        "generator: journal-youtube-likes",
        "---",
        "",
        f"# {item['title']}",
        "",
        f"{item['channel']} · 点赞 {item['like_at']}",
        "",
        url,
        "",
        "## 摘句",
        "",
    ]
    if quotes:
        for quote in quotes:
            lines.append(f"- {quote}")
    else:
        lines.append("- （无字幕、听写也没产出句子）")
    lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def process_item(vault: Path, item: dict, force: bool) -> dict:
    dest = vault / LIKES_DIRNAME / f"{item['liked_day']}-{item['video_id']}.md"
    if dest.exists() and not force:
        text = dest.read_text(encoding="utf-8", errors="replace")
        if "generator: journal-youtube-likes" in text:
            return {"video_id": item["video_id"], "status": "exists", "path": str(dest), "method": "cached"}
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        method = "none"
        lines = fetch_captions(item["video_id"], tmp)
        if lines:
            method = "captions"
        else:
            lines = whisper_transcribe(item["video_id"], tmp)
            if lines:
                method = "whisper"
        quotes = pick_quotes(lines)
        path = write_source(vault, item, quotes, method)
    return {
        "video_id": item["video_id"],
        "status": "wrote",
        "path": str(path),
        "method": method,
        "quotes": len(quotes),
        "liked_day": item["liked_day"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync YouTube likes into vault sources")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today Asia/Shanghai)")
    parser.add_argument("--since", help="Include likes from this date through --date/today")
    parser.add_argument("--vault")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    end = dt.date.fromisoformat(args.date) if args.date else today
    start = dt.date.fromisoformat(args.since) if args.since else end
    client = load_client()
    token = load_token()
    liked = fetch_liked_since(client, token, start)
    liked = [item for item in liked if start <= dt.date.fromisoformat(item["liked_day"]) <= end]
    results = []
    for item in liked:
        results.append(process_item(vault, item, force=args.force))

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "ran_at": dt.datetime.now(SHANGHAI).isoformat(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "liked": len(liked),
        "results": results,
    }
    with STATE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(log, ensure_ascii=False) + "\n")

    if not liked:
        print(f"no new likes {start}..{end}")
        return 0
    for row in results:
        print(
            f"{row['status']} {row.get('liked_day', '')} {row['video_id']} method={row.get('method')} quotes={row.get('quotes', '-')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
