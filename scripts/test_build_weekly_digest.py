#!/usr/bin/env python3
"""Fixtures for the weekly digest builder. Synthetic vaults only."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_weekly_digest as weekly  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "weekly_digest"


def place(vault: Path, fixture: str, *parts: str) -> Path:
    dest = vault.joinpath(*parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text((FIX / fixture).read_text(encoding="utf-8"), encoding="utf-8")
    return dest


class WeekTests(unittest.TestCase):
    def test_shanghai_date_picks_the_local_iso_week(self) -> None:
        # 2026-10-14 16:30 UTC is 2026-10-15 00:30 in Shanghai, ISO week 42.
        moment = dt.datetime(2026, 10, 14, 16, 30, tzinfo=dt.timezone.utc)
        self.assertEqual(weekly.shanghai_today(moment), dt.date(2026, 10, 15))
        self.assertEqual(weekly.week_from_date(weekly.shanghai_today(moment)), "2026-W42")
        self.assertEqual(weekly.week_days(2026, 42)[0].isoformat(), "2026-10-12")
        self.assertEqual(weekly.week_days(2026, 42)[-1].isoformat(), "2026-10-18")
        with self.assertRaises(ValueError):
            weekly.parse_week("2026-W2")
        with self.assertRaises(ValueError):
            weekly.parse_week("2026-W54")


class BuildTests(unittest.TestCase):
    def test_daily_and_root_formats_number_three_groups(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "daily-2026-10-12.md", "📋 Digests", "daily", "2026-10-12.md")
            place(vault, "root-2026-10-13-Digest.md", "📋 Digests", "2026-10-13-Digest.md")
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            dest = weekly.digest_path(vault, "2026-W42")
            text = dest.read_text(encoding="utf-8")
            self.assertIn("generator: information-flow-weekly-digest", text)
            self.assertLess(text.index("## 值得讨论的（thesis）"), text.index("## 可以引用的"))
            self.assertLess(text.index("## 可以引用的"), text.index("## 可以借用的"))
            self.assertIn(
                "- **T-2026W42-1**｜Snipd · Synthetic Show 合成讨论一句｜[[📥 Inbox/Snipd/Data/Synthetic/ep]]",
                text,
            )
            self.assertIn("- **F-2026W42-1**｜合成引用一句｜[原文](https://example.com/quote)", text)
            self.assertIn(
                "- **C-2026W42-1**｜合成可借用的方法｜[[📖 Resources/Synthetic/method]]",
                text,
            )
            self.assertEqual(text.count("Synthetic/ep"), 1)
            self.assertNotIn("我的看法", text)
            self.assertNotIn("没有新到的条目", text)
            again = weekly.main(["--vault", str(vault), "--date", "2026-10-15"])
            self.assertEqual(again, 0)
            self.assertEqual(dest.read_text(encoding="utf-8"), text)

    def test_intake_fallback_when_the_week_has_no_daily_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "intake-2026-W42.md", "📋 Digests", "2026-W42", "intake.md")
            before = (vault / "📋 Digests" / "2026-W42" / "intake.md").read_bytes()
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            text = weekly.digest_path(vault, "2026-W42").read_text(encoding="utf-8")
            self.assertIn("**T-2026W42-1**｜Synthetic · Example 合成摄入一条｜[[📥 Inbox/Synthetic/item]]", text)
            self.assertNotIn("只有标题没有链接", text)
            self.assertNotIn("## 可以引用的", text)
            self.assertEqual((vault / "📋 Digests" / "2026-W42" / "intake.md").read_bytes(), before)

    def test_empty_daily_file_does_not_fall_back_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "empty-daily.md", "📋 Digests", "daily", "2026-10-12.md")
            place(vault, "intake-2026-W42.md", "📋 Digests", "2026-W42", "intake.md")
            kept = vault / "📋 Digests" / "2026-W42" / "digest.md"
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_text("keep\n", encoding="utf-8")
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, weekly.NO_CONTENT_EXIT)
            self.assertEqual(kept.read_text(encoding="utf-8"), "keep\n")

    def test_no_sources_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, weekly.NO_CONTENT_EXIT)
            self.assertFalse((vault / "📋 Digests").exists())

    def test_symlink_daily_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            outside = Path(raw) / "outside.md"
            outside.write_text(
                "- [[📥 Inbox/Synthetic/secret]] — 不应读到\n",
                encoding="utf-8",
            )
            daily = vault / "📋 Digests" / "daily"
            daily.mkdir(parents=True)
            (daily / "2026-10-12.md").symlink_to(outside)
            place(vault, "intake-2026-W42.md", "📋 Digests", "2026-W42", "intake.md")
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            text = weekly.digest_path(vault, "2026-W42").read_text(encoding="utf-8")
            self.assertNotIn("不应读到", text)
            self.assertIn("合成摄入一条", text)

    def test_bad_args_do_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            self.assertEqual(weekly.main(["--vault", str(vault), "--week", "2026-W2"]), 1)
            self.assertEqual(weekly.main(["--vault", str(vault), "--date", "yesterday"]), 1)
            self.assertEqual(
                weekly.main(["--vault", str(vault), "--week", "2026-W42", "--date", "2026-10-15"]),
                1,
            )
            self.assertEqual(weekly.main(["--vault", str(vault / "missing"), "--week", "2026-W42"]), 1)
            self.assertFalse((vault / "📋 Digests").exists())


class SkillContractTests(unittest.TestCase):
    def test_read_order_matches_discussion_step(self) -> None:
        skill = (ROOT / "skills" / "journal" / "SKILL.md").read_text(encoding="utf-8")
        brief = (ROOT / "skills" / "journal" / "references" / "weekly-brief.md").read_text(encoding="utf-8")
        phrase = "「缺文件就跳过」不适用于 digest"
        for text in (skill, brief):
            self.assertIn("📋 Digests/{YYYY-Wnn}/digest.md", text)
            self.assertIn("📋 Digests/weekly-briefs/{YYYY-Wnn}.md", text)
            self.assertIn("📋 Digests/weekly-briefs/{YYYY-Wnn}/digest.md", text)
            self.assertIn("本周 digest 还没有", text)
            self.assertIn(phrase, text)
            self.assertIn("值得讨论的", text)
            self.assertIn("可以引用的", text)
            self.assertIn("可以借用的", text)
        reading = skill.split("### 1. 读输入", 1)[1].split("### 2.", 1)[0]
        step = skill.split("0. **先拿当周 digest", 1)[1].split("\n1. ", 1)[0]
        order = brief.split("## 读取顺序", 1)[1]
        self.assertLess(reading.index("先读当周 digest"), reading.index("先旧周记"))
        self.assertLess(order.index("digest.md"), order.index("📝 Journal/"))
        self.assertIn(phrase, reading)
        self.assertIn(phrase, step)
        self.assertIn("T-2026W42-1", step)
        workflow = (ROOT / ".github" / "workflows" / "daily-intake.yml").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/build_weekly_digest.py --vault digitalbrain", workflow)
        self.assertIn('"$status" -eq 2', workflow)
        digest_skill = (ROOT / "skills" / "digest" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/build_weekly_digest.py", digest_skill)
        self.assertIn("📋 Digests/{YYYY-Wnn}/digest.md", digest_skill)


if __name__ == "__main__":
    unittest.main()
