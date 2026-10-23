#!/usr/bin/env python3
"""User config for information-flow.

Vault path, git remote, and secret files come from the command, the
environment, or config.json. A missing value is an error. This module has
no personal default path, remote, or secrets directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CONFIG_NAME = "config.json"
PLACEHOLDER_MARK = "REPLACE_WITH_"

ENV_FOR_KEY = {
    "vault_root": "INFOFLOW_VAULT_ROOT",
    "git_remote": "INFOFLOW_GIT_REMOTE",
    "git_branch": "INFOFLOW_GIT_BRANCH",
    "storage_mode": "INFOFLOW_STORAGE_MODE",
}


def plugin_root() -> Path:
    return PLUGIN_ROOT


def resolve_config_path(explicit: str | None = None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser()
    env = os.environ.get("INFOFLOW_CONFIG")
    if env:
        return Path(env).expanduser()
    candidate = PLUGIN_ROOT / CONFIG_NAME
    if candidate.is_file():
        return candidate
    return None


def load_config(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"config must be a JSON object: {path}")
    return data


def reject_placeholder(value: str, label: str) -> str:
    if PLACEHOLDER_MARK in value:
        raise SystemExit(
            f"{label} is still a placeholder ({value}). "
            "Replace it in the user config. See config.example.json."
        )
    return value


def require_setting(
    key: str,
    *,
    cli: str | None = None,
    env: str | None = None,
    config_file: str | None = None,
) -> str:
    """Return one configured string. Never substitutes a built-in path."""
    if cli is not None and str(cli).strip():
        return reject_placeholder(str(cli).strip(), key)
    env_name = env if env is not None else ENV_FOR_KEY.get(key)
    if env_name:
        raw_env = os.environ.get(env_name)
        if raw_env is not None and raw_env.strip():
            return reject_placeholder(raw_env.strip(), key)
    path = resolve_config_path(config_file)
    raw = load_config(path).get(key)
    if isinstance(raw, str) and raw.strip():
        return reject_placeholder(raw.strip(), key)
    looked = []
    if env_name:
        looked.append(env_name)
    looked.append(str(path) if path else f"{PLUGIN_ROOT / CONFIG_NAME} (missing)")
    raise SystemExit(
        f"missing {key}: pass it on the command, set the environment, "
        f"or set {key} in config.json. Checked: {', '.join(looked)}. "
        "No default path is used. See config.example.json."
    )


def require_vault(raw: str | None = None, *, config_file: str | None = None) -> Path:
    value = require_setting("vault_root", cli=raw, config_file=config_file)
    return Path(value).expanduser()


def require_secret_file(env_name: str, label: str) -> Path:
    raw = os.environ.get(env_name)
    if raw is None or not raw.strip():
        raise SystemExit(
            f"missing {env_name} for {label}. "
            "Point it at a secrets file outside the vault and outside this repo. "
            "No default secrets directory is used."
        )
    value = reject_placeholder(raw.strip(), env_name)
    return Path(value).expanduser()


def write_user_config(path: Path, updates: dict) -> None:
    """Merge updates into a user config file. Does not drop unknown keys."""
    existing = load_config(path) if path.is_file() else {}
    merged = dict(existing)
    for key, value in updates.items():
        if value is None:
            continue
        merged[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print one information-flow user config value. Missing values exit non-zero."
    )
    parser.add_argument("action", choices=["get"])
    parser.add_argument("key")
    parser.add_argument("--config", help="config.json path (default: INFOFLOW_CONFIG or ./config.json)")
    args = parser.parse_args(argv)
    if args.key == "vault_root":
        print(require_vault(config_file=args.config))
        return 0
    print(require_setting(args.key, config_file=args.config))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(0)
