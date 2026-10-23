#!/usr/bin/env python3
"""Refuse vault writes unless the git remote is an allowed data vault.

Default allowlist is jakeguo117/obsidian-digitalbrain. Override with
INFOFLOW_VAULT_REMOTE (comma-separated) or config.json key vault_remote.
information-flow and this code repository are always refused.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

DEFAULT_VAULT_REMOTE = "jakeguo117/obsidian-digitalbrain"
ENV_ALLOWLIST = "INFOFLOW_VAULT_REMOTE"
ENV_RUNTIME = "INFOFLOW_RUNTIME"
RUNTIME_CODEX_CLOUD = "codex-cloud"
CONFIG_KEY = "vault_remote"
PLACEHOLDER_MARK = "REPLACE_WITH_"
DENIED_REPO_NAMES = frozenset({"information-flow"})
MARKER_NAME = ".runtime-codex-cloud"

PUBLIC_REPO_REFUSAL = "写入只许进 obsidian-digitalbrain，发现是公开仓就拒绝并停下"
CODE_REPO_REFUSAL = "写入只许进 obsidian-digitalbrain，工作区是 information-flow 代码仓，拒绝并停下"
OTHER_REFUSAL = "写入只许进 obsidian-digitalbrain，当前远端不在允许列表，拒绝并停下"
GIT_MISSING = "git is not available; file was not written"

_SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GITHUB = re.compile(
    r"^(?:https?://|ssh://|git://)(?:[^@/]+@)?github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)$",
    re.IGNORECASE,
)
_GITHUB_SCP = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
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
    text = value.strip().rstrip("/")
    if text.endswith(".git"):
        text = text[:-4]
    if _SLUG.fullmatch(text):
        return text.lower()
    for pattern in (_GITHUB, _GITHUB_SCP):
        match = pattern.fullmatch(text)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}".lower()
    return None


def _usable(value: str) -> bool:
    text = value.strip()
    return bool(text) and PLACEHOLDER_MARK not in text


def _as_list(value: object) -> list[str] | None:
    if isinstance(value, str):
        if not _usable(value):
            return None
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return parts or None
    if isinstance(value, list):
        parts = [item.strip() for item in value if isinstance(item, str) and _usable(item)]
        return parts or None
    return None


def _config_path() -> Path | None:
    env = os.environ.get("INFOFLOW_CONFIG")
    if env and env.strip():
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "config.example.json").is_file() and (
            candidate / "skills" / "journal" / "SKILL.md"
        ).is_file():
            path = candidate / "config.json"
            return path if path.is_file() else None
    return None


def allowlist() -> list[str]:
    """Env, then config.json vault_remote, then the default data vault."""
    env = os.environ.get(ENV_ALLOWLIST)
    if env is not None and env.strip():
        parsed = _as_list(env)
        if parsed:
            return parsed
    path = _config_path()
    if path is not None and path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        if isinstance(data, dict):
            parsed = _as_list(data.get(CONFIG_KEY))
            if parsed:
                return parsed
    return [DEFAULT_VAULT_REMOTE]


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


def _slugs_from_remote_v(stdout: str) -> list[str]:
    slugs: list[str] = []
    seen: set[str] = set()
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        slug = slug_of(parts[1])
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


def rejection(vault: Path) -> tuple[str, str] | None:
    """None when a write may proceed. Otherwise (status, message)."""
    code = is_code_repo(vault)
    if not vault.exists() or not vault.is_dir():
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", "vault missing; write refused"
    try:
        proc = _git(vault, ["remote", "-v"])
    except FileNotFoundError:
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", GIT_MISSING
    except subprocess.TimeoutExpired:
        if code:
            return "refused", CODE_REPO_REFUSAL
        return "unavailable", GIT_MISSING
    slugs = _slugs_from_remote_v(proc.stdout or "")
    for slug in slugs:
        if slug.split("/", 1)[1] in DENIED_REPO_NAMES:
            return "refused", PUBLIC_REPO_REFUSAL
    if code:
        return "refused", CODE_REPO_REFUSAL
    allowed = {parsed for item in allowlist() if (parsed := slug_of(item))}
    if any(slug in allowed for slug in slugs):
        return None
    return "refused", OTHER_REFUSAL
