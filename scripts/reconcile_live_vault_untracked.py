#!/usr/bin/env python3
"""Unblock Obsidian Git pull after Snipd/WeRead dual-write.

The live iCloud vault receives plugin files as untracked. launchd copies those
trees into a standalone clone and pushes origin/main. Obsidian Git is pull-only,
so git merge then refuses: untracked working tree files would be overwritten.

Byte-identical untracked files are safe to delete; the incoming commit recreates
them as tracked. Divergent untracked files are left in place.

Never cd into the vault. launchd gets EPERM from getcwd() on iCloud paths.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DEFAULT_VAULT = Path.home() / (
    "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)


def git(vault: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(vault), *args],
        cwd="/",
        check=check,
        capture_output=True,
        text=True,
    )


def is_untracked(vault: Path, rel: str) -> bool:
    tracked = git(vault, "ls-files", "--", rel, check=False)
    if tracked.stdout.strip():
        return False
    others = git(
        vault, "ls-files", "--others", "--exclude-standard", "--", rel, check=False
    )
    return bool(others.stdout.strip())


def reconcile(vault: Path, do_merge: bool) -> int:
    if not vault.is_dir():
        print(f"error: vault missing: {vault}", file=sys.stderr)
        return 1

    git(vault, "fetch", "origin", check=False)

    head = git(vault, "rev-parse", "HEAD").stdout.strip()
    origin = git(vault, "rev-parse", "origin/main", check=False)
    if origin.returncode != 0:
        print("error: origin/main missing", file=sys.stderr)
        return 1
    origin_sha = origin.stdout.strip()

    incoming = [
        line
        for line in git(
            vault,
            "-c",
            "core.quotepath=false",
            "diff",
            "--name-only",
            "HEAD..origin/main",
        ).stdout.splitlines()
        if line
    ]

    removed: list[str] = []
    kept_divergent: list[str] = []

    for rel in incoming:
        path = vault / rel
        if not path.is_file():
            continue
        if not is_untracked(vault, rel):
            continue
        local_blob = git(vault, "hash-object", "--", rel).stdout.strip()
        remote = git(vault, "rev-parse", f"origin/main:{rel}", check=False)
        if remote.returncode != 0:
            kept_divergent.append(rel)
            continue
        remote_blob = remote.stdout.strip()
        if local_blob == remote_blob:
            path.unlink()
            removed.append(rel)
        else:
            kept_divergent.append(rel)

    for rel in removed:
        print(f"removed identical untracked: {rel}")
    for rel in kept_divergent:
        print(f"kept divergent untracked: {rel}")

    if kept_divergent:
        print(
            "skip merge: divergent untracked files would still block pull",
            file=sys.stderr,
        )
        return 0

    if not do_merge or head == origin_sha:
        return 0

    merged = git(
        vault,
        "merge",
        "--ff-only",
        "origin/main",
        check=False,
    )
    if merged.returncode != 0:
        print((merged.stderr or merged.stdout).strip(), file=sys.stderr)
        return 0
    print((merged.stdout or "merged origin/main").strip())
    return 0


def main() -> int:
    vault = Path(
        os.environ.get("INTAKE_VAULT")
        or os.environ.get("DIGITALBRAIN_LIVE_VAULT")
        or DEFAULT_VAULT
    )
    do_merge = os.environ.get("DIGITALBRAIN_RECONCILE_MERGE", "1") not in {
        "0",
        "false",
        "no",
    }
    return reconcile(vault, do_merge)


if __name__ == "__main__":
    sys.exit(main())
