#!/usr/bin/env python3
"""本周完整性闸。合成日期，不读库。"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import preflight  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "discuss-to-resources-ideas" / "SKILL.md"
HK = ZoneInfo("Asia/Hong_Kong")
ET = ZoneInfo("America/New_York")

# 2026-10-31 周六。本周周一至周日 = 2026-10-26 .. 2026-11-01。
SAT = dt.datetime(2026, 10, 31, 12, 0, tzinfo=HK)
SUN = dt.datetime(2026, 11, 1, 12, 0, tzinfo=HK)
MON = dt.datetime(2026, 10, 26, 9, 0, tzinfo=HK)
WEEKDAYS = [
    "2026-10-26.md",
    "2026-10-27.md",
    "2026-10-28.md",
    "2026-10-29.md",
    "2026-10-30.md",
]
JOURNAL = "📝 Journal/2026-10-30 本周.md"


def gate(**overrides: object) -> dict:
    payload = {
        "run_at": SAT,
        "cluster_names": list(WEEKDAYS),
        "journal_paths": [JOURNAL],
        "inbox_days": [],
        "empty_inbox_days": [],
        "saturday_blocked": False,
    }
    payload.update(overrides)
    return preflight.evaluate(**payload)  # type: ignore[arg-type]


class WeekWindowTests(unittest.TestCase):
    def test_saturday_week_is_hong_kong_monday_to_sunday(self) -> None:
        result = gate()
        self.assertEqual(result["week_start"], "2026-10-26")
        self.assertEqual(result["week_end"], "2026-11-01")
        self.assertEqual(
            result["weekdays"],
            ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"],
        )
        self.assertEqual(result["hk_weekday"], "周六")
        self.assertTrue(result["passed"])
        self.assertTrue(result["produce"])

    def test_eastern_saturday_morning_is_still_the_same_hong_kong_day(self) -> None:
        # 美东 2026-10-31 00:23 仍是港时周六。
        run_at = dt.datetime(2026, 10, 31, 0, 23, tzinfo=ET)
        result = gate(run_at=run_at)
        self.assertEqual(result["hk_date"], "2026-10-31")
        self.assertEqual(result["week_start"], "2026-10-26")
        self.assertEqual(result["week_end"], "2026-11-01")


class JournalTests(unittest.TestCase):
    def test_zero_journal_blocks_even_when_cluster_is_complete(self) -> None:
        result = gate(journal_paths=[])
        self.assertFalse(result["passed"])
        self.assertFalse(result["produce"])
        self.assertEqual(result["journal_count"], 0)
        self.assertTrue(any("0 篇" in item for item in result["missing"]))
        self.assertIn("write_idea.py", result["remind"])
        self.assertIn("同周周日", result["remind"])

    def test_sunday_journal_counts_and_friday_is_not_required(self) -> None:
        result = gate(journal_paths=["📝 Journal/2026-11-01 周日一篇.md"])
        self.assertEqual(result["journal_count"], 1)
        self.assertTrue(result["passed"])
        self.assertFalse(any("周五" in item and "必须" in item for item in result["missing"]))

    def test_thought_folder_and_previous_week_do_not_count(self) -> None:
        result = gate(
            journal_paths=[
                "📝 Journal/想法/2026-10-30 随手.md",
                "📝 Journal/想法/2026-W44/thought-20261030-1200.md",
                "📝 Journal/素材/2026-10-30.md",
                "📝 Journal/2026-10-25 上周日.md",
                "📝 Journal/2026-11-02 下周一.md",
            ]
        )
        self.assertEqual(result["journal_count"], 0)
        self.assertFalse(result["passed"])

    def test_bare_root_filename_counts(self) -> None:
        result = gate(journal_paths=["2026-10-28 标题.md"])
        self.assertEqual(result["journal_count"], 1)
        self.assertTrue(result["passed"])


class ClusterTests(unittest.TestCase):
    def test_multiday_main_file_covers_the_range(self) -> None:
        result = gate(
            cluster_names=["2026-10-26_28.md", "2026-10-29.md", "2026-10-30.md"],
            inbox_days=[dt.date(2026, 10, 26), dt.date(2026, 10, 27), dt.date(2026, 10, 28)],
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["exempt_empty_inbox"], [])

    def test_gpt_file_does_not_cover_a_day(self) -> None:
        names = ["2026-10-26.md", "2026-10-27-gpt.md", "2026-10-28.md", "2026-10-29.md", "2026-10-30.md"]
        result = gate(
            cluster_names=names,
            inbox_days=[dt.date(2026, 10, 27)],
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("缺归堆正本：2026-10-27" in item for item in result["missing"]))
        self.assertTrue(all("2026-10-26" not in item for item in result["missing"]))

    def test_empty_inbox_day_is_exempt(self) -> None:
        result = gate(
            cluster_names=["2026-10-26.md", "2026-10-28.md", "2026-10-29.md", "2026-10-30.md"],
            empty_inbox_days=[dt.date(2026, 10, 27)],
            inbox_days=[
                dt.date(2026, 10, 26),
                dt.date(2026, 10, 28),
                dt.date(2026, 10, 29),
                dt.date(2026, 10, 30),
            ],
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["exempt_empty_inbox"], ["2026-10-27"])

    def test_unchecked_inbox_is_not_treated_as_empty(self) -> None:
        result = gate(cluster_names=["2026-10-26.md"])
        self.assertFalse(result["passed"])
        text = "\n".join(result["missing"])
        self.assertIn("未查清 Inbox：2026-10-27", text)
        self.assertIn("未查清 Inbox：2026-10-30", text)
        self.assertNotIn("2026-10-26", text)

    def test_inbox_day_without_main_file_blocks(self) -> None:
        result = gate(
            cluster_names=["2026-10-26_27.md", "2026-10-28.md", "2026-10-29.md"],
            inbox_days=[dt.date(2026, 10, 30)],
            empty_inbox_days=[dt.date(2026, 10, 28)],
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any(item.startswith("缺归堆正本：2026-10-30") for item in result["missing"]))

    def test_file_from_daily_path_does_not_cover(self) -> None:
        result = gate(
            cluster_names=["📋 Digests/daily/2026-10-26.md"] + WEEKDAYS[1:],
            inbox_days=[dt.date(2026, 10, 26)],
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("2026-10-26" in item for item in result["missing"]))

    def test_invalid_span_does_not_cover(self) -> None:
        covered = preflight.cluster_covered_dates("2026-10-30_02.md")
        self.assertEqual(covered, frozenset())
        covered = preflight.cluster_covered_dates("2026-10-26_27-gpt.md")
        self.assertEqual(covered, frozenset())


class ScheduleTests(unittest.TestCase):
    def test_weekday_is_blocked(self) -> None:
        result = gate(run_at=MON)
        self.assertFalse(result["passed"])
        self.assertFalse(result["run_allowed"])
        self.assertIn("平日不跑", result["missing"][0])

    def test_sunday_without_saturday_block_does_not_run(self) -> None:
        result = gate(run_at=SUN, saturday_blocked=False)
        self.assertFalse(result["passed"])
        self.assertIn("不是改成只周日跑", result["missing"][0])
        self.assertNotIn("0 篇", "\n".join(result["missing"]))

    def test_sunday_catch_up_uses_the_same_gate(self) -> None:
        blocked = gate(run_at=SUN, saturday_blocked=True, journal_paths=[])
        self.assertFalse(blocked["passed"])
        self.assertTrue(any("0 篇" in item for item in blocked["missing"]))
        caught_up = gate(run_at=SUN, saturday_blocked=True)
        self.assertTrue(caught_up["passed"])
        self.assertEqual(caught_up["week_start"], "2026-10-26")

    def test_same_day_cannot_be_inbox_and_empty(self) -> None:
        with self.assertRaises(ValueError):
            gate(
                inbox_days=[dt.date(2026, 10, 27)],
                empty_inbox_days=[dt.date(2026, 10, 27)],
            )


class CliTests(unittest.TestCase):
    def test_exit_codes(self) -> None:
        script = TOOL_DIR / "preflight.py"
        blocked = subprocess.run(
            [
                sys.executable,
                str(script),
                "--run-at",
                "2026-10-31T12:00:00+08:00",
                "--cluster-name",
                "2026-10-26.md",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(blocked.returncode, 2)
        payload = json.loads(blocked.stdout)
        self.assertFalse(payload["produce"])
        passed = subprocess.run(
            [sys.executable, str(script), "--run-at", "2026-10-31T12:00:00+08:00"]
            + [arg for name in WEEKDAYS for arg in ("--cluster-name", name)]
            + ["--journal", JOURNAL],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertTrue(json.loads(passed.stdout)["passed"])


class SkillTextTests(unittest.TestCase):
    def test_skill_states_the_gate_without_dropping_both_read(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## 本周完整性闸", text)
        self.assertIn("preflight.py", text)
        self.assertIn("不要求必须有周五", text)
        self.assertIn("不是改成只周日跑", text)
        self.assertIn("同周周日", text)
        self.assertIn("YYYY-MM-DD-gpt.md", text)
        self.assertIn("同一天两份都在：两份都读。", text)
        self.assertIn("同一条（同一来源链接、同一段引用、或同一标题）只算一次。", text)
        self.assertIn("留更详的那份，细节不丢。", text)
        self.assertNotIn("不读 `*-gpt.md`", text)
        self.assertNotIn("不读 *-gpt.md", text)
        self.assertNotIn("只读正本", text)
        self.assertNotIn("不读 GPT", text)

    def test_route_allows_the_sunday_catch_up(self) -> None:
        route = (ROOT / "skills" / "digitalbrain-agents-route.md").read_text(encoding="utf-8")
        self.assertNotIn("周六提炼仍只在周六跑", route)
        self.assertIn("不改成只周日跑", route)
        self.assertIn("先过本周完整性闸", route)
        self.assertIn("周六提炼两边 cluster 都读、同日去重", route)


if __name__ == "__main__":
    unittest.main()
