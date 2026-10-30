#!/usr/bin/env python3
"""Synthetic checks for the journal pack. Temp vaults only. No live DigitalBrain."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "tests" / "synthetic" / "journal_pack"
JOURNAL_TOOLS = ROOT / "skills" / "journal" / "tools"
COGNITION_TOOLS = ROOT / "skills" / "cognition" / "tools"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(JOURNAL_TOOLS))

import journal_lib  # noqa: E402
import package_journal_pack  # noqa: E402
import weekly_intake  # noqa: E402


def run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    body = proc.stdout.strip() or "{}"
    return proc.returncode, json.loads(body)


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


def save_journal(vault: Path, approval: dict, action: str = "save") -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        return run_json(
            [
                sys.executable,
                str(JOURNAL_TOOLS / "write_journal.py"),
                action,
                "--vault",
                str(vault),
                "--approval",
                str(path),
            ]
        )


class IntakeSelectionTests(unittest.TestCase):
    def test_unchecked_related_and_new_channel_are_not_journal_material(self) -> None:
        text = (SYN / "intake_unchecked_and_new_channel.md").read_text(encoding="utf-8")
        items = weekly_intake.parse_items(text)
        self.assertEqual(len(items), 3)
        report = journal_lib.journal_material(items, ["合成项目甲"])
        self.assertEqual(report["selected_count"], 1)
        self.assertEqual(report["skipped_unchecked_related_count"], 2)
        self.assertTrue(report["selected"][0]["checked"])
        self.assertTrue(all(not item["checked"] for item in report["skipped_unchecked_related"]))
        headings = [item["heading"] for item in report["selected"]]
        self.assertTrue(any("和合成项目甲呼应" in heading for heading in headings))
        skipped_headings = [item["heading"] for item in report["skipped_unchecked_related"]]
        self.assertTrue(any("没勾" in heading for heading in skipped_headings))
        self.assertEqual(len(report["new_channels"]), 1)
        self.assertEqual(report["new_channels"][0]["channel"], "synthetic-voice")
        self.assertFalse(report["new_channels"][0]["checked"])
        self.assertNotIn("synthetic-voice", [item["channel"] for item in report["selected"]])


class JournalGateTests(unittest.TestCase):
    def test_refuse_writes_zero_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            for phrase, confirmed in (( "", False), ("写周记", True), ("OK 写", False)):
                approval = journal_approval(confirmed=confirmed, phrase=phrase)
                rc, data = save_journal(vault, approval)
                self.assertEqual(rc, 2, data)
                self.assertEqual(data["status"], "refused", data)
                self.assertEqual(data["files_written"], 0)
                self.assertFalse((vault / "📝 Journal").exists())
                self.assertFalse((vault / "📖 Cognition").exists())

    def test_confirm_saves_one_readable_journal(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            approval = journal_approval()
            rc, data = save_journal(vault, approval)
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["files_written"], 1)
            path = Path(data["path"])
            text = path.read_text(encoding="utf-8")
            self.assertEqual(journal_lib.fingerprint(text), data["fingerprint"])
            self.assertIn("event_id: AIC-SYN-JOURNAL-0001", text)
            self.assertIn("合成正文。不是私人日记。", text)
            self.assertEqual(len(list((vault / "📝 Journal").glob("*.md"))), 1)
            self.assertFalse((vault / "📖 Cognition").exists())

    def test_duplicate_deliveries_keep_one_file_and_retry_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            approval = journal_approval()
            contents = []
            for _ in range(3):
                rc, data = save_journal(vault, approval)
                self.assertEqual(rc, 0, data)
                contents.append(Path(data["path"]).read_text(encoding="utf-8"))
            rc, data = save_journal(vault, approval)
            self.assertEqual(rc, 0, data)
            self.assertTrue(data["already_persisted"])
            self.assertEqual(data["files_written"], 0)
            files = list((vault / "📝 Journal").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertEqual(len(set(contents)), 1)
            self.assertEqual(files[0].read_text(encoding="utf-8"), contents[0])

            files[0].unlink()
            rc, recovered = save_journal(vault, approval, action="retry")
            self.assertEqual(rc, 0, recovered)
            self.assertEqual(recovered["files_written"], 1)
            self.assertFalse(recovered["already_persisted"])
            rc, again = save_journal(vault, approval, action="retry")
            self.assertEqual(rc, 0, again)
            self.assertTrue(again["already_persisted"])
            self.assertEqual(again["files_written"], 0)
            self.assertEqual(len(list((vault / "📝 Journal").glob("*.md"))), 1)

    def test_conflict_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            approval = journal_approval()
            rc, data = save_journal(vault, approval)
            self.assertEqual(rc, 0, data)
            path = Path(data["path"])
            before = path.read_bytes()
            changed = journal_approval(body="另一份合成正文，不应覆盖。\n")
            rc, conflict = save_journal(vault, changed)
            self.assertEqual(rc, 2, conflict)
            self.assertEqual(conflict["status"], "conflict")
            self.assertEqual(conflict["files_written"], 0)
            self.assertEqual(path.read_bytes(), before)
            rc, retry = save_journal(vault, changed, action="retry")
            self.assertEqual(retry["status"], "conflict")
            self.assertEqual(path.read_bytes(), before)


class CognitionPackTests(unittest.TestCase):
    def evidence_text(self) -> str:
        text = (SYN / "evidence_accept.md").read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        return text

    def call_write(self, vault: Path, action: str, payload: str, approval: dict) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            payload_path = work / "payload.md"
            payload_path.write_text(payload, encoding="utf-8")
            approval_path = work / "approval.json"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            return run_json(
                [
                    sys.executable,
                    str(COGNITION_TOOLS / "write_cognition.py"),
                    action,
                    "--vault",
                    str(vault),
                    "--payload",
                    str(payload_path),
                    "--approval",
                    str(approval_path),
                ]
            )

    def accept_approval(self, payload: str) -> dict:
        return {
            "kind": "create",
            "id": "evidence-20261005-pack-echo",
            "type": "evidence",
            "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        }

    def test_reject_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = self.evidence_text()
            rc, data = self.call_write(
                vault,
                "create",
                payload,
                {"kind": "reject", "id": "evidence-20261005-pack-echo", "type": "evidence"},
            )
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "unauthorized")
            self.assertFalse((vault / "📖 Cognition").exists())

    def test_accept_retrieve_conflict_and_duplicate_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = self.evidence_text()
            approval = self.accept_approval(payload)
            rc, created = self.call_write(vault, "create", payload, approval)
            self.assertEqual(rc, 0, created)
            self.assertEqual(created["status"], "success")
            stored = Path(created["path"]).read_text(encoding="utf-8")
            self.assertIn('source: "[[source-synthetic-journal-pack]]"', stored)
            self.assertEqual(stored, payload)

            rc, found = run_json(
                [
                    sys.executable,
                    str(COGNITION_TOOLS / "retrieve_cognition.py"),
                    "--vault",
                    str(vault),
                    "--id",
                    "evidence-20261005-pack-echo",
                ]
            )
            self.assertEqual(rc, 0, found)
            self.assertEqual(found["status"], "found")
            self.assertEqual(found["matched_ids"], ["evidence-20261005-pack-echo"])
            self.assertEqual(found["evidence"][0]["source"], "[[source-synthetic-journal-pack]]")

            other = payload.replace(
                "Synthetic pack echo is retrievable only after an explicit accept.",
                "Synthetic pack echo was overwritten.",
            )
            other_approval = self.accept_approval(other)
            before = Path(created["path"]).read_bytes()
            rc, conflict = self.call_write(vault, "retry", other, other_approval)
            self.assertEqual(rc, 2, conflict)
            self.assertEqual(conflict["status"], "conflict")
            self.assertEqual(Path(created["path"]).read_bytes(), before)

            for _ in range(3):
                rc, retry = self.call_write(vault, "retry", payload, approval)
                self.assertEqual(rc, 0, retry)
                self.assertTrue(retry["already_persisted"])
            self.assertEqual(len(list((vault / "📖 Cognition").rglob("*.md"))), 1)
            self.assertEqual(Path(created["path"]).read_bytes(), before)


class PackageTests(unittest.TestCase):
    def test_readme_forbids_future_dated_digest_in_canonical_repo(self) -> None:
        text = (ROOT / "packaging" / "JOURNAL_PACK_README.md").read_text(encoding="utf-8")
        self.assertIn("测试和集成跑不得往 DigitalBrain 正本仓", text)
        self.assertIn("不得写出比本次运行的 Asia/Hong_Kong 日期更晚的日期文件", text)
        self.assertIn("必须走真实写入路径的测试，只用当天日期", text)
    def test_zip_hashes_and_excludes_collectors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw)
            manifest = package_journal_pack.build(out)
            zip_path = out / manifest["zip_name"]
            self.assertEqual(
                hashlib.sha256(zip_path.read_bytes()).hexdigest(),
                manifest["zip_sha256"],
            )
            self.assertIsNone(manifest["git_commit_of_package"])
            self.assertFalse(manifest["published"])
            names = zipfile.ZipFile(zip_path).namelist()
            self.assertIn("skills/journal/tools/write_journal.py", names)
            self.assertIn("skills/cognition/tools/write_cognition.py", names)
            self.assertIn("skills/cognition/tools/retrieve_cognition.py", names)
            blob = "\n".join(names)
            for part in package_journal_pack.FORBIDDEN_PARTS:
                self.assertNotIn(part, blob)
            for item in manifest["files"]:
                info = zipfile.ZipFile(zip_path).read(item["path"])
                self.assertEqual(hashlib.sha256(info).hexdigest(), item["sha256"])
                self.assertEqual(hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest(), item["sha256"])
            version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
            self.assertEqual(version, "0.1.10")
            self.assertEqual(manifest["plugin_version_field"], version)

    def test_chatgpt_upload_zip_matches_uploaded_layout(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            first = package_journal_pack.build_chatgpt_plugin(Path(raw) / "a")
            second = package_journal_pack.build_chatgpt_plugin(Path(raw) / "b")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            archive = zipfile.ZipFile(first)
            names = archive.namelist()
            self.assertEqual(names[0], "plugin.json")
            self.assertEqual(names[1], ".codex-plugin/plugin.json")
            self.assertEqual(names[2:], sorted(names[2:]))
            self.assertIn("scripts/build_weekly_digest.py", names)
            self.assertIn("scripts/source_groups.py", names)
            self.assertIn("scripts/weekly_intake.py", names)
            self.assertIn("skills/journal/tools/capture_thought.py", names)
            self.assertIn("skills/journal/references/thoughts.md", names)
            self.assertIn("skills/cognition/tools/write_cognition.py", names)
            self.assertIn("skills/daily-cluster/SKILL.md", names)
            self.assertIn("skills/daily-cluster/tools/write_cluster.py", names)
            self.assertIn("skills/socratic-discuss/SKILL.md", names)
            self.assertEqual(
                archive.read("skills/journal/SKILL.md"),
                (ROOT / "skills" / "journal" / "SKILL.md").read_bytes(),
            )
            self.assertIn("写周记的第一步", archive.read("skills/journal/SKILL.md").decode("utf-8"))
            self.assertNotIn("packaging/chatgpt-upload/root-plugin.json", names)
            blob = "\n".join(names)
            for part in package_journal_pack.FORBIDDEN_PARTS:
                self.assertNotIn(part, blob)
            version = package_journal_pack.plugin_version()
            self.assertEqual(version, "0.1.10")
            for entry in ("plugin.json", ".codex-plugin/plugin.json"):
                meta = json.loads(archive.read(entry))
                self.assertEqual(meta["version"], version)
                self.assertIn("归堆", meta["description"])
                interface = meta.get("interface") or meta["extensions"]["com.openai"]["interface"]
                self.assertIn("归堆", interface["defaultPrompt"])
                self.assertIn("归堆之后讨论", interface["defaultPrompt"])
                self.assertIn("归堆之后讨论", interface["longDescription"])
                self.assertIn("两边 cluster 都读", interface["longDescription"])
                self.assertNotIn("只读没有后缀的正本", interface["longDescription"])
                self.assertIn("不写没有后缀的正本", interface["longDescription"])
                self.assertIn("落盘仍只写当天文件，不把旧料重抄进新文件", interface["longDescription"])
                self.assertIn(
                    "换地方装上这个 plugin，现行归堆／带到第二天／周六两边都读等功能应能完整跑",
                    interface["longDescription"],
                )
                info = archive.getinfo(entry)
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr, 0x81A40000)
                self.assertEqual(info.flag_bits, 0)
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.extra, b"")

    def test_extracted_zip_runs_builder(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            zip_path = package_journal_pack.build_chatgpt_plugin(root / "dist")
            extract = root / "plugin"
            extract.mkdir()
            zipfile.ZipFile(zip_path).extractall(extract)
            help_proc = subprocess.run(
                [sys.executable, "scripts/build_weekly_digest.py", "--help"],
                cwd=extract,
                capture_output=True,
                text=True,
            )
            self.assertEqual(help_proc.returncode, 0, help_proc.stderr)
            self.assertIn("--week", help_proc.stdout)
            vault = root / "vault"
            daily = vault / "📋 Digests" / "daily"
            daily.mkdir(parents=True)
            fixture = ROOT / "tests" / "fixtures" / "weekly_digest" / "real" / "2026-10-13.md"
            (daily / "2026-10-13.md").write_bytes(fixture.read_bytes())
            build = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_weekly_digest.py",
                    "--vault",
                    str(vault),
                    "--week",
                    "2026-W42",
                ],
                cwd=extract,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            digest = (vault / "📋 Digests" / "2026-W42" / "digest.md").read_text(encoding="utf-8")
            self.assertIn("T-2026W42-1", digest)
            self.assertIn("Yan Talk", digest)


if __name__ == "__main__":
    unittest.main()
