#!/usr/bin/env python3
"""Synthetic tests for vault recovery. No live vault and no private prose."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

import vault_recovery as recovery


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class MemoryStore:
    def __init__(self, items: dict[str, str] | None = None) -> None:
        self.items = dict(items or {})

    def get(self, account: str) -> str | None:
        return self.items.get(account)

    def put(self, account: str, value: str) -> None:
        self.items[account] = value


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.raw

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


class FakeOpener:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout: int = 60):
        self.requests.append(request)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResponse(item)


def auth_payload() -> dict:
    return {
        "accountId": "acct",
        "authorizationToken": "tok",
        "apiUrl": "https://api.example.test",
        "s3ApiUrl": "https://s3.example.test",
        "allowed": {
            "capabilities": ["listBuckets", "writeBuckets", "readFiles", "writeFiles"]
        },
    }


class StatefulFiles:
    def __init__(self, dataless: set[Path]) -> None:
        self.dataless = set(dataless)
        self.downloads: list[Path] = []

    def stat(self, path: Path) -> recovery.FileStat:
        info = recovery.file_stat(path)
        if path in self.dataless:
            return recovery.FileStat(info.size, 0, recovery.SF_DATALESS, info.mode, False)
        return info

    def download(self, path: Path) -> None:
        self.downloads.append(path)
        self.dataless.discard(path)


class RecoveryTests(unittest.TestCase):
    def test_dataless_flag_and_empty_blocks(self) -> None:
        self.assertTrue(recovery.is_dataless(10, 8, recovery.SF_DATALESS))
        self.assertTrue(recovery.is_dataless(10, 0, 0))
        self.assertFalse(recovery.is_dataless(10, 8, 0))
        self.assertFalse(recovery.is_dataless(0, 0, 0))

    def test_download_command_never_evicts(self) -> None:
        command = recovery.download_command(Path("/tmp/note.md"))
        self.assertEqual(command[:2], ["/usr/bin/brctl", "download"])
        self.assertNotIn("evict", command)

    def test_read_hydrates_dataless_file_without_rewriting(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            note = root / "note.md"
            note.write_text("synthetic bytes\n", encoding="utf-8")
            before = note.read_bytes()
            state = StatefulFiles({note})
            report = recovery.read_tree(
                root,
                stat_fn=state.stat,
                download_fn=state.download,
                sleep_fn=lambda _seconds: None,
                attempts=2,
                workers=1,
            )
            self.assertTrue(report.ok)
            self.assertEqual(report.bytes_read, len(before))
            self.assertEqual(note.read_bytes(), before)
            self.assertEqual(state.downloads, [note])

    def test_read_blocks_when_hydration_does_not_clear_dataless(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            note = root / "note.md"
            note.write_bytes(b"abc")
            state = StatefulFiles({note})
            report = recovery.read_tree(
                root,
                stat_fn=state.stat,
                download_fn=lambda _path: None,
                sleep_fn=lambda _seconds: None,
                attempts=1,
                workers=1,
            )
            self.assertFalse(report.ok)
            self.assertEqual(report.dataless, 1)
            self.assertEqual(note.read_bytes(), b"abc")

    def test_structure_keeps_prose_out_of_the_signature(self) -> None:
        data = (
            "---\n"
            "date: 2026-01-01\n"
            "---\n"
            "See [[Alpha]] and [[Beta#section|alias]].\n"
            "synthetic private prose\n"
        ).encode("utf-8")
        signature = recovery.markdown_structure(data)
        encoded = json.dumps(signature)
        self.assertEqual(signature["frontmatter_keys"], ["date"])
        self.assertEqual(signature["wikilink_count"], 2)
        self.assertNotIn("synthetic private prose", encoded)
        self.assertNotIn("Alpha", encoded)
        again = recovery.markdown_structure(data)
        self.assertEqual(signature["wikilink_digest"], again["wikilink_digest"])

    def test_restore_target_must_stay_outside_the_vault(self) -> None:
        vault = Path("/tmp/vault-root")
        with self.assertRaises(recovery.RecoveryError):
            recovery.assert_isolated_target(vault, vault)
        with self.assertRaises(recovery.RecoveryError):
            recovery.assert_isolated_target(vault / "child", vault)
        with self.assertRaises(recovery.RecoveryError):
            recovery.assert_isolated_target(Path("/tmp"), vault)
        with self.assertRaises(recovery.RecoveryError):
            recovery.assert_isolated_target(Path("/"), vault)
        self.assertEqual(
            recovery.assert_isolated_target(Path("/tmp/if-restore-out"), vault),
            Path("/tmp/if-restore-out").resolve(),
        )

    def test_secret_material_stays_out_of_restic_argv_and_errors(self) -> None:
        password = "test-password-value"
        env = recovery.restic_env("/tmp/restic-repo", password)
        command = recovery.restic_command(["backup", "--json"], binary="restic")
        self.assertNotIn(password, command)
        self.assertNotIn("AWS_ACCESS_KEY_ID", env)
        bag = recovery.SecretBag()
        bag.add(password)
        self.assertNotIn(password, bag.scrub(f"failed with {password}"))
        short = "pw"
        bag.add(short)
        self.assertEqual(bag.scrub(f"failed {short}"), "failed [redacted]")

    def test_backup_summary_drops_file_names(self) -> None:
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "message_type": "status",
                        "current_files": ["Journal/private-title.md"],
                    }
                ),
                json.dumps(
                    {
                        "message_type": "summary",
                        "snapshot_id": "abc123",
                        "files_new": 1,
                        "total_files_processed": 1,
                        "total_bytes_processed": 4,
                    }
                ),
            ]
        ).encode("utf-8")
        summary = recovery.parse_backup_summary(stdout)
        self.assertEqual(summary["snapshot_id"], "abc123")
        self.assertNotIn("private-title", json.dumps(summary))

    def test_backup_refuses_unreadable_tree_before_restic(self) -> None:
        def fail_run(*_args):
            raise AssertionError("restic should not run")

        with self.assertRaises(recovery.RecoveryError) as caught:
            recovery.backup_snapshot(
                Path("/tmp"),
                "/tmp/repo",
                "test-password-value",
                None,
                None,
                run=fail_run,
                preflight=recovery.TreeReport(files=1, dataless=1),
            )
        self.assertEqual(caught.exception.code, 3)

    def test_provision_creates_a_private_bucket_and_stores_the_url(self) -> None:
        store = MemoryStore(
            {
                "b2-key-id": "key-id-value",
                "b2-application-key": "app-key-value",
            }
        )
        opener = FakeOpener(
            [
                auth_payload(),
                {"buckets": []},
                {"bucketName": "jdw-recovery-fixedname01", "bucketType": "allPrivate"},
                {
                    "buckets": [
                        {
                            "bucketName": "jdw-recovery-fixedname01",
                            "bucketType": "allPrivate",
                        }
                    ]
                },
            ]
        )
        repository = recovery.resolve_repository(
            store,
            opener,
            name_fn=lambda: "jdw-recovery-fixedname01",
        )
        self.assertEqual(
            repository,
            "s3:s3.example.test/jdw-recovery-fixedname01/digitalbrain",
        )
        self.assertEqual(store.get("restic-repository"), repository)
        created = json.loads(opener.requests[2].data.decode("utf-8"))
        self.assertEqual(created["bucketType"], "allPrivate")
        self.assertNotIn("app-key-value", repository)

    def test_provision_rejects_a_public_bucket(self) -> None:
        store = MemoryStore(
            {
                "b2-key-id": "key-id-value",
                "b2-application-key": "app-key-value",
                "restic-repository": "s3:s3.example.test/visible-bucket/digitalbrain",
            }
        )
        opener = FakeOpener(
            [
                auth_payload(),
                {
                    "buckets": [
                        {"bucketName": "visible-bucket", "bucketType": "allPublic"}
                    ]
                },
            ]
        )
        with self.assertRaises(recovery.RecoveryError) as caught:
            recovery.resolve_repository(store, opener)
        self.assertIn("not private", str(caught.exception))
        self.assertNotIn("app-key-value", str(caught.exception))

    def test_authorize_failure_does_not_include_the_key(self) -> None:
        store = MemoryStore(
            {"b2-key-id": "key-id-value", "b2-application-key": "app-key-value"}
        )
        error = urllib.error.HTTPError(
            "https://api.example.test",
            401,
            "unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"code":"unauthorized"}'),
        )
        opener = FakeOpener([error])
        with self.assertRaises(recovery.RecoveryError) as caught:
            recovery.resolve_repository(store, opener)
        self.assertNotIn("app-key-value", str(caught.exception))

    def test_git_counts_use_a_copied_index(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            env = os.environ.copy()
            env.update(
                {
                    "GIT_AUTHOR_NAME": "Test",
                    "GIT_AUTHOR_EMAIL": "test@example.com",
                    "GIT_COMMITTER_NAME": "Test",
                    "GIT_COMMITTER_EMAIL": "test@example.com",
                }
            )

            def git(*args: str) -> None:
                subprocess.run(
                    ["git", "-C", str(root), *args],
                    check=True,
                    capture_output=True,
                    env=env,
                )

            git("init")
            write(root / "a.txt", "a\n")
            write(root / "b.txt", "b\n")
            write(root / "c.txt", "c\n")
            git("add", "a.txt", "b.txt", "c.txt")
            git("commit", "-m", "base")
            write(root / "a.txt", "changed\n")
            (root / "b.txt").unlink()
            write(root / "c.txt", "staged\n")
            git("add", "c.txt")
            write(root / "d.txt", "new\n")
            before = (root / ".git" / "index").stat().st_mtime_ns
            names_before = set(os.listdir(root))
            counts = recovery.git_status_counts(root)
            after = (root / ".git" / "index").stat().st_mtime_ns
            self.assertEqual(before, after)
            self.assertEqual(names_before, set(os.listdir(root)))
            self.assertEqual(counts["modified"], 2)
            self.assertEqual(counts["deleted"], 1)
            self.assertEqual(counts["untracked"], 1)
            self.assertEqual(counts["staged"], 1)

    def test_evidence_file_is_private_and_outside_the_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw).resolve() / "evidence.json"
            recovery.write_evidence(path, {"snapshot_id": "abc", "ok": True})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertNotIn("prose", path.read_text(encoding="utf-8"))
        with self.assertRaises(recovery.RecoveryError):
            recovery.write_evidence(recovery.PLUGIN_ROOT / "evidence.json", {"ok": True})

    def test_cli_scan_reports_aggregates_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root / "📝 Journal" / "2026-01-01 synthetic.md", "hello\n")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = recovery.main(["scan", "--root", str(root)])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["files"], 1)
            self.assertEqual(payload["markdown"], 1)
            self.assertNotIn("hello", stdout.getvalue())

    def test_cli_rejects_a_keychain_inside_the_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            code = recovery.main(
                ["--keychain", str(recovery.PLUGIN_ROOT / "temp.keychain"), "scan", "--root", raw]
            )
        self.assertEqual(code, 2)

    def test_temp_keychain_roundtrip(self) -> None:
        if shutil.which("security") is None:
            self.skipTest("security is not available")
        listed = subprocess.run(
            ["security", "list-keychains", "-d", "user"],
            check=True,
            capture_output=True,
            text=True,
        )
        original = [line.strip().strip('"') for line in listed.stdout.splitlines() if line.strip()]
        default = subprocess.run(
            ["security", "default-keychain"],
            check=True,
            capture_output=True,
            text=True,
        )
        original_default = default.stdout.strip().strip('"')
        with tempfile.TemporaryDirectory() as raw:
            keychain = Path(raw).resolve() / "recovery-test.keychain-db"
            password = "temp-keychain-pass"
            secret = "temp-restic-secret"
            try:
                created = subprocess.run(
                    ["security", "create-keychain", "-p", password, str(keychain)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if created.returncode != 0:
                    self.skipTest("temporary keychain could not be created")
                subprocess.run(
                    ["security", "unlock-keychain", "-p", password, str(keychain)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                store = recovery.KeychainStore(
                    service="jake.information-flow.vault-recovery-test",
                    keychain=keychain,
                )
                store.put("restic-password", secret)
                self.assertEqual(store.get("restic-password"), secret)
                self.assertIsNone(store.get("missing-account"))
            finally:
                subprocess.run(
                    ["security", "default-keychain", "-s", original_default],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["security", "list-keychains", "-d", "user", "-s", *original],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["security", "delete-keychain", str(keychain)],
                    check=False,
                    capture_output=True,
                    text=True,
                )

    def test_local_restic_readback_and_isolated_restore(self) -> None:
        if shutil.which("restic") is None:
            self.skipTest("restic is not installed")
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            vault = base / "vault"
            repo = base / "repo"
            sibling = base / "sibling-keep.txt"
            sibling.write_text("keep\n")
            journal = "---\ndate: 2026-01-01\n---\nSee [[Synthetic Target]]\n"
            write(vault / "📝 Journal" / "2026-01-01 synthetic.md", journal)
            write(vault / "📥 Inbox" / "source.md", "inbox synthetic\n")
            write(
                vault / "📖 Cognition" / "Evidence" / "evidence.md",
                "---\nid: evidence-synthetic\n---\n[[Synthetic Target]]\n",
            )
            write(vault / "other.txt", "other\n")
            (vault / "empty-dir").mkdir()
            link = vault / "link.txt"
            link.symlink_to("other.txt")
            summary = recovery.backup_snapshot(
                vault,
                str(repo),
                "test-password-value",
                None,
                None,
            )
            snapshot_id = str(summary["snapshot_id"])
            self.assertGreaterEqual(summary["repo_config_version"], 1)
            self.assertTrue(summary["check_ok"])
            readback = recovery.readback_snapshot(
                vault,
                snapshot_id,
                str(repo),
                "test-password-value",
            )
            self.assertGreater(readback["checked"], 0)
            self.assertEqual(readback["checked"], readback["byte_matches"])
            target = base / "restore-out"
            result = recovery.restore_check(
                vault,
                snapshot_id,
                str(repo),
                "test-password-value",
                target=target,
            )
            self.assertEqual(result["comparison"]["missing"], 0)
            self.assertEqual(result["comparison"]["mismatched"], 0)
            self.assertEqual(result["structure"]["checked"], result["structure"]["matched"])
            self.assertTrue(target.is_dir())
            self.assertEqual(result["restore_path"], str(target))
            self.assertEqual(sibling.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual((vault / "other.txt").read_text(encoding="utf-8"), "other\n")

    def test_local_repository_requires_mounted_external_volume(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            vault.mkdir()
            with self.assertRaises(recovery.RecoveryError):
                recovery.local_repository_path(str(Path(raw) / "repo"), vault)
            with self.assertRaises(recovery.RecoveryError):
                recovery.local_repository_path(str(vault / "repo"), vault)

    def test_local_runtime_needs_only_restic_password(self) -> None:
        store = MemoryStore({"restic-password": "synthetic-password"})
        with mock.patch.object(recovery, "KeychainStore", return_value=store), mock.patch.object(
            recovery, "local_repository_path", return_value="/Volumes/Disk/new-repo"
        ):
            _, password, repository, key_id, app_key = recovery.load_runtime(
                None, "/Volumes/Disk/new-repo", Path("/tmp/vault")
            )
        self.assertEqual(password, "synthetic-password")
        self.assertEqual(repository, "/Volumes/Disk/new-repo")
        self.assertIsNone(key_id)
        self.assertIsNone(app_key)

    def test_existing_non_repo_path_is_never_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            existing = base / "existing"
            existing.mkdir()
            write(existing / "unrelated.txt", "keep\n")
            commands = []

            def run(args, _env):
                commands.append(args)
                return recovery.CommandResult(1, b"", "not a repository")

            with self.assertRaises(recovery.RecoveryError):
                recovery.ensure_restic_repo(
                    run, {"RESTIC_REPOSITORY": str(existing)}, recovery.SecretBag()
                )
            self.assertEqual(commands, [["snapshots", "--json"]])
            self.assertEqual((existing / "unrelated.txt").read_text(), "keep\n")

    def test_new_local_repository_does_not_touch_existing_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            sibling = base / "sibling"
            sibling.mkdir()
            write(sibling / "keep.txt", "keep\n")
            repo = base / "new-repo"
            seen = []

            def run(args, _env):
                contents = sorted(path.name for path in repo.iterdir()) if repo.exists() else None
                seen.append((args[0], repo.exists(), contents))
                if args[0] == "snapshots":
                    return recovery.CommandResult(1, b"", "not a repository")
                if args[0] == "init":
                    return recovery.CommandResult(0, b"", "")
                raise AssertionError(args)

            recovery.ensure_restic_repo(
                run, {"RESTIC_REPOSITORY": str(repo)}, recovery.SecretBag()
            )
            self.assertEqual(seen[0][0], "snapshots")
            self.assertFalse(seen[0][1])
            self.assertEqual(seen[1], ("init", True, []))
            self.assertEqual((sibling / "keep.txt").read_text(encoding="utf-8"), "keep\n")

    def test_new_repository_is_not_created_through_a_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            real = base / "real"
            real.mkdir()
            link = base / "link"
            link.symlink_to(real, target_is_directory=True)
            commands = []

            def run(args, _env):
                commands.append(args)
                return recovery.CommandResult(1, b"", "not a repository")

            with self.assertRaises(recovery.RecoveryError):
                recovery.ensure_restic_repo(
                    run,
                    {"RESTIC_REPOSITORY": str(link / "repo")},
                    recovery.SecretBag(),
                )
            self.assertEqual(commands, [["snapshots", "--json"]])
            self.assertEqual(list(real.iterdir()), [])

    def test_local_repository_rejects_a_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            vault = base / "vault"
            vault.mkdir()
            real = base / "real"
            real.mkdir()
            link = base / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(recovery.RecoveryError):
                recovery.local_repository_path(str(link), vault)
            self.assertEqual(list(real.iterdir()), [])

    def test_restore_refuses_existing_directory_and_symlink_redirects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            vault = base / "vault"
            vault.mkdir()
            write(vault / "keep.txt", "vault\n")
            unrelated = base / "unrelated"
            unrelated.mkdir()
            write(unrelated / "keep.txt", "keep\n")
            existing = base / "restore-out"
            existing.mkdir()
            write(existing / "keep.txt", "keep\n")
            link = base / "link"
            link.symlink_to(unrelated, target_is_directory=True)

            def fail(*_args):
                raise AssertionError("restic should not run")

            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_check(
                    vault, "snap", str(base / "repo"), "pw", target=existing, run=fail
                )
            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_check(
                    vault, "snap", str(base / "repo"), "pw", target=link / "out", run=fail
                )
            inside = base / "repo" / "nested"
            (base / "repo").mkdir()
            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_check(
                    vault, "snap", str(base / "repo"), "pw", target=inside, run=fail
                )
            self.assertEqual((existing / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertEqual((unrelated / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            self.assertFalse((unrelated / "out").exists())
            self.assertFalse(inside.exists())
            self.assertEqual((vault / "keep.txt").read_text(encoding="utf-8"), "vault\n")

    def test_default_restore_is_not_created_inside_the_vault(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw).resolve() / "vault"
            vault.mkdir()
            write(vault / "keep.txt", "keep\n")
            before = set(Path("/private/tmp").glob("if-3b-b1-restore-*"))

            def fail(*_args):
                raise AssertionError("restic should not run")

            try:
                with mock.patch.dict(os.environ, {"TMPDIR": str(vault)}):
                    with self.assertRaises(AssertionError):
                        recovery.restore_check(
                            vault,
                            "snap",
                            str(Path(raw).resolve() / "repo"),
                            "pw",
                            run=fail,
                        )
                self.assertEqual([path.name for path in vault.iterdir()], ["keep.txt"])
                self.assertEqual((vault / "keep.txt").read_text(encoding="utf-8"), "keep\n")
            finally:
                created = set(Path("/private/tmp").glob("if-3b-b1-restore-*")) - before
                for path in created:
                    if path.is_dir() and not path.is_symlink():
                        shutil.rmtree(path)

    def test_evidence_symlink_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw).resolve()
            real = base / "real.json"
            real.write_text("original\n", encoding="utf-8")
            link = base / "link.json"
            link.symlink_to(real)
            with self.assertRaises(recovery.RecoveryError):
                recovery.write_evidence(link, {"ok": True})
            self.assertEqual(real.read_text(encoding="utf-8"), "original\n")

    def test_keychain_put_keeps_the_secret_out_of_argv(self) -> None:
        secret = "synthetic-restic-secret"
        calls = []

        def fake_run(command, **kwargs):
            calls.append((list(command), kwargs.get("input")))
            if command[:2] == ["security", "default-keychain"] and len(command) == 2:
                completed = subprocess.CompletedProcess(command, 0, "", "")
                completed.stdout = '"/Users/jake/Library/Keychains/login.keychain-db"\n'
                completed.stderr = ""
                return completed
            if command[:3] == ["security", "default-keychain", "-s"]:
                return subprocess.CompletedProcess(command, 0, "", "")
            if "add-generic-password" in command:
                return subprocess.CompletedProcess(command, 0, "", "password data for new item:")
            if "find-generic-password" in command:
                completed = subprocess.CompletedProcess(command, 0, "", "")
                completed.stdout = secret + "\n"
                completed.stderr = ""
                return completed
            raise AssertionError(command)

        with mock.patch.object(recovery.subprocess, "run", side_effect=fake_run):
            recovery.KeychainStore(keychain=Path("/private/tmp/test.keychain-db")).put(
                "restic-password", secret
            )
        self.assertTrue(calls)
        for command, stdin in calls:
            self.assertNotIn(secret, command)
        writes = [stdin for command, stdin in calls if "add-generic-password" in command]
        self.assertEqual(writes, [f"{secret}\n{secret}\n"])
        restores = [command for command, _stdin in calls if command[:3] == ["security", "default-keychain", "-s"]]
        self.assertEqual(restores[-1][-1], "/Users/jake/Library/Keychains/login.keychain-db")

    def test_backup_commands_do_not_forget_or_prune(self) -> None:
        seen = []

        def run(args, _env):
            seen.append(list(args))
            if args[0] == "snapshots":
                return recovery.CommandResult(0, b"[]", "")
            if args[0] == "cat":
                return recovery.CommandResult(0, b'{"version": 2}\n', "")
            if args[0] == "backup":
                body = json.dumps(
                    {
                        "message_type": "summary",
                        "snapshot_id": "abc123",
                        "total_files_processed": 1,
                        "total_bytes_processed": 1,
                    }
                ).encode()
                return recovery.CommandResult(0, body, "")
            if args[0] == "check":
                return recovery.CommandResult(0, b"", "")
            raise AssertionError(args)

        summary = recovery.backup_snapshot(
            Path("/tmp/synthetic-vault"),
            "s3:s3.example.test/bucket/digitalbrain",
            "test-password-value",
            "key-id-value",
            "app-key-value",
            run=run,
            preflight=recovery.TreeReport(),
        )
        self.assertEqual(summary["snapshot_id"], "abc123")
        allowed = {"snapshots", "cat", "backup", "check"}
        self.assertTrue(seen)
        for command in seen:
            self.assertIn(command[0], allowed)
            self.assertFalse({"forget", "prune", "--delete"} & set(command))
            self.assertNotIn("test-password-value", command)
            self.assertNotIn("app-key-value", command)


if __name__ == "__main__":
    unittest.main()
