#!/usr/bin/env python3
"""Copy information-flow skills into a DigitalBrain vault.

Source of truth stays in this repo. DigitalBrain only keeps copies so a
Cursor Cloud session opened on obsidian-digitalbrain sees the same rules.
Does not rewrite Journal, Digests, Resources, or Cognition content.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = PLUGIN_ROOT / "skills"
ROUTE_SNIPPET = SKILLS_DIR / "digitalbrain-agents-route.md"
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)

SKILL_RELATIVE_PATHS = (
    "intake/SKILL.md",
    "journal/SKILL.md",
    "journal/references/setup.md",
    "journal/references/weekly-brief.md",
    "cognition/SKILL.md",
    "cognition/references/schema.md",
    "cognition/references/retrieval.md",
    "cognition/references/layout.md",
    "cognition/tools/cognition_lib.py",
    "cognition/tools/validate_cognition.py",
    "cognition/tools/retrieve_cognition.py",
    "cognition/tools/write_cognition.py",
)

MARK_START = "<!-- information-flow:digest-route:start -->"
MARK_END = "<!-- information-flow:digest-route:end -->"
LEGACY_DIGEST_HEADING = re.compile(
    r"^## 今天 Digest.*?(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


def load_route_snippet() -> str:
    text = ROUTE_SNIPPET.read_text(encoding="utf-8").strip() + "\n"
    if MARK_START not in text or MARK_END not in text:
        raise SystemExit(f"route snippet missing markers: {ROUTE_SNIPPET}")
    return text


def copy_skills(vault: Path) -> list[Path]:
    written: list[Path] = []
    for relative in SKILL_RELATIVE_PATHS:
        src = SKILLS_DIR / relative
        if not src.is_file():
            raise SystemExit(f"missing skill source: {src}")
        dest = vault / ".cursor" / "skills" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(dest)
    return written


def patch_agents(text: str, snippet: str) -> str:
    snippet = snippet.strip() + "\n"
    if MARK_START in text and MARK_END in text:
        start = text.index(MARK_START)
        end = text.index(MARK_END) + len(MARK_END)
        suffix = text[end:].lstrip("\n")
        prefix = text[:start]
        if suffix:
            return prefix + snippet + "\n" + suffix
        return prefix + snippet

    match = LEGACY_DIGEST_HEADING.search(text)
    if match:
        suffix = text[match.end() :].lstrip("\n")
        prefix = text[: match.start()]
        if suffix:
            return prefix + snippet + "\n" + suffix
        return prefix + snippet

    if not text.strip():
        return snippet
    return text.rstrip() + "\n\n" + snippet


def write_agents(vault: Path) -> Path:
    dest = vault / "AGENTS.md"
    snippet = load_route_snippet()
    current = dest.read_text(encoding="utf-8") if dest.is_file() else ""
    dest.write_text(patch_agents(current, snippet), encoding="utf-8")
    return dest


def commit_paths(vault: Path) -> list[str]:
    paths = [f".cursor/skills/{relative}" for relative in SKILL_RELATIVE_PATHS]
    paths.append("AGENTS.md")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy intake/journal/cognition skills into a DigitalBrain vault"
    )
    parser.add_argument("--vault")
    parser.add_argument(
        "--print-paths",
        action="store_true",
        help="print vault-relative paths that should be git added",
    )
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1
    if not (vault / "📝 Journal").is_dir() and not (vault / "AGENTS.md").is_file():
        print(f"not a DigitalBrain vault: {vault}", file=sys.stderr)
        return 1

    copy_skills(vault)
    write_agents(vault)
    if args.print_paths:
        for path in commit_paths(vault):
            print(path)
    else:
        print(f"synced skills into {vault}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
