#!/usr/bin/env python3
"""One-shot YouTube OAuth for journal likes sync. Does not call Hermes."""

from __future__ import annotations

import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PORT = 18765
REDIRECT = f"http://localhost:{PORT}/"
SECRETS_DIR = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/.secrets/youtube"
)
CLIENT_PATH = SECRETS_DIR / "google_client_secret.json"
TOKEN_PATH = SECRETS_DIR / "youtube_token.json"


def load_client() -> dict:
    if not CLIENT_PATH.is_file():
        raise SystemExit(f"missing OAuth client: {CLIENT_PATH}")
    data = json.loads(CLIENT_PATH.read_text(encoding="utf-8"))
    installed = data.get("installed") or data.get("web")
    if not installed or "client_id" not in installed or "client_secret" not in installed:
        raise SystemExit("OAuth client JSON missing installed.client_id/secret")
    return installed


def exchange(client: dict, code: str) -> dict:
    body = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT,
        }
    ).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if "refresh_token" not in payload:
        raise SystemExit("token response missing refresh_token; re-consent with prompt=consent")
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    TOKEN_PATH.chmod(0o600)
    return payload


def main() -> int:
    client = load_client()
    state = secrets.token_urlsafe(16)
    captured: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            return

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if qs.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"state mismatch")
                return
            if "error" in qs:
                captured["error"] = qs["error"][0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"oauth error")
                return
            code = qs.get("code", [None])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"missing code")
                return
            captured["code"] = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body><p>YouTube 授权完成，可以关掉这个窗口。</p></body></html>".encode()
            )

    query = urllib.parse.urlencode(
        {
            "client_id": client["client_id"],
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    url = f"{AUTH_URL}?{query}"
    print(f"waiting on {REDIRECT}", flush=True)
    print(f"open: {url}", flush=True)
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.timeout = 1
    webbrowser.open(url)
    for _ in range(300):
        if "code" in captured or "error" in captured:
            break
        server.handle_request()
    server.server_close()
    if "error" in captured:
        print(f"oauth denied: {captured['error']}", file=sys.stderr)
        return 1
    if "code" not in captured:
        print("oauth timed out waiting for browser consent", file=sys.stderr)
        return 1
    exchange(client, captured["code"])
    print(f"wrote {TOKEN_PATH} scopes={SCOPE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
