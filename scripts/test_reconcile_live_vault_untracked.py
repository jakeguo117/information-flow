#!/usr/bin/env python3
"""Temp-repo tests for identical-untracked reconcile. No live vault."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reconcile_live_vault_untracked as reconcile  # noqa: E402


def git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ReconcileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.origin = root / "origin.git"
        self.vault = root / "vault"
        subprocess.check_call(["git", "init", "--bare", str(self.origin)])
        subprocess.check_call(["git", "clone", str(self.origin), str(self.vault)])
        git(self.vault, "config", "user.email", "test@example.com")
        git(self.vault, "config", "user.name", "test")
        write(self.vault / "kept.md", "keep\n")
        git(self.vault, "add", "kept.md")
        git(self.vault, "commit", "-m", "base")
        git(self.vault, "branch", "-M", "main")
        git(self.vault, "push", "-u", "origin", "main")
        os.environ["DIGITALBRAIN_DEBUG_LOG"] = str(root / "debug.ndjson")
        os.environ["DIGITALBRAIN_DEBUG_RUN_ID"] = "test"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _push_snipd_from_clone(self, body: str) -> None:
        clone = Path(self.tmp.name) / "clone"
        subprocess.check_call(["git", "clone", str(self.origin), str(clone)])
        git(clone, "config", "user.email", "test@example.com")
        git(clone, "config", "user.name", "test")
        write(clone / "Snipd" / "ep.md", body)
        git(clone, "add", "Snipd/ep.md")
        git(clone, "commit", "-m", "intake: sync Snipd WeRead sources")
        git(clone, "push", "origin", "main")

    def test_identical_untracked_removed_and_ff_merge(self) -> None:
        body = "# episode\n"
        write(self.vault / "Snipd" / "ep.md", body)
        self._push_snipd_from_clone(body)
        self.assertTrue((self.vault / "Snipd" / "ep.md").is_file())
        self.assertEqual(git(self.vault, "status", "--porcelain", "Snipd/ep.md"), "?? Snipd/ep.md")

        rc = reconcile.reconcile(self.vault, do_merge=True)
        self.assertEqual(rc, 0)
        self.assertTrue((self.vault / "Snipd" / "ep.md").is_file())
        self.assertEqual(git(self.vault, "rev-parse", "--abbrev-ref", "HEAD"), "main")
        self.assertEqual(
            git(self.vault, "rev-parse", "HEAD"),
            git(self.vault, "rev-parse", "origin/main"),
        )
        self.assertEqual((self.vault / "Snipd" / "ep.md").read_text(encoding="utf-8"), body)
        self.assertFalse(git(self.vault, "status", "--porcelain", "Snipd/ep.md"))

    def test_divergent_untracked_kept(self) -> None:
        write(self.vault / "Snipd" / "ep.md", "local unique\n")
        self._push_snipd_from_clone("remote version\n")
        rc = reconcile.reconcile(self.vault, do_merge=True)
        self.assertEqual(rc, 0)
        self.assertEqual((self.vault / "Snipd" / "ep.md").read_text(encoding="utf-8"), "local unique\n")
        self.assertNotEqual(
            git(self.vault, "rev-parse", "HEAD"),
            git(self.vault, "rev-parse", "origin/main"),
        )


if __name__ == "__main__":
    unittest.main()
