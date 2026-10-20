#!/usr/bin/env python3
"""AC09 and Fact write rules. Synthetic records in a temp directory only."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "skills" / "facts" / "tools" / "write_fact.py"
STATUSES = ("unverified", "verified", "disputed", "corrected")
REF = "https://example.com/synthetic#p1"
STATEMENT = "合成事实，关键词是南瓜。"
HAND_FACT_ID = "fact-3bc1db9181f7"
RECORDED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def load(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def formula_id(source_ref: str, statement: str) -> str:
    digest = hashlib.sha1(f"{source_ref}|{statement}".encode("utf-8")).hexdigest()[:12]
    return f"fact-{digest}"


class FactWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "facts.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(
        self,
        statement: str,
        status: str = "unverified",
        source_ref: str = REF,
        as_of: str = "2026-10-20",
        fact_id: str | None = None,
        out: Path | None = None,
        extra: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        args = [
            "write",
            "--out",
            str(out or self.out),
            "--statement",
            statement,
            "--validation-state",
            status,
            "--as-of",
            as_of,
            "--source-ref",
            source_ref,
        ]
        if fact_id is not None:
            args.extend(["--fact-id", fact_id])
        if extra:
            args.extend(extra)
        return run(args)

    def test_ac09_retrieve_without_journal_reference(self) -> None:
        keyword = "南瓜"
        first = self.write(STATEMENT, "unverified", as_of="2026-10-20")
        self.assertEqual(first.returncode, 0, first.stderr)
        written = load(first)["record"]
        fact_id = written["fact_id"]
        self.assertEqual(fact_id, HAND_FACT_ID)
        self.assertEqual(written["validation_state"], "unverified")
        self.assertNotIn("journal", written)
        self.assertFalse(any("journal" in path.name.lower() for path in Path(self.tmp.name).rglob("*")))

        other_statement = "合成事实，这条没有目标词。"
        other = self.write(other_statement, source_ref="https://example.com/synthetic#p2")
        self.assertEqual(other.returncode, 0, other.stderr)
        other_id = load(other)["record"]["fact_id"]
        self.assertNotEqual(other_id, fact_id)

        found = run(["retrieve", "--out", str(self.out), "--keyword", keyword])
        self.assertEqual(found.returncode, 0, found.stderr)
        matches = load(found)["matches"]
        self.assertEqual([node["fact_id"] for node in matches], [fact_id])
        self.assertNotIn(other_id, [node["fact_id"] for node in matches])

        corrected = self.write(
            "合成更正，不再重复那个目标词。",
            "corrected",
            fact_id=fact_id,
            source_ref="https://example.com/synthetic#p9",
        )
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        self.assertEqual(load(corrected)["record"]["fact_id"], fact_id)

        again = run(["retrieve", "--out", str(self.out), "--keyword", keyword])
        self.assertEqual(again.returncode, 0, again.stderr)
        matches = load(again)["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["fact_id"], fact_id)
        self.assertEqual(
            [item["validation_state"] for item in matches[0]["records"]],
            ["unverified", "corrected"],
        )
        self.assertEqual(len(matches[0]["records"]), 2)

    def test_four_verification_statuses_can_be_written(self) -> None:
        seen: list[str] = []
        for status in STATUSES:
            statement = f"合成事实状态{status}"
            proc = self.write(statement, status, source_ref=f"https://example.com/synthetic#{status}")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            record = load(proc)["record"]
            self.assertEqual(record["validation_state"], status)
            self.assertEqual(record["fact_id"], formula_id(f"https://example.com/synthetic#{status}", statement))
            seen.append(status)
        lines = self.out.read_text(encoding="utf-8").splitlines()
        self.assertEqual([json.loads(line)["validation_state"] for line in lines], seen)

    def test_invalid_verification_status_rejected(self) -> None:
        for status in ("待核验", "已验证", "verified ", ""):
            with self.subTest(status=status):
                before = list(Path(self.tmp.name).iterdir())
                proc = self.write(STATEMENT, status)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertEqual(list(Path(self.tmp.name).iterdir()), before)
                self.assertIn("validation_state", load(proc)["error"])

    def test_missing_required_fields_exit_nonzero(self) -> None:
        cases = [
            ["write", "--out", str(self.out), "--validation-state", "unverified", "--as-of", "2026-10-20", "--source-ref", REF],
            ["write", "--out", str(self.out), "--statement", STATEMENT, "--as-of", "2026-10-20", "--source-ref", REF],
            ["write", "--out", str(self.out), "--statement", STATEMENT, "--validation-state", "unverified", "--source-ref", REF],
            ["write", "--out", str(self.out), "--statement", STATEMENT, "--validation-state", "unverified", "--as-of", "2026-10-20"],
        ]
        for args in cases:
            with self.subTest(args=args):
                proc = run(args)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertFalse(load(proc)["ok"])

    def test_blank_fact_id_or_statement_rejected(self) -> None:
        for extra in (["--fact-id", "   "], ["--statement", "   "]):
            with self.subTest(extra=extra):
                args = [
                    "write",
                    "--out",
                    str(self.out),
                    "--statement",
                    STATEMENT,
                    "--validation-state",
                    "unverified",
                    "--as-of",
                    "2026-10-20",
                    "--source-ref",
                    REF,
                    *extra,
                ]
                proc = run(args)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.out.exists())
                self.assertIn("missing", load(proc)["error"])

    def test_fact_id_matches_sha1_formula(self) -> None:
        self.assertEqual(formula_id(REF, STATEMENT), HAND_FACT_ID)
        mismatch = self.write("另一句合成事实。", fact_id=HAND_FACT_ID, source_ref="https://example.com/other#p1")
        self.assertNotEqual(mismatch.returncode, 0)
        self.assertIn("fact_id", load(mismatch)["error"])
        self.assertFalse(self.out.exists())
        dry = self.write(STATEMENT, extra=["--dry-run"])
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(load(dry)["record"]["fact_id"], HAND_FACT_ID)
        self.assertFalse(self.out.exists())
        proc = self.write(STATEMENT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(load(proc)["record"]["fact_id"], HAND_FACT_ID)
        second_ref = "https://example.com/ignored#p9"
        two = self.write(STATEMENT, extra=["--source-ref", second_ref])
        self.assertEqual(two.returncode, 0, two.stderr)
        self.assertEqual(load(two)["record"]["fact_id"], HAND_FACT_ID)
        self.assertEqual(load(two)["record"]["source_refs"], [REF, second_ref])

    def test_later_write_reuses_fact_id(self) -> None:
        first = self.write(STATEMENT)
        self.assertEqual(first.returncode, 0, first.stderr)
        fact_id = load(first)["record"]["fact_id"]
        changed = "合成更正后的陈述。"
        second = self.write(changed, "corrected", fact_id=fact_id, source_ref="https://example.com/synthetic#later")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(load(second)["record"]["fact_id"], fact_id)
        self.assertNotEqual(formula_id("https://example.com/synthetic#later", changed), fact_id)
        self.assertNotEqual(formula_id(REF, changed), fact_id)

    def test_correction_appends_and_old_record_unchanged(self) -> None:
        first = self.write(STATEMENT, "unverified", as_of="2026-10-01")
        self.assertEqual(first.returncode, 0, first.stderr)
        fact_id = load(first)["record"]["fact_id"]
        snap1 = self.out.read_bytes()

        changed = self.write(STATEMENT, "verified", fact_id=fact_id)
        self.assertEqual(changed.returncode, 0, changed.stderr)
        snap2 = self.out.read_bytes()
        self.assertTrue(snap2.startswith(snap1))

        corrected = self.write(
            "合成事实更正后",
            "corrected",
            fact_id=fact_id,
            source_ref="https://example.com/synthetic-new#p1",
            as_of="2026-10-20",
        )
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        snap3 = self.out.read_bytes()
        self.assertTrue(snap3.startswith(snap2))

        records = [json.loads(line) for line in self.out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([item["fact_id"] for item in records], [fact_id, fact_id, fact_id])
        self.assertEqual([item["validation_state"] for item in records], ["unverified", "verified", "corrected"])
        self.assertEqual(records[0]["statement"], STATEMENT)
        self.assertEqual(records[0]["source_refs"], [REF])
        self.assertEqual(records[0]["as_of"], "2026-10-01")
        self.assertEqual(records[2]["statement"], "合成事实更正后")
        self.assertEqual(records[2]["source_refs"], ["https://example.com/synthetic-new#p1"])
        self.assertEqual(snap3.splitlines()[0], snap1.splitlines()[0])

    def test_rejects_append_when_file_lacks_trailing_newline(self) -> None:
        self.out.write_bytes(b'{"fact_id":"fact-0123456789ab"}\n{"partial":true}')
        before = self.out.read_bytes()
        self.assertNotEqual(before[-1:], b"\n")
        proc = self.write(STATEMENT, fact_id=HAND_FACT_ID)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("newline", load(proc)["error"])
        self.assertEqual(self.out.read_bytes(), before)
        dry = self.write(STATEMENT, fact_id=HAND_FACT_ID, extra=["--dry-run"])
        self.assertNotEqual(dry.returncode, 0)
        self.assertEqual(self.out.read_bytes(), before)

    def test_dry_run_writes_no_file(self) -> None:
        proc = self.write(STATEMENT, extra=["--dry-run"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(load(proc)["dry_run"])
        self.assertEqual(load(proc)["record"]["fact_id"], HAND_FACT_ID)
        self.assertFalse(self.out.exists())
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])

        created = self.write(STATEMENT)
        self.assertEqual(created.returncode, 0, created.stderr)
        before = self.out.read_bytes()
        again = self.write("不应写盘", "corrected", fact_id=HAND_FACT_ID, extra=["--dry-run"])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.out.read_bytes(), before)

        directory = Path(self.tmp.name) / "caller-dir"
        directory.mkdir()
        via_dir = self.write("合成目录", "disputed", source_ref="https://example.com/synthetic#dir", out=directory, extra=["--dry-run"])
        self.assertEqual(via_dir.returncode, 0, via_dir.stderr)
        self.assertEqual(list(directory.iterdir()), [])

    def test_dry_run_missing_parent_exits_nonzero(self) -> None:
        missing = Path(self.tmp.name) / "missing-parent" / "facts.jsonl"
        proc = self.write(STATEMENT, out=missing, extra=["--dry-run"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("directory", load(proc)["error"])
        self.assertFalse(missing.parent.exists())
        self.assertFalse(missing.exists())
        real = self.write(STATEMENT, out=missing)
        self.assertNotEqual(real.returncode, 0)
        self.assertFalse(missing.parent.exists())

    def test_as_of_accepts_date_or_hong_kong_offset(self) -> None:
        accepted = ("2026-10-20", "2026-10-20T11:50:00+08:00")
        for value in accepted:
            with self.subTest(value=value):
                proc = self.write(f"合成时间{value}", as_of=value, source_ref=f"https://example.com/synthetic#{value}")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(load(proc)["record"]["as_of"], value)
        for value in ("2026-10-20T11:50:00", "2026-10-20T11:50:00Z", "2026-13-01", "10/20/2026"):
            with self.subTest(value=value):
                before = self.out.read_bytes() if self.out.exists() else b""
                proc = self.write("合成坏时间", as_of=value, source_ref="https://example.com/synthetic#bad-time")
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("as_of", load(proc)["error"])
                after = self.out.read_bytes() if self.out.exists() else b""
                self.assertEqual(after, before)

    def test_recorded_at_is_hong_kong_iso(self) -> None:
        proc = self.write(STATEMENT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        recorded = load(proc)["record"]["recorded_at"]
        self.assertRegex(recorded, RECORDED_AT_RE)
        parsed = datetime.strptime(recorded, "%Y-%m-%dT%H:%M:%S%z")
        self.assertEqual(parsed.utcoffset(), timedelta(hours=8))

    def test_unknown_schema_version_rejected(self) -> None:
        proc = self.write(STATEMENT, extra=["--schema-version", "facts-9.9"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("schema_version", load(proc)["error"])
        self.assertFalse(self.out.exists())
        ok = self.write(STATEMENT)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(load(ok)["record"]["schema_version"], "facts-0.1")

    def test_visibility_defaults_and_is_not_validated(self) -> None:
        proc = self.write(STATEMENT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(load(proc)["record"]["visibility"], "private-jake")
        other = self.write(
            "合成可见性未定。",
            source_ref="https://example.com/synthetic#vis",
            extra=["--visibility", "not-yet-decided"],
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        self.assertEqual(load(other)["record"]["visibility"], "not-yet-decided")

    def test_out_directory_appends_inside_caller_directory(self) -> None:
        directory = Path(self.tmp.name) / "caller-dir"
        directory.mkdir()
        proc = self.write("合成目录写入", out=directory)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        log = directory / "facts.jsonl"
        self.assertTrue(log.is_file())
        self.assertEqual(list(directory.iterdir()), [log])
        found = run(["retrieve", "--out", str(directory), "--keyword", "目录写入"])
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(load(found)["matches"][0]["fact_id"], formula_id(REF, "合成目录写入"))

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
