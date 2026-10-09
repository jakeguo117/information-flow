#!/usr/bin/env python3
"""Synthetic thought-capture checks. Temp vaults and a local bare remote only."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
JOURNAL_TOOLS = ROOT / "skills" / "journal" / "tools"
sys.path.insert(0, str(JOURNAL_TOOLS))

import capture_thought  # noqa: E402
import journal_lib  # noqa: E402
import thought_lib  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
VERBATIM = "  合成原话：先放着，一字不改。\n原话:\n第二行"


def run_json(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    body = proc.stdout.strip() or "{}"
    return proc.returncode, json.loads(body)


def at(raw: str) -> datetime:
    return thought_lib.parse_instant(raw)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def write_words(root: Path, text: str) -> Path:
    path = root / f"words-{len(list(root.glob('words-*')))}.txt"
    write_text(path, text)
    return path


def journal_approval(**overrides: object) -> dict:
    data: dict = {
        "event_id": "AIC-SYN-JOURNAL-0001",
        "confirmed": True,
        "phrase": "OK 写",
        "date": "2026-10-05",
        "journal_number": 1,
        "title": "合成周记一",
        "body": "合成正文。不是私人日记。\n\n---\n",
        "topics": ["[[Synthetic Project Alpha]]"],
        "previous": "",
    }
    data.update(overrides)
    if data.get("confirmed") is True and data.get("phrase") in journal_lib.CONFIRM_PHRASES:
        rendered = journal_lib.render_journal(data)
        data["payload_sha256"] = journal_lib.fingerprint(rendered)
    return data


def save_journal(vault: Path, approval: dict) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        return run_json(
            [
                sys.executable,
                str(JOURNAL_TOOLS / "write_journal.py"),
                "save",
                "--vault",
                str(vault),
                "--approval",
                str(path),
            ]
        )


def capture(vault: Path, verbatim: str, when: str, thought_id: str | None = None) -> dict:
    result, ok = thought_lib.add_thought(vault, verbatim, at(when), thought_id)
    if not ok and result.get("status") not in {"refused", "already_persisted"}:
        raise AssertionError(result)
    return result


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def init_repo(root: Path) -> tuple[Path, Path]:
    vault = root / "vault"
    remote = root / "remote.git"
    vault.mkdir()
    subprocess.check_call(["git", "init", "--bare", "-b", "main", str(remote)])
    subprocess.check_call(["git", "init", "-b", "main", str(vault)])
    for args in (
        ["config", "user.email", "synthetic@example.com"],
        ["config", "user.name", "Synthetic"],
        ["config", "commit.gpgsign", "false"],
        ["config", "core.autocrlf", "false"],
    ):
        subprocess.check_call(["git", *args], cwd=vault)
    write_text(vault / "README.md", "synthetic\n")
    subprocess.check_call(["git", "add", "README.md"], cwd=vault)
    subprocess.check_call(["git", "commit", "-m", "init"], cwd=vault)
    subprocess.check_call(["git", "remote", "add", "origin", str(remote)], cwd=vault)
    subprocess.check_call(["git", "push", "-u", "origin", "main"], cwd=vault)
    return vault, remote


def remote_names(remote: Path, rev: str = "main") -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "--git-dir", str(remote), "diff-tree", "--no-commit-id", "--name-status", "-r", "-z", rev],
        capture_output=True,
        check=True,
    )
    parts = proc.stdout.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    rows: list[tuple[str, str]] = []
    for offset in range(0, len(parts), 2):
        rows.append((parts[offset].decode(), parts[offset + 1].decode()))
    return rows


def commit_thought(vault: Path, when: str, body: str) -> tuple[str, str]:
    instant = at(when)
    thought_id = thought_lib.thought_id_for(instant)
    path = thought_lib.thought_path(vault, thought_lib.week_id(instant), thought_id)
    write_text(path, thought_lib.render_thought(thought_id, instant, body))
    relative = path.relative_to(vault).as_posix()
    subprocess.check_call(["git", "add", "--", relative], cwd=vault)
    subprocess.check_call(["git", "commit", "-q", "-m", thought_id], cwd=vault)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
    return relative, sha


def clone_other(root: Path, remote: Path) -> Path:
    other = root / "other"
    subprocess.check_call(["git", "clone", "-q", str(remote), str(other)])
    for args in (
        ["config", "user.email", "other@example.com"],
        ["config", "user.name", "Other"],
        ["config", "commit.gpgsign", "false"],
    ):
        subprocess.check_call(["git", *args], cwd=other)
    return other


def remote_paths(remote: Path) -> str:
    return subprocess.check_output(
        ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"],
        text=True,
    )


def remote_head_count(remote: Path) -> int:
    proc = subprocess.run(
        ["git", "--git-dir", str(remote), "rev-list", "--count", "main"],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(proc.stdout.strip())


class VerbatimAndIdentityTests(unittest.TestCase):
    def test_verbatim_is_byte_exact_including_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            result = capture(vault, VERBATIM, "2026-10-08T17:48:00+08:00")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["id"], "thought-20261008-1748")
            self.assertEqual(result["week"], "2026-W41")
            with Path(result["path"]).open("r", encoding="utf-8", newline="") as handle:
                text = handle.read()
            self.assertEqual(thought_lib.verbatim_of(text), VERBATIM)
            self.assertFalse(VERBATIM.endswith("\n"))
            self.assertIn("原话:\n第二行", VERBATIM)
            self.assertEqual(journal_lib.cognition_file_count(vault), 0)
            self.assertFalse((vault / "📖 Cognition").exists())

    def test_crlf_and_cli_round_trip(self) -> None:
        verbatim = "合成第一行\r\n合成第二行  "
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            source = Path(raw) / "words.txt"
            write_text(source, verbatim)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(source),
                    "--at",
                    "2026-10-08T09:01:00+08:00",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["reason"], "not pushed")
            self.assertEqual(data["verbatim"], verbatim)
            with Path(data["path"]).open("r", encoding="utf-8", newline="") as handle:
                stored = handle.read()
            self.assertEqual(thought_lib.verbatim_of(stored), verbatim)

    def test_same_explicit_id_is_not_written_twice(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            when = "2026-10-08T17:48:00+08:00"
            thought_id = "thought-20261008-1748"
            first = capture(vault, VERBATIM, when, thought_id)
            self.assertEqual(first["files_written"], 1)
            before = Path(first["path"]).read_bytes()
            second = capture(vault, VERBATIM, when, thought_id)
            self.assertEqual(second["status"], "already_persisted")
            self.assertEqual(second["files_written"], 0)
            self.assertEqual(Path(first["path"]).read_bytes(), before)
            self.assertEqual(len(list((vault / "📝 Journal" / "想法").rglob("*.md"))), 1)

    def test_existing_path_with_different_bytes_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            when = "2026-10-08T17:48:00+08:00"
            thought_id = "thought-20261008-1748"
            path = vault / "📝 Journal" / "想法" / "2026-W41" / f"{thought_id}.md"
            write_text(path, "已有合成文件，不能改\n")
            before = path.read_bytes()
            result = capture(vault, VERBATIM, when, thought_id)
            self.assertEqual(result["status"], "refused")
            self.assertEqual(result["files_written"], 0)
            self.assertEqual(path.read_bytes(), before)
            changed = capture(vault, "另一句合成原话", when, thought_id)
            self.assertEqual(changed["status"], "refused")
            self.assertEqual(path.read_bytes(), before)

    def test_suffix_when_the_same_minute_is_taken(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            when = "2026-10-08T17:48:00+08:00"
            ids = []
            for index in range(3):
                result = capture(vault, f"合成第{index}条", when)
                self.assertEqual(result["status"], "success", result)
                ids.append(result["id"])
            self.assertEqual(
                ids,
                [
                    "thought-20261008-1748",
                    "thought-20261008-1748-2",
                    "thought-20261008-1748-3",
                ],
            )
            occupied = vault / "📝 Journal" / "想法" / "2026-W41"
            write_text(occupied / "thought-20261008-1800.md", "占位\n")
            write_text(occupied / "thought-20261008-1800-2.md", "占位\n")
            nxt = capture(vault, "合成跳过已占用的后缀", "2026-10-08T18:00:00+08:00")
            self.assertEqual(nxt["id"], "thought-20261008-1800-3")

    def test_naive_timestamp_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            result, ok = thought_lib.add_thought(
                vault,
                "合成",
                datetime(2026, 10, 8, 17, 48),
            )
            self.assertFalse(ok)
            self.assertEqual(result["files_written"], 0)
            self.assertFalse((vault / "📝 Journal").exists())


class ShanghaiWeekTests(unittest.TestCase):
    def test_iso_week_boundaries(self) -> None:
        cases = (
            ("2026-10-04T15:59:00+00:00", "2026-W40", "thought-20261004-2359"),
            ("2026-10-04T16:00:00+00:00", "2026-W41", "thought-20261005-0000"),
            ("2026-10-11T15:59:00+00:00", "2026-W41", "thought-20261011-2359"),
            ("2026-10-11T16:00:00+00:00", "2026-W42", "thought-20261012-0000"),
            ("2025-12-28T15:59:00+00:00", "2025-W52", "thought-20251228-2359"),
            ("2025-12-28T16:00:00+00:00", "2026-W01", "thought-20251229-0000"),
        )
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            for raw_at, week, thought_id in cases:
                result = capture(vault, f"合成 {thought_id}", raw_at)
                self.assertEqual(result["week"], week, raw_at)
                self.assertEqual(result["id"], thought_id, raw_at)
                relative = Path(result["relative"])
                self.assertEqual(relative.parts[0], "📝 Journal")
                self.assertEqual(relative.parts[1], "想法")
                self.assertEqual(relative.parts[2], week)
                self.assertEqual(relative.name, f"{thought_id}.md")


class DigestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = tempfile.TemporaryDirectory()
        self.vault = Path(self.raw.name)
        self.older = capture(self.vault, "合成上周那句", "2026-10-04T15:59:00+00:00")
        self.newer = capture(self.vault, "合成这周要展开的一句", "2026-10-08T17:48:00+08:00")
        self.third = capture(self.vault, "合成只看过的一句", "2026-10-08T17:49:00+08:00")

    def tearDown(self) -> None:
        self.raw.cleanup()

    def dispositions(self, mapping: dict[str, str]) -> list[dict[str, str]]:
        return [{"id": key, "disposition": value} for key, value in mapping.items()]

    def test_undigested_is_files_minus_digest_ids_across_weeks(self) -> None:
        opened, ok = thought_lib.list_open(self.vault)
        self.assertTrue(ok)
        self.assertEqual(
            [item["id"] for item in opened["thoughts"]],
            [self.older["id"], self.newer["id"], self.third["id"]],
        )
        rc, journal = save_journal(self.vault, journal_approval())
        self.assertEqual(rc, 0, journal)
        partial, ok = thought_lib.record_digest(
            self.vault,
            journal,
            self.dispositions({self.newer["id"]: "展开"}),
        )
        self.assertFalse(ok)
        self.assertEqual(partial["files_written"], 0)
        self.assertFalse((self.vault / "📝 Journal" / "想法" / "digests").exists())
        self.assertEqual(thought_lib.list_open(self.vault)[0]["count"], 3)

        recorded, ok = thought_lib.record_digest(
            self.vault,
            journal,
            self.dispositions(
                {
                    self.newer["id"]: "展开",
                    self.third["id"]: "看过未展开",
                    self.older["id"]: "看过未展开",
                }
            ),
        )
        self.assertTrue(ok, recorded)
        self.assertEqual(recorded["files_written"], 1)
        digest = Path(recorded["path"]).read_text(encoding="utf-8")
        self.assertIn("disposition: 展开", digest)
        self.assertIn("disposition: 看过未展开", digest)
        self.assertIn("[[2026-10-05 合成周记一]]", digest)
        self.assertEqual(thought_lib.list_open(self.vault)[0]["count"], 0)
        again, ok = thought_lib.record_digest(
            self.vault,
            journal,
            self.dispositions({}),
        )
        self.assertTrue(ok, again)
        self.assertEqual(again["files_written"], 0)
        self.assertEqual(len(list((self.vault / "📝 Journal" / "想法" / "digests").glob("*.md"))), 1)

    def test_seen_not_expanded_never_returns(self) -> None:
        rc, journal = save_journal(self.vault, journal_approval())
        self.assertEqual(rc, 0, journal)
        thought_lib.record_digest(
            self.vault,
            journal,
            self.dispositions(
                {
                    self.older["id"]: "看过未展开",
                    self.newer["id"]: "展开",
                    self.third["id"]: "看过未展开",
                }
            ),
        )
        fresh = capture(self.vault, "合成清单之后的新一句", "2026-10-09T08:00:00+08:00")
        opened, ok = thought_lib.list_open(self.vault)
        self.assertTrue(ok)
        self.assertEqual([item["id"] for item in opened["thoughts"]], [fresh["id"]])
        self.assertNotIn(self.third["id"], [item["id"] for item in opened["thoughts"]])
        self.assertNotIn(self.older["id"], [item["id"] for item in opened["thoughts"]])

    def test_digest_is_not_written_unless_journal_save_succeeded(self) -> None:
        refused_approval = journal_approval(confirmed=True, phrase="写周记")
        rc, refused = save_journal(self.vault, refused_approval)
        self.assertEqual(rc, 2, refused)
        result, ok = thought_lib.record_digest(
            self.vault,
            refused,
            self.dispositions({self.older["id"]: "展开", self.newer["id"]: "展开", self.third["id"]: "展开"}),
        )
        self.assertFalse(ok)
        self.assertEqual(result["files_written"], 0)
        self.assertFalse((self.vault / "📝 Journal" / "想法" / "digests").exists())
        self.assertEqual(thought_lib.list_open(self.vault)[0]["count"], 3)

        rc, journal = save_journal(self.vault, journal_approval())
        self.assertEqual(rc, 0, journal)
        missing = dict(journal)
        Path(missing["path"]).unlink()
        result, ok = thought_lib.record_digest(self.vault, missing, [])
        self.assertFalse(ok)
        self.assertEqual(result["files_written"], 0)
        self.assertFalse((self.vault / "📝 Journal" / "想法" / "digests").exists())

    def test_journal_listing_ignores_thoughts_and_digests(self) -> None:
        rc, journal = save_journal(self.vault, journal_approval())
        self.assertEqual(rc, 0, journal)
        thought_lib.record_digest(
            self.vault,
            journal,
            self.dispositions(
                {
                    self.older["id"]: "展开",
                    self.newer["id"]: "看过未展开",
                    self.third["id"]: "看过未展开",
                }
            ),
        )
        stray = self.vault / "📝 Journal" / "stray-thought.md"
        write_text(stray, "---\ntype: thought\nid: thought-20261008-1748\n---\n原话:\n合成\n")
        listed = journal_lib.list_journal_files(self.vault)
        self.assertEqual([path.name for path in listed], ["2026-10-05 合成周记一.md"])
        self.assertTrue((self.vault / "📝 Journal" / "想法").is_dir())
        self.assertGreater(len(list((self.vault / "📝 Journal" / "想法").rglob("*.md"))), 0)


class PublishTests(unittest.TestCase):
    def test_push_contains_only_the_new_thought(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault, remote = init_repo(Path(raw))
            result = capture(vault, VERBATIM, "2026-10-08T17:48:00+08:00")
            published, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertTrue(ok, published)
            self.assertTrue(published["pushed"])
            self.assertEqual(remote_head_count(remote), 2)
            self.assertEqual(remote_names(remote, "main"), [("A", result["relative"])])
            again, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok, again)
            self.assertEqual(again["status"], "refused")
            self.assertIn("already exists on main", again["message"])
            self.assertFalse(again["pushed"])
            self.assertEqual(remote_head_count(remote), 2)
            before = Path(result["path"]).read_bytes()
            Path(result["path"]).write_bytes(b"changed synthetic bytes\n")
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok)
            self.assertEqual(refused["status"], "refused")
            self.assertEqual(remote_head_count(remote), 2)
            Path(result["path"]).write_bytes(before)

    def test_other_worktree_changes_refuse_and_leave_the_remote(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault, remote = init_repo(Path(raw))
            result = capture(vault, "合成推送前的一句", "2026-10-08T17:48:00+08:00")
            extra = vault / "extra.txt"
            write_text(extra, "other synthetic change\n")
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok, refused)
            self.assertEqual(refused["status"], "refused")
            self.assertEqual(remote_head_count(remote), 1)
            self.assertTrue(Path(result["path"]).is_file())
            self.assertEqual(extra.read_text(encoding="utf-8"), "other synthetic change\n")
            head = git(vault, "rev-parse", "HEAD").stdout.strip()
            origin = git(vault, "rev-parse", "origin/main").stdout.strip()
            self.assertEqual(head, origin)

            extra.unlink()
            readme = vault / "README.md"
            readme.write_text("modified synthetic\n", encoding="utf-8")
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok)
            self.assertEqual(remote_head_count(remote), 1)
            readme.write_text("synthetic\n", encoding="utf-8")
            tracked = vault / "gone.md"
            write_text(tracked, "tracked\n")
            subprocess.check_call(["git", "add", "gone.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "add gone"], cwd=vault)
            subprocess.check_call(["git", "push", "origin", "HEAD:main"], cwd=vault)
            tracked.unlink()
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok)
            self.assertEqual(remote_names(remote, "main")[-1][0], "A")
            self.assertNotIn(result["relative"], [path for _, path in remote_names(remote, "main")])

    def test_digest_publish_waits_until_it_is_the_only_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault, remote = init_repo(Path(raw))
            thought = capture(vault, "合成消化用的一句", "2026-10-08T17:48:00+08:00")
            published, ok = thought_lib.publish_exact(vault, thought["relative"])
            self.assertTrue(ok, published)
            rc, journal = save_journal(vault, journal_approval())
            self.assertEqual(rc, 0, journal)
            recorded, ok = thought_lib.record_digest(
                vault,
                journal,
                [{"id": thought["id"], "disposition": "看过未展开"}],
            )
            self.assertTrue(ok, recorded)
            self.assertEqual(recorded["files_written"], 1)
            refused, ok = thought_lib.publish_exact(vault, recorded["relative"])
            self.assertFalse(ok, refused)
            self.assertIn("another change", refused["message"])
            self.assertTrue(Path(journal["path"]).is_file())
            digest_bytes = Path(recorded["path"]).read_bytes()
            self.assertNotIn(
                recorded["relative"],
                [path for _, path in remote_names(remote, "main")],
            )
            subprocess.check_call(["git", "add", "--", str(Path(journal["path"]).relative_to(vault))], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "journal stays a separate commit"], cwd=vault)
            subprocess.check_call(["git", "push", "origin", "HEAD:main"], cwd=vault)
            published, ok = thought_lib.publish_exact(vault, recorded["relative"])
            self.assertTrue(ok, published)
            self.assertTrue(published["pushed"])
            self.assertEqual(remote_names(remote, "main"), [("A", recorded["relative"])])
            self.assertEqual(Path(recorded["path"]).read_bytes(), digest_bytes)
            opened, _ = thought_lib.list_open(vault)
            self.assertEqual(opened["count"], 0)

    def test_publish_refuses_staged_modify_or_delete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault, remote = init_repo(Path(raw))
            result = capture(vault, "合成暂存区里不能带修改", "2026-10-08T17:48:00+08:00")
            readme = vault / "README.md"
            readme.write_text("modified synthetic\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "--", "README.md"], cwd=vault)
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok, refused)
            self.assertEqual(refused["status"], "refused")
            self.assertIn("modifies or deletes", refused["message"])
            self.assertEqual(remote_head_count(remote), 1)
            cached = git(vault, "diff", "--cached", "--name-status").stdout
            self.assertIn("M\tREADME.md", cached)
            self.assertNotIn(result["relative"], cached)
            self.assertTrue(Path(result["path"]).is_file())

            subprocess.check_call(["git", "restore", "--staged", "--", "README.md"], cwd=vault)
            subprocess.check_call(["git", "checkout", "--", "README.md"], cwd=vault)
            tracked = vault / "gone.md"
            write_text(tracked, "tracked\n")
            subprocess.check_call(["git", "add", "--", "gone.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "add gone"], cwd=vault)
            subprocess.check_call(["git", "push", "origin", "HEAD:main"], cwd=vault)
            subprocess.check_call(["git", "rm", "--", "gone.md"], cwd=vault)
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok, refused)
            self.assertIn("modifies or deletes", refused["message"])
            cached = git(vault, "diff", "--cached", "--name-status").stdout
            self.assertIn("D\tgone.md", cached)
            self.assertNotIn(result["relative"], [path for _, path in remote_names(remote, "main")])
            shown = subprocess.run(
                ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("gone.md", shown.stdout.splitlines())

    def test_cli_reports_not_saved_until_push_succeeds(self) -> None:
        source = (JOURNAL_TOOLS / "thought_lib.py").read_text(encoding="utf-8")
        self.assertIn('["push", "origin", "HEAD:main"]', source)
        self.assertIn('"--no-overwrite-ignore"', source)
        self.assertNotIn("--force", source)
        self.assertNotIn("push --force", source)
        self.assertNotIn("push -f", source)
        self.assertNotIn("--force-with-lease", source)
        self.assertNotIn("+HEAD", source)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            words = root / "words.txt"
            verbatim = "合成要推上去的一句"
            write_text(words, verbatim)
            tool = str(JOURNAL_TOOLS / "capture_thought.py")

            dirty = vault / "extra.txt"
            write_text(dirty, "other synthetic change\n")
            rc, data = run_json(
                [
                    sys.executable,
                    tool,
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(words),
                    "--at",
                    "2026-10-08T17:48:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["verbatim"], verbatim)
            self.assertTrue(data["reason"])
            self.assertNotEqual(data["status"], "success")
            self.assertEqual(remote_head_count(remote), 1)
            dirty.unlink()

            rc, data = run_json(
                [
                    sys.executable,
                    tool,
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    "📝 Journal/想法/2026-W41/thought-20261008-1748.md",
                ]
            )
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["status"], "success")
            self.assertTrue(data["pushed"])
            self.assertEqual(data["verbatim"], verbatim)
            self.assertEqual(remote_names(remote, "main"), [("A", data["relative"])])

            rc, again = run_json(
                [
                    sys.executable,
                    tool,
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    data["relative"],
                ]
            )
            self.assertEqual(rc, 2, again)
            self.assertEqual(again["status"], "not_saved")
            self.assertEqual(again["verbatim"], verbatim)
            self.assertIn("already exists on main", again["reason"])
            self.assertEqual(remote_head_count(remote), 2)
            before = Path(data["path"]).read_bytes()

            other_words = root / "other-words.txt"
            other_verbatim = "合成另一句还没推"
            write_text(other_words, other_verbatim)
            rc, pending = run_json(
                [
                    sys.executable,
                    tool,
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(other_words),
                    "--at",
                    "2026-10-08T18:10:00+08:00",
                ]
            )
            self.assertEqual(rc, 2, pending)
            self.assertEqual(pending["status"], "not_saved")
            self.assertEqual(pending["reason"], "not pushed")
            self.assertEqual(pending["verbatim"], other_verbatim)
            pending_rel = Path(pending["path"]).relative_to(vault).as_posix()

            readme = vault / "README.md"
            readme.write_text("modified synthetic\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "--", "README.md"], cwd=vault)
            rc, staged = run_json(
                [sys.executable, tool, "publish", "--vault", str(vault), "--path", pending_rel]
            )
            self.assertEqual(rc, 2, staged)
            self.assertEqual(staged["status"], "not_saved")
            self.assertEqual(staged["verbatim"], other_verbatim)
            self.assertIn("modifies or deletes", staged["reason"])
            self.assertEqual(remote_head_count(remote), 2)
            subprocess.check_call(["git", "restore", "--staged", "--worktree", "--", "README.md"], cwd=vault)
            self.assertEqual(Path(data["path"]).read_bytes(), before)

    def test_remote_reject_is_not_saved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\necho synthetic reject >&2\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            verbatim = "合成被远端拒绝的一句"
            words = root / "words.txt"
            write_text(words, verbatim)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(words),
                    "--at",
                    "2026-10-08T18:05:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 3, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["verbatim"], verbatim)
            self.assertTrue(data["reason"])
            self.assertNotIn("success", data["status"])
            self.assertEqual(remote_head_count(remote), 1)
            self.assertTrue(Path(data["path"]).is_file())

    def test_missing_git_exits_4_with_not_saved_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            verbatim = "PATH 里没有 git"
            words = root / "words.txt"
            write_text(words, verbatim)
            empty = root / "no-git"
            empty.mkdir()
            env = os.environ.copy()
            env["PATH"] = str(empty)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(words),
                    "--at",
                    "2026-10-08T11:06:00+08:00",
                    "--publish",
                ],
                capture_output=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 4, proc.stderr.decode())
            self.assertEqual(proc.stderr, b"")
            data = json.loads(proc.stdout.decode())
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["verbatim"], verbatim)
            self.assertIn("git is not available", data["reason"])
            self.assertEqual(remote_head_count(remote), 1)

    def test_staged_rename_is_refused(self) -> None:
        parsed = thought_lib._parse_name_status_z(b"R100\0a.md\0b.md\0")
        self.assertEqual(parsed, [("R", "b.md")])
        with tempfile.TemporaryDirectory() as raw:
            vault, remote = init_repo(Path(raw))
            write_text(vault / "a.md", "tracked a\n")
            subprocess.check_call(["git", "add", "a.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "add a"], cwd=vault)
            subprocess.check_call(["git", "push", "origin", "HEAD:main"], cwd=vault)
            subprocess.check_call(["git", "mv", "a.md", "b.md"], cwd=vault)
            result = capture(vault, "暂存了重命名", "2026-10-08T10:04:00+08:00")
            refused, ok = thought_lib.publish_exact(vault, result["relative"])
            self.assertFalse(ok, refused)
            self.assertEqual(refused["status"], "refused")
            self.assertIn("modifies or deletes", refused["message"])
            self.assertEqual(remote_head_count(remote), 2)
            names = [path for _, path in remote_names(remote, "main")]
            self.assertIn("a.md", names)
            self.assertNotIn("b.md", names)
            self.assertNotIn(result["relative"], names)

    def test_remote_only_same_name_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = root / "other"
            subprocess.check_call(["git", "clone", "-q", str(remote), str(other)])
            for args in (
                ["config", "user.email", "other@example.com"],
                ["config", "user.name", "Other"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", *args], cwd=other)
            rel = "📝 Journal/想法/2026-W41/thought-20261008-1008.md"
            write_text(
                other / rel,
                "---\nid: thought-20261008-1008\ntype: thought\n---\n原话:\n别的设备\n",
            )
            subprocess.check_call(["git", "add", "--", rel], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "other"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "HEAD:main"], cwd=other)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "本地不知道远端已有同名")),
                    "--at",
                    "2026-10-08T10:08:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertIn("already exists on main", data["reason"])
            shown = subprocess.check_output(["git", "--git-dir", str(remote), "show", f"main:{rel}"])
            self.assertIn("别的设备".encode(), shown)
            self.assertNotIn("本地不知道".encode(), shown)

    def test_path_traversal_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            fake = vault / "notes" / "2026-W41" / "thought-20261008-1014.md"
            write_text(
                fake,
                "---\nid: thought-20261008-1014\ntype: thought\nweek: 2026-W41\n---\n原话:\nx\n",
            )
            (vault / "📝 Journal" / "想法" / "2026-W41").mkdir(parents=True)
            link = vault / "📝 Journal" / "想法" / "2026-W41" / "thought-20261008-1015.md"
            os.symlink(fake, link)
            probes = [
                "📝 Journal/想法/../../README.md",
                "📝 Journal/想法/2026-W41/../../../notes/2026-W41/thought-20261008-1014.md",
                "notes/2026-W41/thought-20261008-1014.md",
                str(fake),
                "README.md",
                "../outside.md",
                "📝 Journal/想法\\..\\..\\README.md",
                "📝 Journal/想法/2026-W41/thought-20261008-1015.md",
            ]
            for probe in probes:
                refused, ok = thought_lib.publish_exact(vault, probe)
                self.assertFalse(ok, probe)
                self.assertEqual(refused["status"], "refused", probe)
            self.assertEqual(remote_head_count(remote), 1)

    def test_stuck_after_fetch_failure_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            tool = str(JOURNAL_TOOLS / "capture_thought.py")
            subprocess.check_call(["git", "remote", "set-url", "origin", str(root / "nope.git")], cwd=vault)
            first = root / "first.txt"
            write_text(first, "第一条")
            rc1, data1 = run_json(
                [sys.executable, tool, "add", "--vault", str(vault), "--text-file", str(first), "--at", "2026-10-08T11:10:00+08:00", "--publish"]
            )
            self.assertEqual(rc1, 4, data1)
            self.assertEqual(data1["status"], "not_saved")
            self.assertEqual(data1["verbatim"], "第一条")
            subprocess.check_call(["git", "remote", "set-url", "origin", str(remote)], cwd=vault)
            second = root / "second.txt"
            write_text(second, "第二条")
            rc2, data2 = run_json(
                [sys.executable, tool, "add", "--vault", str(vault), "--text-file", str(second), "--at", "2026-10-08T11:11:00+08:00", "--publish"]
            )
            self.assertEqual(rc2, 0, data2)
            self.assertTrue(data2["pushed"])
            rc3, data3 = run_json(
                [sys.executable, tool, "publish", "--vault", str(vault), "--path", data1["relative"]]
            )
            self.assertEqual(rc3, 0, data3)
            self.assertTrue(data3["pushed"])
            files = subprocess.check_output(
                ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"],
                text=True,
            )
            self.assertIn("thought-20261008-1110.md", files)
            self.assertIn("thought-20261008-1111.md", files)

    def test_behind_origin_fast_forwards_then_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = root / "other"
            subprocess.check_call(["git", "clone", "-q", str(remote), str(other)])
            for args in (
                ["config", "user.email", "other@example.com"],
                ["config", "user.name", "Other"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", *args], cwd=other)
            write_text(other / "other.md", "daily synthetic\n")
            subprocess.check_call(["git", "add", "other.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "HEAD:main"], cwd=other)
            other_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=other, text=True).strip()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "落后之后仍能记")),
                    "--at",
                    "2026-10-08T10:09:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 0, data)
            self.assertTrue(data["pushed"])
            remote_head = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            ancestor = subprocess.call(
                ["git", "--git-dir", str(remote), "merge-base", "--is-ancestor", other_head, remote_head]
            )
            self.assertEqual(ancestor, 0)
            self.assertEqual(remote_names(remote, "main"), [("A", data["relative"])])
            files = subprocess.check_output(
                ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"], text=True
            )
            self.assertIn("other.md", files)

    def test_diverged_main_is_not_force_pushed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            subprocess.check_call(["git", "commit", "-q", "--allow-empty", "-m", "local empty"], cwd=vault)
            other = root / "other"
            subprocess.check_call(["git", "clone", "-q", str(remote), str(other)])
            for args in (
                ["config", "user.email", "other@example.com"],
                ["config", "user.name", "Other"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", *args], cwd=other)
            write_text(other / "other.md", "remote side\n")
            subprocess.check_call(["git", "add", "other.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "remote side"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "HEAD:main"], cwd=other)
            before = remote_head_count(remote)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "分叉了不能推")),
                    "--at",
                    "2026-10-08T10:30:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertIn("fast-forward", data["reason"])
            self.assertIn("local commits not on origin/main:", data["reason"])
            self.assertIn("origin/main commits not local:", data["reason"])
            self.assertIn("manual recovery:", data["reason"])
            self.assertIn("task/thought-recovery", data["reason"])
            self.assertNotIn("push origin HEAD:main", data["reason"])
            self.assertNotIn("--force", data["reason"])
            self.assertFalse((vault / ".git" / "rebase-merge").exists())
            self.assertEqual(remote_head_count(remote), before)
            files = subprocess.check_output(
                ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"], text=True
            )
            self.assertNotIn("thought-20261008-1030.md", files)

    def test_rejected_push_then_new_thought_pushes_both(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            hook = remote / "hooks" / "pre-receive"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            tool = str(JOURNAL_TOOLS / "capture_thought.py")
            first = root / "first.txt"
            write_text(first, "被拒的一条")
            rc1, data1 = run_json(
                [sys.executable, tool, "add", "--vault", str(vault), "--text-file", str(first), "--at", "2026-10-08T11:12:00+08:00", "--publish"]
            )
            self.assertEqual(rc1, 3, data1)
            hook.unlink()
            second = root / "second.txt"
            write_text(second, "远端恢复后的新一条")
            rc2, data2 = run_json(
                [sys.executable, tool, "add", "--vault", str(vault), "--text-file", str(second), "--at", "2026-10-08T11:13:00+08:00", "--publish"]
            )
            self.assertEqual(rc2, 0, data2)
            self.assertEqual(remote_head_count(remote), 3)
            files = subprocess.check_output(
                ["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"], text=True
            )
            self.assertIn("thought-20261008-1112.md", files)
            self.assertIn("thought-20261008-1113.md", files)

    def test_push_network_loss_is_exit_4(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            real_git = shutil.which("git")
            self.assertTrue(real_git)
            shim = root / "shim"
            shim.mkdir()
            (shim / "git").write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"push\" ]; then\n"
                "  echo \"fatal: unable to access 'http://127.0.0.1:9/x.git/': Failed to connect to 127.0.0.1 port 9: Could not connect to server\" >&2\n"
                "  exit 1\n"
                "fi\n"
                f"exec {real_git} \"$@\"\n",
                encoding="utf-8",
            )
            (shim / "git").chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
            verbatim = "推的时候断网"
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, verbatim)),
                    "--at",
                    "2026-10-08T11:20:00+08:00",
                    "--publish",
                ],
                env=env,
            )
            self.assertEqual(rc, 4, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["verbatim"], verbatim)
            self.assertEqual(remote_head_count(remote), 1)

    def test_digest_publish_failure_has_empty_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault, _remote = init_repo(Path(raw))
            thought = capture(vault, "合成消化用的一句", "2026-10-08T17:48:00+08:00")
            published, ok = thought_lib.publish_exact(vault, thought["relative"])
            self.assertTrue(ok, published)
            rc, journal = save_journal(vault, journal_approval())
            self.assertEqual(rc, 0, journal)
            recorded, ok = thought_lib.record_digest(
                vault,
                journal,
                [{"id": thought["id"], "disposition": "看过未展开"}],
            )
            self.assertTrue(ok, recorded)
            digest_text = Path(recorded["path"]).read_text(encoding="utf-8")
            self.assertNotEqual(digest_text, "")
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    recorded["relative"],
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["verbatim"], "")

    def test_contents_create_body_has_no_sha(self) -> None:
        body = thought_lib.github_contents_create_body(
            "📝 Journal/想法/2026-W41/thought-20261008-1748.md",
            "合成原话".encode("utf-8"),
            "thought: thought-20261008-1748",
        )
        self.assertEqual(set(body), {"message", "content", "branch"})
        self.assertNotIn("sha", body)
        with self.assertRaises(ValueError):
            thought_lib.github_contents_create_body(
                "README.md",
                b"synthetic\n",
                "thought: nope",
            )

    def test_later_modify_or_delete_in_the_unpushed_range_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            before = remote_head_count(remote)
            relative, _first = commit_thought(vault, "2026-10-08T12:01:00+08:00", "先新增")
            write_text(vault / relative, "改掉了\n")
            subprocess.check_call(["git", "commit", "-q", "-am", "modify"], cwd=vault)
            modified = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "新的一条")),
                    "--at",
                    "2026-10-08T12:02:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn(modified[:12], data["reason"])
            self.assertIn("M ", data["reason"])
            self.assertEqual(remote_head_count(remote), before)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            before = remote_head_count(remote)
            relative, _first = commit_thought(vault, "2026-10-08T12:03:00+08:00", "会被删")
            subprocess.check_call(["git", "rm", "-q", "--", relative], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "delete"], cwd=vault)
            deleted = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "新的一条")),
                    "--at",
                    "2026-10-08T12:04:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn(deleted[:12], data["reason"])
            self.assertEqual(remote_head_count(remote), before)

    def test_merge_commit_in_the_unpushed_range_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            before = remote_head_count(remote)
            subprocess.check_call(["git", "checkout", "-q", "-b", "side"], cwd=vault)
            commit_thought(vault, "2026-10-08T12:12:00+08:00", "旁边")
            subprocess.check_call(["git", "checkout", "-q", "main"], cwd=vault)
            commit_thought(vault, "2026-10-08T12:13:00+08:00", "主干")
            subprocess.check_call(["git", "merge", "-q", "--no-ff", "-m", "merge side", "side"], cwd=vault)
            merge = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "merge 之后")),
                    "--at",
                    "2026-10-08T12:14:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn(merge[:12], data["reason"])
            self.assertIn("merge", data["reason"])
            self.assertEqual(remote_head_count(remote), before)

    def test_fast_forward_does_not_overwrite_an_ignored_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            write_text(vault / ".gitignore", "private.md\n")
            subprocess.check_call(["git", "add", ".gitignore"], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "ignore"], cwd=vault)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=vault)
            other = clone_other(root, remote)
            local_note = "Jake 本地被忽略的私人笔记\n"
            write_text(vault / "private.md", local_note)
            write_text(other / "private.md", "远端提交的同名文件\n")
            subprocess.check_call(["git", "add", "-f", "private.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "track private"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "落后加被忽略的本地文件")),
                    "--at",
                    "2026-10-08T12:17:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn("private.md", data["reason"])
            self.assertEqual((vault / "private.md").read_text(encoding="utf-8"), local_note)
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            self.assertNotIn("thought-20261008-1217.md", remote_paths(remote))

    def test_race_then_retry_replays_the_add_only_commit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            real_git = shutil.which("git")
            self.assertTrue(real_git)
            shim = root / "shim"
            shim.mkdir()
            flag = root / "flag"
            (shim / "git").write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "push" ] && [ ! -e "{flag}" ]; then\n'
                f'  touch "{flag}"\n'
                f'  ( cd "{other}" && echo r >> race.md && {real_git} add race.md && {real_git} commit -q -m race && {real_git} push -q origin main ) >/dev/null 2>&1\n'
                f'  exec {real_git} "$@"\n'
                "fi\n"
                f'exec {real_git} "$@"\n',
                encoding="utf-8",
            )
            (shim / "git").chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
            tool = str(JOURNAL_TOOLS / "capture_thought.py")
            first = "竞态的一条"
            rc1, data1 = run_json(
                [
                    sys.executable,
                    tool,
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, first)),
                    "--at",
                    "2026-10-08T12:24:00+08:00",
                    "--publish",
                ],
                env=env,
            )
            self.assertEqual(rc1, 3, data1)
            self.assertEqual(data1["verbatim"], first)
            self.assertIn("race.md", remote_paths(remote))
            self.assertNotIn("thought-20261008-1224.md", remote_paths(remote))
            rc2, data2 = run_json(
                [sys.executable, tool, "publish", "--vault", str(vault), "--path", data1["relative"]]
            )
            self.assertEqual(rc2, 0, data2)
            self.assertTrue(data2["pushed"])
            self.assertIn("race.md", remote_paths(remote))
            self.assertIn("thought-20261008-1224.md", remote_paths(remote))
            rc3, data3 = run_json(
                [
                    sys.executable,
                    tool,
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "再记一条")),
                    "--at",
                    "2026-10-08T12:25:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc3, 0, data3)
            files = remote_paths(remote)
            self.assertIn("thought-20261008-1225.md", files)
            self.assertIn("race.md", files)
            parents = subprocess.check_output(
                ["git", "--git-dir", str(remote), "log", "--format=%P", "main"],
                text=True,
            )
            self.assertTrue(all(len(line.split()) <= 1 for line in parents.splitlines()))

    def test_network_loss_then_remote_advance_replays(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            real_git = shutil.which("git")
            self.assertTrue(real_git)
            shim = root / "shim"
            shim.mkdir()
            flag = root / "flag"
            (shim / "git").write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "push" ] && [ ! -e "{flag}" ]; then\n'
                f'  touch "{flag}"\n'
                "  echo \"fatal: unable to access 'https://github.com/x/y.git/': Could not resolve host: github.com\" >&2\n"
                "  exit 128\n"
                "fi\n"
                f'exec {real_git} "$@"\n',
                encoding="utf-8",
            )
            (shim / "git").chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{shim}{os.pathsep}{env['PATH']}"
            verbatim = "push 时断网"
            rc1, data1 = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, verbatim)),
                    "--at",
                    "2026-10-08T12:26:00+08:00",
                    "--publish",
                ],
                env=env,
            )
            self.assertEqual(rc1, 4, data1)
            self.assertEqual(data1["status"], "not_saved")
            self.assertEqual(data1["verbatim"], verbatim)
            write_text(other / "daily-0800.md", "08:00 日摘要\n")
            subprocess.check_call(["git", "add", "daily-0800.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            rc2, data2 = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "网络恢复后第二天记的")),
                    "--at",
                    "2026-10-09T09:00:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc2, 0, data2)
            files = remote_paths(remote)
            self.assertIn("daily-0800.md", files)
            self.assertIn("thought-20261008-1226.md", files)
            self.assertIn("thought-20261009-0900.md", files)
            parents = subprocess.check_output(
                ["git", "--git-dir", str(remote), "log", "--format=%P", "main"],
                text=True,
            )
            self.assertTrue(all(len(line.split()) <= 1 for line in parents.splitlines()))

    def test_symlink_or_garbage_in_an_unpushed_commit_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            relative = "📝 Journal/想法/2026-W41/thought-20261008-1232.md"
            (vault / relative).parent.mkdir(parents=True)
            os.symlink("../../../README.md", vault / relative)
            subprocess.check_call(["git", "add", "--", relative], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "symlink thought"], cwd=vault)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "符号链接提交在前")),
                    "--at",
                    "2026-10-08T12:33:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn("symlink", data["reason"])
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            mode = subprocess.check_output(
                ["git", "--git-dir", str(remote), "ls-tree", "main", "--", relative],
                text=True,
            )
            self.assertNotIn("120000", mode)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            relative = "📝 Journal/想法/2026-W41/thought-20261008-1234.md"
            write_text(vault / relative, "placeholder")
            (vault / relative).write_bytes(b"\x00\x01 not a thought")
            subprocess.check_call(["git", "add", "--", relative], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "garbage"], cwd=vault)
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "垃圾内容提交在前")),
                    "--at",
                    "2026-10-08T12:35:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn("not a thought or digest", data["reason"])
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )

    def test_internal_error_reports_the_exception_and_keeps_verbatim(self) -> None:
        import io
        from contextlib import redirect_stdout

        def boom(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("synthetic internal bug")

        original = thought_lib.add_thought
        thought_lib.add_thought = boom
        try:
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                words = write_words(root, "原话还在")
                vault = root / "vault"
                vault.mkdir()
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = capture_thought.main(
                        [
                            "add",
                            "--vault",
                            str(vault),
                            "--text-file",
                            str(words),
                            "--at",
                            "2026-10-08T12:00:00+08:00",
                            "--publish",
                        ]
                    )
        finally:
            thought_lib.add_thought = original
        data = json.loads(buf.getvalue())
        self.assertEqual(code, 5, data)
        self.assertEqual(data["status"], "not_saved")
        self.assertIn("RuntimeError", data["reason"])
        self.assertIn("synthetic internal bug", data["reason"])
        self.assertNotIn("git is not available", data["reason"])
        self.assertEqual(data["verbatim"], "原话还在")

        def missing_git(*_args: object, **_kwargs: object) -> None:
            raise FileNotFoundError(2, "No such file or directory", "git")

        thought_lib.add_thought = missing_git
        try:
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                words = write_words(root, "git 丢了但原话在")
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = capture_thought.main(
                        [
                            "add",
                            "--vault",
                            str(root / "vault"),
                            "--text-file",
                            str(words),
                            "--publish",
                        ]
                    )
        finally:
            thought_lib.add_thought = original
        data = json.loads(buf.getvalue())
        self.assertEqual(code, 4, data)
        self.assertIn("FileNotFoundError", data["reason"])
        self.assertEqual(data["verbatim"], "git 丢了但原话在")

        def other(*_args: object, **_kwargs: object) -> None:
            raise OSError("disk full")

        thought_lib.add_thought = other
        try:
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                words = write_words(root, "磁盘满了")
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = capture_thought.main(
                        ["add", "--vault", str(root), "--text-file", str(words), "--publish"]
                    )
        finally:
            thought_lib.add_thought = original
        data = json.loads(buf.getvalue())
        self.assertEqual(code, 5, data)
        self.assertIn("OSError: disk full", data["reason"])
        self.assertEqual(data["verbatim"], "磁盘满了")

    def test_argument_error_prints_json(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(JOURNAL_TOOLS / "capture_thought.py"), "publish"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "not_saved")
        self.assertIn("vault", data["reason"])
        self.assertNotIn("usage:", proc.stderr.lower())

    def _publish_words(self, vault: Path, root: Path, text: str, when: str) -> tuple[int, dict]:
        return run_json(
            [
                sys.executable,
                str(JOURNAL_TOOLS / "capture_thought.py"),
                "add",
                "--vault",
                str(vault),
                "--text-file",
                str(write_words(root, text)),
                "--at",
                when,
                "--publish",
            ]
        )

    def test_recovery_command_does_not_push_modifications(self) -> None:
        park = "git branch task/thought-recovery HEAD && git reset --keep origin/main"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            write_text(vault / "README.md", "Jake 的修改\n")
            subprocess.check_call(["git", "commit", "-qam", "edit readme"], cwd=vault)
            write_text(other / "daily.md", "daily\n")
            subprocess.check_call(["git", "add", "daily.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            rc, data = self._publish_words(vault, root, "修改提交在前", "2026-10-08T13:30:00+08:00")
            self.assertEqual(rc, 2, data)
            self.assertNotIn("push origin HEAD:main", data["reason"])
            self.assertIn(park, data["reason"])
            self.assertIn("hand them to Jake", data["reason"])
            self.assertIn("re-run only git reset --keep origin/main", data["reason"])
            subprocess.check_call(park, cwd=vault, shell=True)
            remote_readme = subprocess.check_output(
                ["git", "--git-dir", str(remote), "show", "main:README.md"], text=True
            )
            self.assertEqual(remote_readme, "synthetic\n")
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            parked = subprocess.check_output(
                ["git", "show", "task/thought-recovery:README.md"], cwd=vault, text=True
            )
            self.assertEqual(parked, "Jake 的修改\n")
            self.assertTrue((vault / "📝 Journal" / "想法").exists())
            thought = next((vault / "📝 Journal" / "想法").rglob("thought-20261008-1330.md"))
            self.assertEqual(thought.read_text(encoding="utf-8").split("原话:\n", 1)[1], "修改提交在前")
            self.assertFalse((vault / ".git" / "rebase-merge").exists())

        cases = (
            ("delete", "2026-10-08T13:40:00+08:00"),
            ("rename", "2026-10-08T13:41:00+08:00"),
            ("merge", "2026-10-08T13:42:00+08:00"),
            ("exists", "2026-10-08T13:43:00+08:00"),
            ("bad-sha", "2026-10-08T13:44:00+08:00"),
        )
        for kind, when in cases:
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as raw:
                    root = Path(raw)
                    vault, remote = init_repo(root)
                    other = clone_other(root, remote)
                    if kind == "delete":
                        relative, _sha = commit_thought(vault, "2026-10-08T13:39:00+08:00", "会被删")
                        subprocess.check_call(["git", "rm", "-q", "--", relative], cwd=vault)
                        subprocess.check_call(["git", "commit", "-q", "-m", "delete"], cwd=vault)
                    elif kind == "rename":
                        subprocess.check_call(["git", "mv", "README.md", "README-renamed.md"], cwd=vault)
                        subprocess.check_call(["git", "commit", "-q", "-m", "rename"], cwd=vault)
                    elif kind == "merge":
                        subprocess.check_call(["git", "checkout", "-q", "-b", "side"], cwd=vault)
                        commit_thought(vault, "2026-10-08T13:20:00+08:00", "旁边")
                        subprocess.check_call(["git", "checkout", "-q", "main"], cwd=vault)
                        commit_thought(vault, "2026-10-08T13:21:00+08:00", "主干")
                        subprocess.check_call(
                            ["git", "merge", "-q", "--no-ff", "-m", "merge side", "side"], cwd=vault
                        )
                    elif kind == "exists":
                        relative, _sha = commit_thought(vault, "2026-10-08T13:37:00+08:00", "本地版本")
                        (other / relative).parent.mkdir(parents=True, exist_ok=True)
                        write_text(other / relative, (vault / relative).read_text(encoding="utf-8").replace("本地版本", "远端版本"))
                        subprocess.check_call(["git", "add", "--", relative], cwd=other)
                        subprocess.check_call(["git", "commit", "-q", "-m", "same path"], cwd=other)
                        subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
                    else:
                        instant = at("2026-10-08T13:36:00+08:00")
                        thought_id = thought_lib.thought_id_for(instant)
                        text = thought_lib.render_thought(thought_id, instant, "原话").replace(
                            "原话:\n原话", "原话:\n改过的原话"
                        )
                        path = thought_lib.thought_path(vault, thought_lib.week_id(instant), thought_id)
                        write_text(path, text)
                        relative = path.relative_to(vault).as_posix()
                        subprocess.check_call(["git", "add", "--", relative], cwd=vault)
                        subprocess.check_call(["git", "commit", "-q", "-m", "bad sha"], cwd=vault)
                    if kind != "exists":
                        write_text(other / "daily.md", "daily\n")
                        subprocess.check_call(["git", "add", "daily.md"], cwd=other)
                        subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
                        subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
                    before = subprocess.check_output(
                        ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                    ).strip()
                    rc, data = self._publish_words(vault, root, "后面这条", when)
                    self.assertEqual(rc, 2, data)
                    self.assertNotIn("push origin HEAD:main", data["reason"])
                    self.assertIn("hand them to Jake", data["reason"])
                    self.assertEqual(
                        subprocess.check_output(
                            ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                        ).strip(),
                        before,
                    )
                    self.assertFalse((vault / ".git" / "rebase-merge").exists())
                    self.assertFalse((vault / ".git" / "rebase-apply").exists())

    def test_replay_git_failure_says_rerun_publish_and_aborts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            commit_thought(vault, "2026-10-08T13:01:00+08:00", "第一笔")
            kept = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
            subprocess.check_call(["git", "branch", "jake-backup", kept], cwd=vault)
            commit_thought(vault, "2026-10-08T13:02:00+08:00", "第二笔")
            write_text(other / "daily.md", "daily\n")
            subprocess.check_call(["git", "add", "daily.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            hook = vault / ".git" / "hooks" / "pre-rebase"
            hook.write_text("#!/bin/sh\necho no-rebase >&2\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            head_before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip()
            rc, data = self._publish_words(vault, root, "签名失败时", "2026-10-08T13:03:00+08:00")
            self.assertEqual(rc, 2, data)
            self.assertNotIn("push origin HEAD:main", data["reason"])
            self.assertNotIn("git rebase --onto", data["reason"])
            self.assertIn("fix the cause, then re-run publish", data["reason"])
            self.assertIn("git rebase --abort", data["reason"])
            self.assertEqual(
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=vault, text=True).strip(),
                head_before,
            )
            self.assertEqual(
                subprocess.check_output(["git", "branch", "--show-current"], cwd=vault, text=True).strip(),
                "main",
            )
            self.assertFalse((vault / ".git" / "rebase-merge").exists())
            self.assertFalse((vault / ".git" / "rebase-apply").exists())
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            self.assertEqual(
                subprocess.check_output(["git", "rev-parse", "jake-backup"], cwd=vault, text=True).strip(),
                kept,
            )
            write_text(vault / "README.md", "Jake 看到原因之后的修改\n")
            subprocess.check_call(["git", "add", "README.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "later edit"], cwd=vault)
            hook.unlink()
            again = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    data["relative"],
                ]
            )
            self.assertEqual(again[0], 2, again[1])
            self.assertNotIn("push origin HEAD:main", again[1]["reason"])
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "show", "main:README.md"], text=True
                ),
                "synthetic\n",
            )
            self.assertFalse((vault / ".git" / "rebase-merge").exists())

    def test_replay_failure_rerun_publish_after_the_cause_is_fixed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            commit_thought(vault, "2026-10-08T13:11:00+08:00", "修好后再推")
            write_text(other / "daily.md", "daily\n")
            subprocess.check_call(["git", "add", "daily.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            hook = vault / ".git" / "hooks" / "pre-rebase"
            hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            hook.chmod(0o755)
            rc, data = self._publish_words(vault, root, "原因排除后再 publish", "2026-10-08T13:12:00+08:00")
            self.assertEqual(rc, 2, data)
            self.assertIn("re-run publish", data["reason"])
            hook.unlink()
            again = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    data["relative"],
                ]
            )
            self.assertEqual(again[0], 0, again[1])
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "show", "main:README.md"], text=True
                ),
                "synthetic\n",
            )
            names = remote_paths(remote)
            self.assertIn("thought-20261008-1311.md", names)
            self.assertIn("thought-20261008-1312.md", names)

    def test_replay_keeps_caller_git_config_count(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            commit_thought(vault, "2026-10-08T13:21:00+08:00", "环境配置还在")
            subprocess.check_call(["git", "config", "rebase.autoStash", "true"], cwd=vault)
            write_text(other / "daily.md", "daily\n")
            subprocess.check_call(["git", "add", "daily.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            env = os.environ.copy()
            env["GIT_CONFIG_COUNT"] = "1"
            env["GIT_CONFIG_KEY_0"] = "user.email"
            env["GIT_CONFIG_VALUE_0"] = "env-jake@example.com"
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(write_words(root, "新的一条也用这个环境")),
                    "--at",
                    "2026-10-08T13:22:00+08:00",
                    "--publish",
                ],
                env=env,
            )
            self.assertEqual(rc, 0, data)
            log = subprocess.check_output(
                ["git", "--git-dir", str(remote), "log", "--format=%s|%ce", "main"],
                text=True,
            )
            replayed = [line for line in log.splitlines() if line.startswith("thought-20261008-1321|")]
            self.assertEqual(replayed, ["thought-20261008-1321|env-jake@example.com"])
            self.assertIn("thought-20261008-1321", log)

    def test_replay_does_not_move_other_branches(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            _relative, kept = commit_thought(vault, "2026-10-08T13:52:00+08:00", "留给分支")
            subprocess.check_call(["git", "branch", "jake-backup", kept], cwd=vault)
            subprocess.check_call(["git", "config", "rebase.updateRefs", "true"], cwd=vault)
            write_text(other / "daily.md", "daily\n")
            subprocess.check_call(["git", "add", "daily.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "daily"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            rc, data = self._publish_words(vault, root, "updateRefs", "2026-10-08T13:53:00+08:00")
            self.assertEqual(rc, 0, data)
            self.assertEqual(
                subprocess.check_output(["git", "rev-parse", "jake-backup"], cwd=vault, text=True).strip(),
                kept,
            )

    def test_replay_keeps_an_ignored_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            other = clone_other(root, remote)
            write_text(vault / ".gitignore", "private.md\n")
            subprocess.check_call(["git", "add", ".gitignore"], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "ignore"], cwd=vault)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=vault)
            subprocess.check_call(["git", "pull", "-q", "--ff-only"], cwd=other)
            commit_thought(vault, "2026-10-08T13:08:00+08:00", "本地想法")
            local_note = "Jake 私人笔记\n"
            write_text(vault / "private.md", local_note)
            write_text(other / "private.md", "远端同名\n")
            subprocess.check_call(["git", "add", "-f", "private.md"], cwd=other)
            subprocess.check_call(["git", "commit", "-q", "-m", "track private"], cwd=other)
            subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=other)
            before = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
            ).strip()
            rc, data = self._publish_words(vault, root, "重放路径加忽略文件", "2026-10-08T13:09:00+08:00")
            self.assertEqual(rc, 2, data)
            self.assertIn("private.md", data["reason"])
            self.assertNotIn("push origin HEAD:main", data["reason"])
            self.assertNotIn("git reset --keep", data["reason"])
            self.assertEqual((vault / "private.md").read_text(encoding="utf-8"), local_note)
            self.assertEqual(
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "main"], text=True
                ).strip(),
                before,
            )
            self.assertFalse((vault / ".git" / "rebase-merge").exists())

    def test_verbatim_sha256_is_checked_for_one_file_and_a_range(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            instant = at("2026-10-08T13:45:00+08:00")
            thought_id = thought_lib.thought_id_for(instant)
            body = "原话不该被改"
            text = thought_lib.render_thought(thought_id, instant, body).replace(
                "原话:\n" + body, "原话:\n改过"
            )
            path = thought_lib.thought_path(vault, thought_lib.week_id(instant), thought_id)
            write_text(path, text)
            relative = path.relative_to(vault).as_posix()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    relative,
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn("thought file verbatim does not match verbatim_sha256", data["reason"])
            self.assertNotIn(thought_id, remote_paths(remote))
            subprocess.check_call(["git", "add", "--", relative], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "bad sha"], cwd=vault)
            rc2, data2 = self._publish_words(vault, root, "后面这条", "2026-10-08T13:46:00+08:00")
            self.assertEqual(rc2, 2, data2)
            self.assertIn("thought file verbatim does not match verbatim_sha256", data2["reason"])
            self.assertNotIn("push origin HEAD:main", data2["reason"])
            self.assertEqual(remote_head_count(remote), 1)

    def test_missing_verbatim_sha256_says_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault, remote = init_repo(root)
            instant = at("2026-10-08T13:47:00+08:00")
            thought_id = thought_lib.thought_id_for(instant)
            body = "没有哈希字段"
            text = thought_lib.render_thought(thought_id, instant, body)
            text = "".join(
                line for line in text.splitlines(keepends=True) if not line.startswith("verbatim_sha256:")
            )
            path = thought_lib.thought_path(vault, thought_lib.week_id(instant), thought_id)
            write_text(path, text)
            relative = path.relative_to(vault).as_posix()
            rc, data = run_json(
                [
                    sys.executable,
                    str(JOURNAL_TOOLS / "capture_thought.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    relative,
                ]
            )
            self.assertEqual(rc, 2, data)
            self.assertIn("thought file verbatim_sha256 is missing", data["reason"])
            self.assertNotIn("does not match", data["reason"])
            self.assertNotIn("push origin HEAD:main", data["reason"])
            subprocess.check_call(["git", "add", "--", relative], cwd=vault)
            subprocess.check_call(["git", "commit", "-q", "-m", "missing sha"], cwd=vault)
            rc2, data2 = self._publish_words(vault, root, "后面这条", "2026-10-08T13:48:00+08:00")
            self.assertEqual(rc2, 2, data2)
            self.assertIn("thought file verbatim_sha256 is missing", data2["reason"])
            self.assertNotIn("does not match", data2["reason"])
            self.assertNotIn("push origin HEAD:main", data2["reason"])
            self.assertEqual(remote_head_count(remote), 1)

    def test_network_words_in_an_internal_error_are_exit_5(self) -> None:
        import io
        from contextlib import redirect_stdout

        def boom(*_args: object, **_kwargs: object) -> None:
            raise ValueError("bug while parsing text 'unable to access' in user note")

        original = thought_lib.add_thought
        thought_lib.add_thought = boom
        try:
            with tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                words = write_words(root, "原话还在")
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = capture_thought.main(
                        [
                            "add",
                            "--vault",
                            str(root / "vault"),
                            "--text-file",
                            str(words),
                            "--publish",
                        ]
                    )
        finally:
            thought_lib.add_thought = original
        data = json.loads(buf.getvalue())
        self.assertEqual(code, 5, data)
        self.assertIn("ValueError", data["reason"])
        self.assertEqual(data["verbatim"], "原话还在")


if __name__ == "__main__":
    unittest.main()
