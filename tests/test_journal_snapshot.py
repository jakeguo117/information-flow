"""AC07 journal half: --digest-snapshot records the Thursday snapshot id."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "skills" / "journal" / "tools"
sys.path.insert(0, str(TOOLS))

import journal_lib  # noqa: E402

DIGEST_ID = "dg-cy-20261015"
CYCLE_ID = "cy-20261015"
SPEC_R1 = f"{DIGEST_ID}@r1"
SPEC_R2 = f"{DIGEST_ID}@r2"
IDS_R1 = ["in-snap-r1-aaa", "in-snap-r1-bbb"]
IDS_R2 = ["in-snap-r2-ccc"]
MARKER = "<!-- information-flow-weekly-digest generator=1 sha256=" + ("ab" * 32) + " -->"


def sha256_ids(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def snapshot_text(digest_id: str, revision: int, input_ids: list[str] | None, body: str) -> str:
    lines = [
        "---",
        'schema_version: "digest-0.2"',
        'type: "digest"',
        f"digest_id: {json.dumps(digest_id, ensure_ascii=False)}",
        f"cycle_id: {json.dumps(digest_id.removeprefix('dg-'), ensure_ascii=False)}",
        'coverage_start: "2026-10-09"',
        'cutoff_at: "2026-10-15T08:00:00+08:00"',
        f"snapshot_revision: {revision}",
    ]
    if input_ids is None:
        pass
    elif not input_ids:
        lines.append("input_ids: []")
    else:
        lines.append("input_ids:")
        lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in input_ids)
    lines.extend(
        [
            "source_weeks: {}",
            "counts: {}",
            "late_or_cross_week: []",
            'generated_at: "2026-10-15T12:00:00+08:00"',
            'generator: "digest-v2-test"',
            "---",
            "",
            "# 本周 digest",
            "",
            "## 本周 digest（2026-W42）",
            "",
            body,
            "",
        ]
    )
    return "\n".join(lines)


class JournalSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.vault = self.tmp / "vault"
        self.vault.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_snapshot(
        self,
        revision: int,
        input_ids: list[str] | None,
        *,
        digest_id: str = DIGEST_ID,
        body: str,
        directory: Path | None = None,
        marker: bool = False,
    ) -> Path:
        root = directory if directory is not None else self.vault / "📋 Digests" / "cycles" / CYCLE_ID
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"r{revision}.md"
        text = snapshot_text(digest_id, revision, input_ids, body)
        if marker:
            text = text.rstrip("\n") + "\n" + MARKER + "\n"
        path.write_text(text, encoding="utf-8")
        return path

    def approval(
        self,
        ids: list[str],
        *,
        revision: int = 1,
        digest_id: str = DIGEST_ID,
        event_id: str = "journal-snap-r1",
        title: str = "快照号",
        confirmed: bool = True,
        phrase: str = "可以写",
        payload: str | None = None,
    ) -> dict:
        data: dict = {
            "confirmed": confirmed,
            "phrase": phrase,
            "date": "2026-10-16",
            "journal_number": 7,
            "title": title,
            "event_id": event_id,
            "body": "合成正文。",
            "topics": [],
            "previous": "",
            "digest_id": digest_id,
            "snapshot_revision": revision,
            "input_ids_sha256": sha256_ids(ids),
        }
        if payload is None:
            data["payload_sha256"] = journal_lib.fingerprint(journal_lib.render_journal(data))
        else:
            data["payload_sha256"] = payload
        return data

    def invoke(self, approval: dict, *extra: str, action: str = "save") -> tuple[int, dict]:
        path = self.tmp / "approval.json"
        path.write_text(json.dumps(approval, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "write_journal.py"),
                action,
                "--vault",
                str(self.vault),
                "--approval",
                str(path),
                *extra,
            ],
            capture_output=True,
            text=True,
        )
        self.assertTrue(proc.stdout, proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def assert_no_journal(self) -> None:
        journal = self.vault / "📝 Journal"
        if not journal.exists():
            return
        files = [path for path in journal.rglob("*") if path.is_file()]
        self.assertEqual(files, [])

    def test_input_ids_sha256_joins_with_newline_and_no_trailing_newline(self) -> None:
        self.assertEqual(journal_lib.input_ids_sha256(IDS_R1), sha256_ids(IDS_R1))
        self.assertNotEqual(sha256_ids(IDS_R1), hashlib.sha256(("\n".join(IDS_R1) + "\n").encode("utf-8")).hexdigest())
        self.assertEqual(journal_lib.input_ids_sha256([]), hashlib.sha256(b"").hexdigest())

    def test_r1_fields_stay_r1_after_r2_exists(self) -> None:
        r1 = self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-r1", marker=True)
        r1_bytes = r1.read_bytes()
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["files_written"], 1)
        journal = Path(out["path"])
        text = journal.read_text(encoding="utf-8")
        sha = sha256_ids(IDS_R1)
        self.assertIn(f"\ndigest_id: {DIGEST_ID}\n", text)
        self.assertIn("\nsnapshot_revision: 1\n", text)
        self.assertIn(f"\ninput_ids_sha256: {sha}\n", text)
        self.assertEqual(text.count("digest_id:"), 1)
        self.assertEqual(text.count("snapshot_revision:"), 1)
        self.assertEqual(text.count("input_ids_sha256:"), 1)
        self.assertNotIn("## 本周 digest", text)
        self.assertNotIn("SNAPSHOT-BODY-r1", text)
        self.assertNotIn("in-snap-r1-aaa", text)
        self.assertNotIn("information-flow-weekly-digest", text)
        self.assertEqual(journal_lib.fingerprint(text), approval["payload_sha256"])
        saved = journal.read_bytes()

        self.write_snapshot(2, IDS_R2, body="SNAPSHOT-BODY-r2")
        self.assertEqual(r1.read_bytes(), r1_bytes)
        self.assertEqual(journal.read_bytes(), saved)
        self.assertIn("snapshot_revision: 1", journal.read_text(encoding="utf-8"))
        self.assertNotIn(sha256_ids(IDS_R2), journal.read_text(encoding="utf-8"))

        switched = self.approval(IDS_R2, revision=2)
        rc, out = self.invoke(switched, "--digest-snapshot", SPEC_R2)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "conflict")
        self.assertEqual(out["files_written"], 0)
        self.assertEqual(journal.read_bytes(), saved)
        self.assertNotIn("snapshot_revision: 2", journal.read_text(encoding="utf-8"))

        rc, retry = self.invoke(approval, "--digest-snapshot", SPEC_R1, action="retry")
        self.assertEqual(rc, 0, retry)
        self.assertTrue(retry["already_persisted"])
        self.assertEqual(retry["files_written"], 0)
        rc, again = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 0, again)
        self.assertTrue(again["already_persisted"])
        self.assertEqual(again["files_written"], 0)
        self.assertEqual(journal.read_bytes(), saved)
        self.assertEqual(r1.read_bytes(), r1_bytes)

    def test_empty_input_ids_list_is_recorded(self) -> None:
        self.write_snapshot(1, [], body="SNAPSHOT-BODY-empty")
        approval = self.approval([])
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 0, out)
        text = Path(out["path"]).read_text(encoding="utf-8")
        self.assertIn(f"\ninput_ids_sha256: {hashlib.sha256(b'').hexdigest()}\n", text)
        self.assertNotIn("SNAPSHOT-BODY-empty", text)

    def test_missing_file(self) -> None:
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "unavailable")
        self.assertIn("missing", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_digest_id_mismatch(self) -> None:
        self.write_snapshot(1, IDS_R1, digest_id="dg-cy-19990101", body="SNAPSHOT-BODY-other")
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "validation_error")
        self.assertIn("digest_id", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_revision_mismatch(self) -> None:
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-rev")
        path = self.vault / "📋 Digests" / "cycles" / CYCLE_ID / "r1.md"
        path.write_text(path.read_text(encoding="utf-8").replace("snapshot_revision: 1", "snapshot_revision: 2"), encoding="utf-8")
        approval = self.approval(IDS_R1, revision=1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "validation_error")
        self.assertIn("snapshot_revision", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_missing_input_ids(self) -> None:
        self.write_snapshot(1, None, body="SNAPSHOT-BODY-no-ids")
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "validation_error")
        self.assertIn("input_ids", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_file_symlink_is_refused(self) -> None:
        outside = self.tmp / "outside.md"
        outside.write_text(snapshot_text(DIGEST_ID, 1, IDS_R1, "SNAPSHOT-BODY-link"), encoding="utf-8")
        link_dir = self.vault / "📋 Digests" / "cycles" / CYCLE_ID
        link_dir.mkdir(parents=True)
        (link_dir / "r1.md").symlink_to(outside)
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "unavailable")
        self.assertIn("symlink", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_ancestor_symlink_escape_is_refused(self) -> None:
        outside = self.tmp / "outside-cycles"
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-escape", directory=outside / CYCLE_ID)
        digests = self.vault / "📋 Digests"
        digests.mkdir()
        (digests / "cycles").symlink_to(outside, target_is_directory=True)
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "unavailable")
        self.assertTrue("symlink" in out["message"] or "escapes" in out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_unsafe_spec_is_rejected(self) -> None:
        approval = self.approval(IDS_R1)
        for spec in ("dg-cy-20261015/../../x@r1", "dg-cy-20261015@r0", "../etc/passwd"):
            rc, out = self.invoke(approval, "--digest-snapshot", spec)
            self.assertEqual(rc, 2, out)
            self.assertEqual(out["status"], "validation_error", spec)
            self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_approval_hash_must_match_the_snapshot_file(self) -> None:
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-r1")
        approval = self.approval(IDS_R2, revision=1)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "validation_error")
        self.assertIn("do not match", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_snapshot_fields_require_the_flag(self) -> None:
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-r1")
        approval = self.approval(IDS_R1)
        rc, out = self.invoke(approval)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "validation_error")
        self.assertIn("--digest-snapshot", out["message"])
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

    def test_confirmation_still_refuses(self) -> None:
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-r1")
        approval = self.approval(IDS_R1, confirmed=False, phrase="可以写")
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "refused")
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()

        wrong_phrase = self.approval(IDS_R1, phrase="先别写")
        rc, out = self.invoke(wrong_phrase, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "refused")
        self.assert_no_journal()

    def test_stale_approval_includes_snapshot_frontmatter(self) -> None:
        self.write_snapshot(1, IDS_R1, body="SNAPSHOT-BODY-r1")
        approval = self.approval(IDS_R1)
        bare = {
            key: value
            for key, value in approval.items()
            if key not in {"digest_id", "snapshot_revision", "input_ids_sha256", "payload_sha256"}
        }
        without = journal_lib.render_journal(bare)
        with_fields = journal_lib.render_journal(approval)
        self.assertNotEqual(journal_lib.fingerprint(without), journal_lib.fingerprint(with_fields))
        self.assertIn("input_ids_sha256:", with_fields)
        self.assertNotIn("input_ids_sha256:", without)
        approval["payload_sha256"] = journal_lib.fingerprint(without)
        rc, out = self.invoke(approval, "--digest-snapshot", SPEC_R1)
        self.assertEqual(rc, 2, out)
        self.assertEqual(out["status"], "stale_approval")
        self.assertEqual(out["files_written"], 0)
        self.assert_no_journal()


if __name__ == "__main__":
    unittest.main()
