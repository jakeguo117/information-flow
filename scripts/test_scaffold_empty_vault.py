#!/usr/bin/env python3
"""Acceptance tests for the empty-vault template and scaffold.

S1 and S2 stay Workflow manual checks: this repo has no onboarding UI.
S1 is the three-step walk (pick A or B, point at a root, connect one source).
S2 is posting left out of those steps. The scaffold does not post and does
not run a first index (P7).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_digest  # noqa: E402
import infoflow_config  # noqa: E402
import scaffold_empty_vault as scaffold  # noqa: E402
import sync_digitalbrain_skills as sync  # noqa: E402
import weekly_rollup  # noqa: E402
import youtube_likes  # noqa: E402
import youtube_oauth  # noqa: E402

PLUGIN = scaffold.PLUGIN_ROOT
TEMPLATE = scaffold.TEMPLATE_ROOT

EXPECTED_FILES = {
    "README.md",
    ".infoflow/vault.json",
    "📥 Inbox/README.md",
    "📥 Inbox/_index/.gitkeep",
    "📥 Inbox/YouTube-Likes/.gitkeep",
    "📥 Inbox/Snipd/.gitkeep",
    "📥 Inbox/WeRead/.gitkeep",
    "📥 Inbox/X-Bookmarks/.gitkeep",
    "📥 Inbox/Instagram-Saves/.gitkeep",
    "📥 Inbox/manual/.gitkeep",
    "📝 Journal/README.md",
    "📝 Journal/想法/digests/.gitkeep",
    "💡 Ideas/README.md",
    "📋 Digests/README.md",
    "📋 Digests/cycles/.gitkeep",
    "📖 Cognition/README.md",
}

ABSENT = (
    "📖 Resources",
    "🚀 Projects",
    "📖 Cognition/Evidence",
    "📖 Cognition/Beliefs",
    "📖 Cognition/Principles",
    "📋 Digests/daily",
    "💡 Ideas/Content",
    "💡 Ideas/Insurance",
    "💡 Ideas/Life",
    "💡 Ideas/Tech",
    "💡 Ideas/Trading",
    "💡 Ideas/General",
    ".cursor",
    "📥 Inbox/_index/sources.jsonl",
)

BANNED = (
    "iCloud~md~obsidian",
    "jakeguo117",
    "obsidian-digitalbrain",
    "/Users/jake",
    "com.jake",
    "com~apple~CloudDocs",
    "jakeguo117@gmail.com",
    "DEFAULT_VAULT",
)

P5_FILES = (
    "scripts/daily_digest.py",
    "scripts/weekly_rollup.py",
    "scripts/youtube_likes.py",
    "scripts/youtube_oauth.py",
    "scripts/sync_digitalbrain_skills.py",
    "scripts/push_intake_sources.sh",
    "scripts/run_digest_jobs.sh",
    "scripts/infoflow_config.py",
    "scripts/scaffold_empty_vault.py",
    "config.example.json",
)


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def file_set(root: Path) -> set[str]:
    found = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.relative_to(root).parts:
            continue
        found.add(path.relative_to(root).as_posix())
    return found


def assert_layout(test: unittest.TestCase, root: Path) -> None:
    test.assertEqual(file_set(root), EXPECTED_FILES)
    for rel in ABSENT:
        test.assertFalse((root / rel).exists(), rel)


class EmptyVaultScaffoldTests(unittest.TestCase):
    def test_t1_template_package_matches_section_1_1(self) -> None:
        self.assertEqual(file_set(TEMPLATE), EXPECTED_FILES)
        for rel in ABSENT:
            self.assertFalse((TEMPLATE / rel).exists(), rel)

    def test_t2_t3_t4_template_and_scaffold_have_no_private_defaults(self) -> None:
        blobs = []
        for path in TEMPLATE.rglob("*"):
            if path.is_file() and path.suffix != ".gitkeep":
                blobs.append(path.read_text(encoding="utf-8"))
        example = (PLUGIN / "config.example.json").read_text(encoding="utf-8")
        blobs.append(example)
        self.assertIn("REPLACE_WITH_VAULT_ROOT", example)
        self.assertIn("REPLACE_WITH_GIT_REMOTE", example)
        self.assertIn("REPLACE_WITH_A_OR_B", example)
        self.assertIn("REPLACE_WITH_GIT_USER_NAME", example)
        self.assertIn("REPLACE_WITH_GIT_USER_EMAIL", example)
        example_json = json.loads(example)
        self.assertEqual(example_json["git_user_name"], "REPLACE_WITH_GIT_USER_NAME")
        self.assertEqual(example_json["git_user_email"], "REPLACE_WITH_GIT_USER_EMAIL")
        joined = "\n".join(blobs)
        for banned in BANNED:
            self.assertNotIn(banned, joined)
        self.assertNotIn("Jake", joined)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            config = root / "config.json"
            rc = scaffold.main(
                ["B", "--vault-root", str(vault), "--config", str(config)]
            )
            self.assertEqual(rc, 0, "mode B scaffold failed")
            assert_layout(self, vault)
            marker = json.loads((vault / ".infoflow" / "vault.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["template_id"], "information-flow.empty-vault")
            self.assertEqual(marker["template_version"], "1")
            self.assertEqual(marker["storage_mode"], "B")
            self.assertRegex(marker["created_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
            self.assertFalse((vault / ".git").exists())
            ideas = [path.name for path in (vault / "💡 Ideas").iterdir()]
            self.assertEqual(ideas, ["README.md"])
            cognition = [path.name for path in (vault / "📖 Cognition").iterdir()]
            self.assertEqual(cognition, ["README.md"])
            written = (vault / "README.md").read_text(encoding="utf-8")
            self.assertNotIn("Jake", written)
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(saved["vault_root"], str(vault.resolve()))
            self.assertEqual(saved["storage_mode"], "B")
            self.assertNotIn("git_remote", saved)

    def test_b1_git_init_is_opt_in_and_does_not_commit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            rc = scaffold.main(
                [
                    "B",
                    "--vault-root",
                    str(vault),
                    "--git-init",
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue((vault / ".git").is_dir())
            self.assertNotEqual(git("rev-parse", "HEAD", cwd=vault).returncode, 0)
            self.assertNotEqual(git("remote", "get-url", "origin", cwd=vault).returncode, 0)

    def test_b2_rejects_code_repository_root_and_children(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = Path(raw) / "config.json"
            rc = scaffold.main(["B", "--vault-root", str(PLUGIN), "--config", str(config)])
            self.assertEqual(rc, 1)
            self.assertFalse((PLUGIN / ".infoflow" / "vault.json").exists())
            nested = PLUGIN / "scaffold-must-not-create"
            rc = scaffold.main(["B", "--vault-root", str(nested), "--config", str(config)])
            self.assertEqual(rc, 1)
            self.assertFalse(nested.exists())

    def test_a1_commits_template_and_does_not_push(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            remote = root / "remote.git"
            vault = root / "vault"
            config = root / "config.json"
            self.assertEqual(git("init", "--bare", "-b", "main", str(remote)).returncode, 0)
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    str(remote),
                    "--config",
                    str(config),
                ]
            )
            self.assertEqual(rc, 0)
            assert_layout(self, vault)
            subject = git("log", "-1", "--format=%s", cwd=vault).stdout.strip()
            self.assertEqual(subject, "initialize empty information-flow vault")
            self.assertEqual(git("ls-remote", str(remote)).stdout.strip(), "")
            saved = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(saved["storage_mode"], "A")
            self.assertEqual(saved["git_remote"], str(remote))
            self.assertEqual(saved["git_branch"], "main")
            self.assertEqual(saved["vault_root"], str(vault.resolve()))
            marker = json.loads((vault / ".infoflow" / "vault.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["storage_mode"], "A")

    def test_a2_auth_failure_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    "http://127.0.0.1:9/no-such-vault.git",
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 1)
            self.assertFalse(vault.exists())
            self.assertFalse((root / "config.json").exists())

    def test_a2_nonempty_conflict_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            vault.mkdir()
            note = vault / "notes.md"
            note.write_text("keep\n", encoding="utf-8")
            remote = root / "remote.git"
            self.assertEqual(git("init", "--bare", "-b", "main", str(remote)).returncode, 0)
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    str(remote),
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 1)
            self.assertEqual(note.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse((vault / ".infoflow").exists())
            self.assertFalse((vault / "📥 Inbox").exists())
            self.assertFalse((vault / ".git").exists())

    def test_a2_nonempty_remote_is_not_left_behind(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            remote = root / "remote.git"
            seed = root / "seed"
            seed.mkdir()
            self.assertEqual(git("init", "-b", "main", str(seed)).returncode, 0)
            git("config", "user.name", "information-flow", cwd=seed)
            git("config", "user.email", "information-flow@localhost", cwd=seed)
            (seed / "README.md").write_text("occupied\n", encoding="utf-8")
            git("add", "README.md", cwd=seed)
            self.assertEqual(git("commit", "-m", "occupied", cwd=seed).returncode, 0)
            self.assertEqual(git("init", "--bare", "-b", "main", str(remote)).returncode, 0)
            git("remote", "add", "origin", str(remote), cwd=seed)
            self.assertEqual(git("push", "origin", "main", cwd=seed).returncode, 0)
            vault = root / "vault"
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    str(remote),
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 1)
            self.assertFalse(vault.exists())

    def test_reentry_soft_fill_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            config = root / "config.json"
            self.assertEqual(
                scaffold.main(["B", "--vault-root", str(vault), "--config", str(config)]),
                0,
            )
            readme = vault / "README.md"
            readme.write_text("USER EDIT\n", encoding="utf-8")
            note = vault / "📝 Journal" / "mine.md"
            note.write_text("keep\n", encoding="utf-8")
            marker_path = vault / ".infoflow" / "vault.json"
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            marker["template_version"] = "0"
            marker_path.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
            before = marker_path.read_text(encoding="utf-8")
            shutil.rmtree(vault / "💡 Ideas")
            (vault / "📋 Digests" / "cycles" / ".gitkeep").unlink()
            config.write_text(
                json.dumps({"vault_root": "stale", "storage_mode": "B", "extra": "kept"}) + "\n",
                encoding="utf-8",
            )
            rc = scaffold.main(["B", "--vault-root", str(vault), "--config", str(config)])
            self.assertEqual(rc, 0)
            self.assertEqual(readme.read_text(encoding="utf-8"), "USER EDIT\n")
            self.assertEqual(note.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(marker_path.read_text(encoding="utf-8"), before)
            self.assertTrue((vault / "💡 Ideas" / "README.md").is_file())
            self.assertTrue((vault / "📋 Digests" / "cycles" / ".gitkeep").is_file())
            self.assertEqual(json.loads(config.read_text(encoding="utf-8"))["extra"], "kept")
            self.assertFalse((vault / ".git").exists())

    def test_a_soft_fill_commits_locally_and_still_does_not_push(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            remote = root / "remote.git"
            vault = root / "vault"
            self.assertEqual(git("init", "--bare", "-b", "main", str(remote)).returncode, 0)
            self.assertEqual(
                scaffold.main(
                    [
                        "A",
                        "--vault-root",
                        str(vault),
                        "--git-remote",
                        str(remote),
                        "--config",
                        str(root / "config.json"),
                    ]
                ),
                0,
            )
            (vault / "README.md").write_text("USER EDIT\n", encoding="utf-8")
            removed = "📋 Digests/cycles/.gitkeep"
            self.assertEqual(git("rm", "-q", "--", removed, cwd=vault).returncode, 0)
            self.assertEqual(
                git("commit", "-m", "drop cycles placeholder", cwd=vault).returncode,
                0,
            )
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    str(remote),
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertEqual((vault / "README.md").read_text(encoding="utf-8"), "USER EDIT\n")
            self.assertTrue((vault / "📋 Digests" / "cycles" / ".gitkeep").is_file())
            count = git("rev-list", "--count", "HEAD", cwd=vault).stdout.strip()
            self.assertEqual(count, "3")
            subject = git("log", "-1", "--format=%s", cwd=vault).stdout.strip()
            self.assertEqual(subject, "fill missing empty-vault template paths")
            names = git(
                "-c",
                "core.quotepath=false",
                "show",
                "--name-only",
                "--format=",
                "HEAD",
                cwd=vault,
            ).stdout
            self.assertIn(removed, names)
            self.assertNotIn("README.md", names)
            self.assertEqual(git("ls-remote", str(remote)).stdout.strip(), "")

    def test_template_id_mismatch_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            self.assertEqual(
                scaffold.main(
                    ["B", "--vault-root", str(vault), "--config", str(root / "config.json")]
                ),
                0,
            )
            marker_path = vault / ".infoflow" / "vault.json"
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            marker["template_id"] = "other-template"
            marker_path.write_text(json.dumps(marker) + "\n", encoding="utf-8")
            shutil.rmtree(vault / "💡 Ideas")
            rc = scaffold.main(
                ["B", "--vault-root", str(vault), "--config", str(root / "config.json")]
            )
            self.assertEqual(rc, 1)
            self.assertFalse((vault / "💡 Ideas").exists())

    def test_disk_failure_on_new_vault_leaves_no_tree(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            calls = {"n": 0}
            real = scaffold.write_bytes

            def boom(path: Path, data: bytes) -> None:
                calls["n"] += 1
                if calls["n"] == 3:
                    raise OSError(28, "No space left on device")
                real(path, data)

            with patch.object(scaffold, "write_bytes", boom):
                rc = scaffold.main(
                    ["B", "--vault-root", str(vault), "--config", str(root / "config.json")]
                )
            self.assertEqual(rc, 1)
            self.assertFalse(vault.exists())
            self.assertFalse((root / "config.json").exists())

    def test_disk_failure_on_existing_empty_dir_restores_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            vault.mkdir()
            calls = {"n": 0}
            real = scaffold.write_bytes

            def boom(path: Path, data: bytes) -> None:
                calls["n"] += 1
                if calls["n"] == 2:
                    raise OSError(28, "No space left on device")
                real(path, data)

            with patch.object(scaffold, "write_bytes", boom):
                rc = scaffold.main(
                    ["B", "--vault-root", str(vault), "--config", str(root / "config.json")]
                )
            self.assertEqual(rc, 1)
            self.assertTrue(vault.is_dir())
            self.assertEqual(list(vault.iterdir()), [])

    def test_refuses_push_and_does_not_index(self) -> None:
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.run_git(["push", "origin", "main"])
        source = Path(scaffold.__file__).read_text(encoding="utf-8")
        self.assertNotIn("inbox_index", source)
        self.assertIn("manual Workflow", source)
        help_run = subprocess.run(
            [sys.executable, str(Path(scaffold.__file__)), "-h"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(help_run.returncode, 0)
        self.assertIn("does not set up posting", help_run.stdout)
        self.assertIn("does not run an inbox index", help_run.stdout.lower())

    def test_c1_scripts_have_no_personal_vault_default(self) -> None:
        for rel in P5_FILES:
            text = (PLUGIN / rel).read_text(encoding="utf-8")
            for banned in BANNED:
                self.assertNotIn(banned, text, f"{rel} contains {banned}")
        with patch.dict(os.environ, {"INFOFLOW_CONFIG": "/tmp/infoflow-missing-config.json"}, clear=False):
            os.environ.pop("INFOFLOW_VAULT_ROOT", None)
            os.environ.pop("INFOFLOW_GIT_REMOTE", None)
            for fn in (
                daily_digest.vault_path,
                weekly_rollup.vault_path,
                sync.vault_path,
                youtube_likes.vault_path,
            ):
                with self.assertRaises(SystemExit) as caught:
                    fn(None)
                message = str(caught.exception.code)
                self.assertNotIn("DigitalBrain", message)
                self.assertNotIn("iCloud", message)
            for fn in (youtube_likes.client_path, youtube_oauth.client_path, youtube_likes.token_path):
                os.environ.pop("YOUTUBE_CLIENT_FILE", None)
                os.environ.pop("YOUTUBE_TOKEN_FILE", None)
                with self.assertRaises(SystemExit) as caught:
                    fn()
                self.assertNotIn("CloudDocs", str(caught.exception.code))

    def test_c2_and_x1_template_stays_out_of_user_notes_and_skill_copies(self) -> None:
        for path in TEMPLATE.rglob("*"):
            self.assertNotIn(".cursor", path.parts)
            self.assertNotEqual(path.name, "SKILL.md")
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            self.assertEqual(
                scaffold.main(
                    ["B", "--vault-root", str(vault), "--config", str(Path(raw) / "config.json")]
                ),
                0,
            )
            resolved = vault.resolve()
            self.assertNotEqual(resolved, PLUGIN.resolve())
            self.assertFalse(PLUGIN.resolve() in resolved.parents)
            self.assertFalse(resolved.is_relative_to(PLUGIN.resolve()))

    def test_local_switchover_doc_has_no_personal_defaults(self) -> None:
        doc = PLUGIN / "docs" / "onboarding" / "local-switchover.md"
        text = doc.read_text(encoding="utf-8")
        for banned in (
            "/Users/jake",
            "jakeguo",
            "iCloud~md~obsidian",
            "obsidian-digitalbrain",
            "@gmail",
        ):
            self.assertNotIn(banned, text)
        for required in (
            "INFOFLOW_CONFIG",
            "INFOFLOW_VAULT_ROOT",
            "YOUTUBE_CLIENT_FILE",
            "YOUTUBE_TOKEN_FILE",
            "INTAKE_GIT_USER_NAME",
            "INTAKE_GIT_USER_EMAIL",
            "git_user_name",
            "git_user_email",
            "REPLACE_WITH_GIT_USER_NAME",
            "REPLACE_WITH_GIT_USER_EMAIL",
            "launchctl bootout",
            "launchctl kickstart",
            "daily-intake.yml",
            "sync-digitalbrain-skills.yml",
            "weekly-digest.yml",
            "push_intake_sources.sh",
            "run_digest_jobs.sh",
            "REPLACE_WITH_VAULT_ROOT",
            "REPLACE_WITH_GIT_REMOTE",
            "plugins/information-flow",
            "cursor/cognition-v1.1",
            "reconcile_live_vault_untracked.py",
            "com.jake.intake-source-push",
            "com.jake.digitalbrain-reconcile",
            "push_intake_sources rc",
            "不要删除",
        ):
            self.assertIn(required, text)
        self.assertNotIn("Git 身份**不在**", text)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        runtime = readme.split("## Runtime (not in git)", 1)[1].split("## ", 1)[0]
        self.assertIn("config.json", runtime)
        self.assertIn("docs/onboarding/local-switchover.md", runtime)
        self.assertIn("YOUTUBE_CLIENT_FILE", runtime)
        self.assertIn("YOUTUBE_TOKEN_FILE", runtime)
        self.assertIn("git_user_name", runtime)
        self.assertIn("git_user_email", runtime)
        self.assertNotIn(".secrets/youtube/", runtime)
        push = (PLUGIN / "scripts" / "push_intake_sources.sh").read_text(encoding="utf-8")
        self.assertIn('get git_user_name', push)
        self.assertIn('get git_user_email', push)
        self.assertNotIn("INTAKE_GIT_USER_NAME and INTAKE_GIT_USER_EMAIL are required", push)
        wrapper = (PLUGIN / "scripts" / "run_intake_source_push.applescript").read_text(
            encoding="utf-8"
        )
        self.assertIn("INTAKE_GIT_USER_NAME", wrapper)
        self.assertIn("on envAssign", wrapper)

    def test_git_identity_env_overrides_config_and_push_script_reads_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            cfg = root / "config.json"
            cfg.write_text(
                json.dumps(
                    {
                        "git_user_name": "config-name",
                        "git_user_email": "config@example.com",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"INFOFLOW_CONFIG": str(cfg)}, clear=False):
                os.environ.pop("INTAKE_GIT_USER_NAME", None)
                os.environ.pop("INTAKE_GIT_USER_EMAIL", None)
                self.assertEqual(infoflow_config.require_setting("git_user_name"), "config-name")
                self.assertEqual(
                    infoflow_config.require_setting("git_user_email"), "config@example.com"
                )
            with patch.dict(
                os.environ,
                {
                    "INFOFLOW_CONFIG": str(cfg),
                    "INTAKE_GIT_USER_NAME": "env-name",
                    "INTAKE_GIT_USER_EMAIL": "env@example.com",
                },
                clear=False,
            ):
                self.assertEqual(infoflow_config.require_setting("git_user_name"), "env-name")
                self.assertEqual(
                    infoflow_config.require_setting("git_user_email"), "env@example.com"
                )
            with patch.dict(os.environ, {"INTAKE_GIT_USER_NAME": "REPLACE_WITH_GIT_USER_NAME"}):
                with self.assertRaises(SystemExit) as caught:
                    infoflow_config.require_setting("git_user_name", config_file=str(cfg))
                self.assertIn("placeholder", str(caught.exception))

            missing_vault = str(root / "missing-vault")
            reached = self._run_push(cfg, INTAKE_VAULT=missing_vault)
            self.assertNotEqual(reached.returncode, 0)
            self.assertIn("vault missing", reached.stderr)
            self.assertNotIn("missing git_user_name", reached.stderr)

            empty = root / "empty.json"
            empty.write_text("{}", encoding="utf-8")
            no_identity = self._run_push(empty, INTAKE_VAULT=missing_vault)
            self.assertNotEqual(no_identity.returncode, 0)
            self.assertIn("missing git_user_name", no_identity.stderr)

            from_env = self._run_push(
                empty,
                INTAKE_VAULT=missing_vault,
                INTAKE_GIT_USER_NAME="env-name",
                INTAKE_GIT_USER_EMAIL="env@example.com",
            )
            self.assertIn("vault missing", from_env.stderr)
            self.assertNotIn("missing git_user_name", from_env.stderr)

    def _run_push(self, cfg: Path, **extra: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in (
            "INTAKE_GIT_USER_NAME",
            "INTAKE_GIT_USER_EMAIL",
            "INTAKE_VAULT",
            "INTAKE_SOURCE_REMOTE",
            "INFOFLOW_VAULT_ROOT",
            "INFOFLOW_GIT_REMOTE",
            "INFOFLOW_CONFIG",
            "INFOFLOW_GIT_BRANCH",
            "INFOFLOW_STORAGE_MODE",
        ):
            env.pop(key, None)
        env["INFOFLOW_CONFIG"] = str(cfg)
        env["INTAKE_SOURCE_ICLOUD_WAIT"] = "0"
        env["INTAKE_SOURCE_REMOTE"] = "git@example.invalid:vault.git"
        env.update(extra)
        return subprocess.run(
            ["/bin/sh", str(PLUGIN / "scripts" / "push_intake_sources.sh")],
            cwd=PLUGIN,
            env=env,
            text=True,
            capture_output=True,
        )

    def test_placeholder_remote_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            rc = scaffold.main(
                [
                    "A",
                    "--vault-root",
                    str(vault),
                    "--git-remote",
                    "REPLACE_WITH_GIT_REMOTE",
                    "--config",
                    str(root / "config.json"),
                ]
            )
            self.assertEqual(rc, 1)
            self.assertFalse(vault.exists())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
