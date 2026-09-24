#!/usr/bin/env python3
"""Copy information-flow skills into a DigitalBrain vault.

Source of truth stays in this repo. DigitalBrain only keeps copies so a
Cursor Cloud session opened on obsidian-digitalbrain sees the same rules.
Does not rewrite Journal, Digests, Resources, or Cognition content.

Default mode writes the allowlisted skill copies and patches the AGENTS
marked route block. Pass --check / --drift for a read-only exact-file
drift report (zero destination writes).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
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


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    """Replace only the marked route block; preserve all other AGENTS bytes."""
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


def extract_marked_block(text: str) -> str | None:
    if MARK_START not in text or MARK_END not in text:
        return None
    start = text.index(MARK_START)
    end = text.index(MARK_END) + len(MARK_END)
    return text[start:end]


def expected_marked_block() -> str:
    return load_route_snippet().rstrip("\n")


@dataclass(frozen=True)
class SkillDriftStatus:
    path: str
    status: str  # match | missing | mismatch
    source_hash: str
    dest_hash: str | None


@dataclass(frozen=True)
class DriftReport:
    skills: tuple[SkillDriftStatus, ...]
    agents_block_status: str  # match | missing | mismatch
    agents_source_hash: str
    agents_dest_hash: str | None

    @property
    def has_drift(self) -> bool:
        if self.agents_block_status != "match":
            return True
        return any(item.status != "match" for item in self.skills)


def check_skill_file(vault: Path, relative: str) -> SkillDriftStatus:
    src = SKILLS_DIR / relative
    if not src.is_file():
        raise SystemExit(f"missing skill source: {src}")
    source_bytes = src.read_bytes()
    source_hash = content_hash(source_bytes)
    vault_rel = f".cursor/skills/{relative}"
    dest = vault / ".cursor" / "skills" / relative
    if not dest.is_file():
        return SkillDriftStatus(vault_rel, "missing", source_hash, None)
    dest_bytes = dest.read_bytes()
    dest_hash = content_hash(dest_bytes)
    status = "match" if dest_bytes == source_bytes else "mismatch"
    return SkillDriftStatus(vault_rel, status, source_hash, dest_hash)


def check_agents_block(vault: Path) -> tuple[str, str, str | None]:
    """Status is match, missing, or mismatch.

    missing: AGENTS.md is absent, or the file exists but the managed marked
    block is absent. mismatch: the marked block is present and its bytes
    differ from the source snippet. match: the marked block bytes match.
    """
    expected = expected_marked_block()
    source_hash = content_hash(expected.encode("utf-8"))
    agents = vault / "AGENTS.md"
    if not agents.is_file():
        return "missing", source_hash, None
    text = agents.read_text(encoding="utf-8")
    block = extract_marked_block(text)
    if block is None:
        return "missing", source_hash, None
    dest_hash = content_hash(block.encode("utf-8"))
    # Compare marker-to-marker body; tolerate a single trailing newline on either side.
    if block.rstrip("\n") == expected.rstrip("\n"):
        return "match", source_hash, dest_hash
    return "mismatch", source_hash, dest_hash


def check_drift(vault: Path) -> DriftReport:
    """Read-only exact-file drift for allowlisted skills + AGENTS marked block."""
    skills = tuple(check_skill_file(vault, relative) for relative in SKILL_RELATIVE_PATHS)
    agents_status, agents_src, agents_dst = check_agents_block(vault)
    return DriftReport(skills, agents_status, agents_src, agents_dst)


def print_drift_report(report: DriftReport) -> None:
    """Privacy-safe stdout: paths, status, and hashes only."""
    for item in report.skills:
        dest = item.dest_hash if item.dest_hash is not None else "-"
        print(
            f"skill {item.path} {item.status} src={item.source_hash} dst={dest}"
        )
    dest = report.agents_dest_hash if report.agents_dest_hash is not None else "-"
    print(
        f"agents_block {report.agents_block_status} "
        f"src={report.agents_source_hash} dst={dest}"
    )
    print("drift found" if report.has_drift else "drift clean")


def validate_vault(vault: Path) -> int | None:
    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1
    if not (vault / "📝 Journal").is_dir() and not (vault / "AGENTS.md").is_file():
        print(f"not a DigitalBrain vault: {vault}", file=sys.stderr)
        return 1
    return None


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
    parser.add_argument(
        "--check",
        "--drift",
        dest="check",
        action="store_true",
        help=(
            "read-only drift check for allowlisted skill copies and the "
            "AGENTS marked route block; never writes"
        ),
    )
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    invalid = validate_vault(vault)
    if invalid is not None:
        return invalid

    if args.check:
        report = check_drift(vault)
        print_drift_report(report)
        return 1 if report.has_drift else 0

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
