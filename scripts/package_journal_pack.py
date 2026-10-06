#!/usr/bin/env python3
"""Build the unpublished Journal + cognition dependency ZIP.

Reads the working tree. Does not git add, commit, push, or contact a vault.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_NAME = "AIC-TASK-JOURNAL-PACK-0001-journal-cognition.zip"

ALLOWLIST = (
    ".codex-plugin/plugin.json",
    "packaging/JOURNAL_PACK_README.md",
    "skills/journal/SKILL.md",
    "skills/journal/references/setup.md",
    "skills/journal/references/weekly-brief.md",
    "skills/journal/tools/journal_lib.py",
    "skills/journal/tools/write_journal.py",
    "skills/cognition/SKILL.md",
    "skills/cognition/references/schema.md",
    "skills/cognition/references/retrieval.md",
    "skills/cognition/references/layout.md",
    "skills/cognition/tools/cognition_lib.py",
    "skills/cognition/tools/validate_cognition.py",
    "skills/cognition/tools/retrieve_cognition.py",
    "skills/cognition/tools/write_cognition.py",
    "skills/digitalbrain-agents-route.md",
    "scripts/weekly_intake.py",
    "scripts/sync_digitalbrain_skills.py",
    "scripts/test_journal_pack.py",
    "scripts/package_journal_pack.py",
    "tests/synthetic/journal_pack/intake_unchecked_and_new_channel.md",
    "tests/synthetic/journal_pack/evidence_accept.md",
)

FORBIDDEN_PARTS = (
    "launchd/",
    ".github/",
    "youtube_",
    "vault_recovery",
    "daily_digest",
    "push_intake",
    "continue_project",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def build(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    missing = [rel for rel in ALLOWLIST if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit(f"missing pack files: {missing}")
    for rel in ALLOWLIST:
        for part in FORBIDDEN_PARTS:
            if part in rel:
                raise SystemExit(f"allowlist contains forbidden path: {rel}")

    files = []
    for rel in ALLOWLIST:
        path = ROOT / rel
        files.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    zip_path = out_dir / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in ALLOWLIST:
            archive.write(ROOT / rel, arcname=rel)
    zip_bytes = zip_path.read_bytes()
    names = zipfile.ZipFile(zip_path).namelist()
    for name in names:
        for part in FORBIDDEN_PARTS:
            if part in name:
                raise SystemExit(f"zip contains forbidden path: {name}")

    manifest = {
        "package_id": "AIC-TASK-JOURNAL-PACK-0001",
        "parent_handoff": "AIC-HO-0001",
        "approval_id": "AIC-APR-0001",
        "source_repo": "https://github.com/jakeguo117/information-flow",
        "base_commit": git_output(["rev-parse", "HEAD"]),
        "git_commit_of_package": None,
        "published": False,
        "working_tree_dirty": bool(git_output(["status", "--porcelain"])),
        "plugin_version_field": "0.1.0",
        "requirements": "AIC-DOC-REQ@0.1.1",
        "workflow": "AIC-DOC-WORKFLOW@0.2.0",
        "handoff": "AIC-DOC-HANDOFF@0.2.0",
        "zip_name": ZIP_NAME,
        "zip_bytes": len(zip_bytes),
        "zip_sha256": hashlib.sha256(zip_bytes).hexdigest(),
        "files": files,
        "excluded": [
            "launchd and reminder plists",
            "GitHub Actions workflows",
            "YouTube OAuth and likes collectors",
            "daily_digest collector",
            "vault_recovery",
            "continue_project",
            "intake source push",
        ],
        "not_executed": [
            "install into a target account",
            "Cloud Work",
            "git add/commit/push/PR",
            "real Journal or Cognition read/write",
        ],
    }
    manifest_path = out_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package the journal + cognition ZIP")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    manifest = build(Path(args.out_dir))
    print(json.dumps({"zip_sha256": manifest["zip_sha256"], "files": len(manifest["files"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
