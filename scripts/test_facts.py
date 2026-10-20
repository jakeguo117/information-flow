#!/usr/bin/env python3
"""AC09 and Fact write rules. Synthetic records in a temp directory only."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills" / "facts" / "tools" / "write_fact.py"
STATUSES = ("待核验", "已核验", "有争议", "已更正")


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def load(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


class FactWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "facts.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, fact_id: str, status: str, text: str, **extra: str) -> subprocess.CompletedProcess[str]:
        args = [
            "write",
            "--out",
            str(self.out),
            "--id",
            fact_id,
            "--verification-status",
            status,
            "--text",
            text,
        ]
        for key, value in extra.items():
            args.extend([f"--{key}", value])
        return run(args)

    def test_ac09_retrieve_without_journal_reference(self) -> None:
        keyword = "合成南瓜"
        proc = self.write(
            "fact-synthetic-ac09",
            "待核验",
            f"合成事实，关键词是{keyword}。",
            link="https://example.com/synthetic-fact",
            date="2026-10-20",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        written = load(proc)["record"]
        self.assertEqual(written["verification_status"], "待核验")
        self.assertNotIn("journal", written)
        self.assertFalse(any(path.name.lower().find("journal") >= 0 for path in Path(self.tmp.name).rglob("*")))

        found = run(["retrieve", "--out", str(self.out), "--keyword", keyword])
        self.assertEqual(found.returncode, 0, found.stderr)
        matches = load(found)["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "fact-synthetic-ac09")
        self.assertEqual(matches[0]["records"][0]["link"], "https://example.com/synthetic-fact")
        self.assertEqual(matches[0]["records"][0]["date"], "2026-10-20")
        self.assertNotIn("journal", matches[0]["records"][0])

        content_record = {"fact_id": matches[0]["id"]}
        cited = [node for node in matches if node["id"] == content_record["fact_id"]]
        self.assertEqual(cited[0]["records"][0]["text"].find(keyword), matches[0]["records"][0]["text"].find(keyword))
        self.assertGreaterEqual(cited[0]["records"][0]["text"].find(keyword), 0)

    def test_four_verification_statuses_can_be_written(self) -> None:
        for status in STATUSES:
            proc = self.write(f"fact-status-{status}", status, f"合成事实状态{status}")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(load(proc)["record"]["verification_status"], status)
        lines = self.out.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            [json.loads(line)["verification_status"] for line in lines],
            list(STATUSES),
        )

    def test_invalid_verification_status_rejected(self) -> None:
        for status in ("verified", "已验证", ""):
            with self.subTest(status=status):
                before = list(Path(self.tmp.name).iterdir())
                proc = self.write("fact-bad-status", status, "合成事实")
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertEqual(list(Path(self.tmp.name).iterdir()), before)
                self.assertIn("verification_status", load(proc)["error"])

    def test_missing_required_fields_exit_nonzero(self) -> None:
        cases = [
            ["write", "--out", str(self.out), "--verification-status", "待核验", "--text", "合成"],
            ["write", "--out", str(self.out), "--id", "fact-missing-status", "--text", "合成"],
            ["write", "--out", str(self.out), "--id", "fact-missing-text", "--verification-status", "待核验"],
        ]
        for args in cases:
            with self.subTest(args=args):
                proc = run(args)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertFalse(load(proc)["ok"])

    def test_correction_appends_and_old_record_unchanged(self) -> None:
        original = "合成事实原文"
        first = self.write(
            "fact-synthetic-correct",
            "待核验",
            original,
            link="https://example.com/synthetic-old",
            date="2026-10-01",
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        snap1 = self.out.read_bytes()

        changed = self.write("fact-synthetic-correct", "已核验", original)
        self.assertEqual(changed.returncode, 0, changed.stderr)
        snap2 = self.out.read_bytes()
        self.assertTrue(snap2.startswith(snap1))

        corrected = self.write(
            "fact-synthetic-correct",
            "已更正",
            "合成事实更正后",
            link="https://example.com/synthetic-new",
            date="2026-10-20",
        )
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        snap3 = self.out.read_bytes()
        self.assertTrue(snap3.startswith(snap2))

        records = [json.loads(line) for line in self.out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([item["verification_status"] for item in records], ["待核验", "已核验", "已更正"])
        self.assertEqual(records[0]["text"], original)
        self.assertEqual(records[0]["link"], "https://example.com/synthetic-old")
        self.assertEqual(records[0]["date"], "2026-10-01")
        self.assertEqual(records[1]["text"], original)
        self.assertNotIn("link", records[1])
        self.assertEqual(records[2]["text"], "合成事实更正后")
        self.assertEqual(snap3.splitlines()[0], snap1.splitlines()[0])

    def test_dry_run_writes_no_file(self) -> None:
        proc = run(
            [
                "write",
                "--out",
                str(self.out),
                "--id",
                "fact-dry",
                "--verification-status",
                "待核验",
                "--text",
                "合成事实",
                "--dry-run",
            ]
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(load(proc)["dry_run"])
        self.assertFalse(self.out.exists())
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])

        created = self.write("fact-dry", "待核验", "合成事实")
        self.assertEqual(created.returncode, 0, created.stderr)
        before = self.out.read_bytes()
        again = run(
            [
                "write",
                "--out",
                str(self.out),
                "--id",
                "fact-dry",
                "--verification-status",
                "已更正",
                "--text",
                "不应写盘",
                "--dry-run",
            ]
        )
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.out.read_bytes(), before)

        directory = Path(self.tmp.name) / "caller-dir"
        directory.mkdir()
        via_dir = run(
            [
                "write",
                "--out",
                str(directory),
                "--id",
                "fact-dir",
                "--verification-status",
                "有争议",
                "--text",
                "合成目录",
                "--dry-run",
            ]
        )
        self.assertEqual(via_dir.returncode, 0, via_dir.stderr)
        self.assertEqual(list(directory.iterdir()), [])

    def test_out_directory_appends_inside_caller_directory(self) -> None:
        directory = Path(self.tmp.name) / "caller-dir"
        directory.mkdir()
        proc = run(
            [
                "write",
                "--out",
                str(directory),
                "--id",
                "fact-dir",
                "--verification-status",
                "待核验",
                "--text",
                "合成目录写入",
            ]
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        log = directory / "facts.jsonl"
        self.assertTrue(log.is_file())
        self.assertEqual(list(directory.iterdir()), [log])
        found = run(["retrieve", "--out", str(directory), "--keyword", "目录写入"])
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(load(found)["matches"][0]["id"], "fact-dir")

    def test_source_is_stdlib_and_has_no_vault_path(self) -> None:
        source = TOOL.read_text(encoding="utf-8")
        self.assertNotIn("DigitalBrain", source)
        tree = ast.parse(source)
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
        allowed = set(sys.stdlib_module_names)
        self.assertTrue(modules <= allowed, modules - allowed)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
