#!/usr/bin/env python3
"""The daily takeaway lists five sources and never writes weekly intake."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_takeaway  # noqa: E402
import weekly_intake  # noqa: E402
from test_weekly_intake import make_vault, write  # noqa: E402

DAY = dt.date(2026, 9, 14)


def add_social(vault: Path) -> None:
    write(
        vault / "📥 Inbox" / "Instagram-Saves" / "2026-09-14-author-abc.md",
        "# @author：一个概念\n\n- 视频发布时间：2026-09-14\n",
    )
    write(
        vault / "📥 Inbox" / "X-Bookmarks" / "2026-09-14-user-1.md",
        "# @user：另一条\n\n- 发布时间：2026-09-14 08:21（UTC+8）\n",
    )
    write(
        vault / "📥 Inbox" / "Instagram-Saves" / "2026-09-13-old.md",
        "# @old：昨天以前\n",
    )


class DailyTakeawayTests(unittest.TestCase):
    def test_five_sources_and_no_weekly_intake(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = make_vault(Path(raw))
            add_social(vault)
            rc = daily_takeaway.main(["--vault", str(vault), "--date", DAY.isoformat()])
            self.assertEqual(rc, 0)
            dest = daily_takeaway.takeaway_path(vault, DAY)
            text = dest.read_text(encoding="utf-8")
            self.assertIn("generator: information-flow-daily-takeaway", text)
            for heading in ("## Snipd", "## WeRead", "## YouTube", "## Instagram", "## X"):
                self.assertIn(heading, text)
            self.assertIn("[[📥 Inbox/Snipd/Data/JRE/ep]]", text)
            self.assertIn("[[📥 Inbox/WeRead/金刚经（白话版）]]", text)
            self.assertIn("[[📥 Inbox/YouTube-Likes/2026-09-14-CqtvQ9uDBho]]", text)
            self.assertIn("[[📥 Inbox/Instagram-Saves/2026-09-14-author-abc]]", text)
            self.assertIn("[[📥 Inbox/X-Bookmarks/2026-09-14-user-1]]", text)
            self.assertNotIn("2026-09-13-old", text)
            self.assertFalse(weekly_intake.intake_path(vault, "2026-W38").exists())

    def test_empty_day_still_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc = daily_takeaway.main(["--vault", str(vault), "--date", "2026-09-15"])
            self.assertEqual(rc, 0)
            text = daily_takeaway.takeaway_path(vault, dt.date(2026, 9, 15)).read_text(encoding="utf-8")
            self.assertIn("这一天五个入口都没有新到的条目。", text)
            self.assertEqual(text.count("\n没有新到的条目。\n"), 5)
            self.assertFalse((vault / "📋 Digests" / "2026-W38").exists())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
