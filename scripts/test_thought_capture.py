#!/usr/bin/env python3
"""Synthetic thought-capture checks. Temp vaults and a local bare remote only."""

from __future__ import annotations

import json
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

import journal_lib  # noqa: E402
import thought_lib  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
VERBATIM = "  合成原话：先放着，一字不改。\n原话:\n第二行"


def run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    body = proc.stdout.strip() or "{}"
    return proc.returncode, json.loads(body)


def at(raw: str) -> datetime:
    return thought_lib.parse_instant(raw)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


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
        self.assertNotIn("--force", source)
        self.assertNotIn("push --force", source)
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


if __name__ == "__main__":
    unittest.main()
