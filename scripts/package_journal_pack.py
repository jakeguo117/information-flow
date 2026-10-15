#!/usr/bin/env python3
"""Build the unpublished Journal + cognition dependency ZIP.

Reads the working tree. Does not git add, commit, push, or contact a vault.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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


CHATGPT_ZIP_NAME = "information-flow-plugin.zip"
CHATGPT_FILES = (
    "packaging/JOURNAL_PACK_README.md",
    "scripts/build_weekly_digest.py",
    "scripts/source_groups.py",
    "scripts/package_journal_pack.py",
    "scripts/sync_digitalbrain_skills.py",
    "scripts/test_journal_pack.py",
    "scripts/weekly_intake.py",
    "skills/digitalbrain-agents-route.md",
)
CHATGPT_TREES = (
    "skills/cognition",
    "skills/journal",
    "tests/synthetic/journal_pack",
)
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = 0x81A40000


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plugin_version() -> str:
    path = ROOT / ".codex-plugin" / "plugin.json"
    version = json.loads(path.read_text(encoding="utf-8")).get("version")
    if not isinstance(version, str) or not version.strip():
        raise SystemExit(f"plugin.json missing version: {path}")
    return version


def chatgpt_manifest(name: str) -> bytes:
    """ChatGPT upload manifests keep the uploaded ZIP's JSON shape.

    packaging/chatgpt-upload/*.json keeps the uploaded ZIP's JSON shape. The
    packed bytes take their version from .codex-plugin/plugin.json.
    """
    text = (ROOT / "packaging" / "chatgpt-upload" / name).read_text(encoding="utf-8")
    updated, count = re.subn(
        r'"version"\s*:\s*"[^"]*"',
        f'"version": "{plugin_version()}"',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"chatgpt manifest missing version: {name}")
    return updated.encode("utf-8")


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ZIP_MODE
    info.flag_bits = 0
    return info


def write_deterministic_zip(path: Path, entries: list[tuple[str, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in entries:
            archive.writestr(zip_info(name), data)


def chatgpt_repo_files() -> list[str]:
    files = list(CHATGPT_FILES)
    for rel in CHATGPT_TREES:
        root = ROOT / rel
        if not root.is_dir():
            raise SystemExit(f"missing pack tree: {rel}")
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            files.append(path.relative_to(ROOT).as_posix())
    missing = [rel for rel in files if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit(f"missing chatgpt pack files: {missing}")
    for rel in files:
        for part in FORBIDDEN_PARTS:
            if part in rel:
                raise SystemExit(f"chatgpt pack contains forbidden path: {rel}")
    return sorted(set(files))


def build_chatgpt_plugin(dist_dir: Path) -> Path:
    """Upload ZIP for the ChatGPT plugin. Fixed 1980-01-01 timestamps."""
    entries = [
        ("plugin.json", chatgpt_manifest("root-plugin.json")),
        (".codex-plugin/plugin.json", chatgpt_manifest("codex-plugin.json")),
    ]
    for rel in chatgpt_repo_files():
        entries.append((rel, (ROOT / rel).read_bytes()))
    dest = dist_dir / CHATGPT_ZIP_NAME
    write_deterministic_zip(dest, entries)
    return dest


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
        "plugin_version_field": plugin_version(),
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
    parser.add_argument("--out-dir", help="write the unpublished task pack and MANIFEST.json here")
    parser.add_argument(
        "--chatgpt-plugin",
        action="store_true",
        help="write dist/information-flow-plugin.zip for the ChatGPT upload",
    )
    parser.add_argument("--dist", default=str(ROOT / "dist"))
    args = parser.parse_args(argv)
    if not args.out_dir and not args.chatgpt_plugin:
        parser.error("pass --out-dir and/or --chatgpt-plugin")
    payload: dict = {}
    if args.out_dir:
        manifest = build(Path(args.out_dir))
        payload["zip_sha256"] = manifest["zip_sha256"]
        payload["files"] = len(manifest["files"])
    if args.chatgpt_plugin:
        dest = build_chatgpt_plugin(Path(args.dist))
        payload["chatgpt_zip"] = str(dest)
        payload["chatgpt_sha256"] = sha256_file(dest)
        payload["chatgpt_files"] = len(zipfile.ZipFile(dest).namelist())
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
