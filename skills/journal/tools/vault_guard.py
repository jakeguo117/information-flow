#!/usr/bin/env python3
"""Refuse vault writes unless every git remote is jakeguo117/obsidian-digitalbrain.

origin must exist. Each remote's fetch URL and effective push URL (pushurl,
pushInsteadOf, insteadOf) must be an https or ssh github.com URL for that
repository. information-flow and this code repository are always refused.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

DEFAULT_VAULT_REMOTE = "jakeguo117/obsidian-digitalbrain"
ENV_RUNTIME = "INFOFLOW_RUNTIME"
RUNTIME_CODEX_CLOUD = "codex-cloud"
DENIED_REPO_NAMES = frozenset({"information-flow"})
MARKER_NAME = ".runtime-codex-cloud"

PUBLIC_REPO_REFUSAL = "写入只许进 obsidian-digitalbrain，发现是公开仓就拒绝并停下"
CODE_REPO_REFUSAL = "写入只许进 obsidian-digitalbrain，工作区是 information-flow 代码仓，拒绝并停下"
OTHER_REFUSAL = "写入只许进 obsidian-digitalbrain，当前远端不在允许列表，拒绝并停下"
GIT_MISSING = "git is not available; file was not written"

_GITHUB_HTTPS = re.compile(
    r"^https://(?:[^@/]+@)?github\.com(?::\d+)?/(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
    re.IGNORECASE,
)
_GITHUB_SSH = re.compile(
    r"^ssh://(?:[^@/]+@)?github\.com(?::\d+)?/(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
    re.IGNORECASE,
)
_GITHUB_SCP = re.compile(
    r"^[^@/\s]+@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
    re.IGNORECASE,
)


def codex_cloud() -> bool:
    """True when this process should leave commits to a Codex Cloud pull request."""
    raw = os.environ.get(ENV_RUNTIME)
    if raw is not None and raw.strip():
        return raw.strip() == RUNTIME_CODEX_CLOUD
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "skills" / "journal" / "tools" / "vault_guard.py").is_file():
            return (candidate / MARKER_NAME).is_file()
    return False


def is_code_repo(path: Path) -> bool:
    """True when path is this information-flow checkout or a directory inside it."""
    try:
        current = path.expanduser().resolve()
    except OSError:
        return False
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "scripts" / "package_journal_pack.py").is_file() and (
            candidate / "skills" / "journal" / "SKILL.md"
        ).is_file():
            return True
    return False


def slug_of(value: str) -> str | None:
    """Return owner/repo for a github.com https or ssh URL. Anything else is None."""
    text = value.strip().rstrip("/")
    if text.endswith(".git"):
        text = text[:-4]
    for pattern in (_GITHUB_HTTPS, _GITHUB_SSH, _GITHUB_SCP):
        match = pattern.fullmatch(text)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}".lower()
    return None


def _git(vault: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    return subprocess.run(
        ["git", "-C", str(vault), *args],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
        check=False,
    )


def _remote_urls(vault: Path, name: str, *, push: bool) -> list[str] | None:
    args = ["remote", "get-url"]
    if push:
        args.append("--push")
    args.extend(["--all", name])
    proc = _git(vault, args)
    urls = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    if proc.returncode != 0 or not urls:
        return None
    return urls


def _remote_rejection(vault: Path, code: bool) -> tuple[str, str] | None:
    listed = _git(vault, ["remote"])
    names = [line.strip() for line in (listed.stdout or "").splitlines() if line.strip()]
    if listed.returncode != 0:
        names = []
    if "origin" not in names:
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "refused", OTHER_REFUSAL
    public = False
    mismatch = False
    for name in names:
        for push in (False, True):
            urls = _remote_urls(vault, name, push=push)
            if urls is None:
                mismatch = True
                continue
            for url in urls:
                slug = slug_of(url)
                repo = slug.split("/", 1)[1] if slug is not None else ""
                if repo in DENIED_REPO_NAMES:
                    public = True
                elif slug != DEFAULT_VAULT_REMOTE:
                    mismatch = True
    if public:
        return "refused", PUBLIC_REPO_REFUSAL
    if code:
        return "refused", CODE_REPO_REFUSAL
    if mismatch:
        return "refused", OTHER_REFUSAL
    return None


def rejection(vault: Path) -> tuple[str, str] | None:
    """None when a write may proceed. Otherwise (status, message)."""
    code = is_code_repo(vault)
    if not vault.exists() or not vault.is_dir():
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", "vault missing; write refused"
    try:
        return _remote_rejection(vault, code)
    except FileNotFoundError:
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", GIT_MISSING
    except subprocess.TimeoutExpired:
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", GIT_MISSING
