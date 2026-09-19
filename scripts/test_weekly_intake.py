#!/usr/bin/env python3
"""Temp-vault tests for weekly intake.md. No Hermes. No live vault."""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import daily_digest  # noqa: E402
import weekly_intake  # noqa: E402
import weekly_rollup  # noqa: E402

DAY = dt.date(2026, 9, 14)
EMPTY_DAY = dt.date(2026, 9, 15)
WEEK = "2026-W38"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_vault(root: Path) -> Path:
    snipd = (
        "---\n"
        "show_title: The Joe Rogan Experience\n"
        "episode_title: #2552 - Guest\n"
        "last_snip_date: 2026-09-14\n"
        "---\n"
        "# #2552 - Guest\n\n"
        "## Episode metadata\n"
        "- Episode AI description: Agents can leave the box. Superintelligence beats humans everywhere.\n\n"
        "## Snips\n\n"
        "- Training does not guarantee aligned behavior.\n"
    )
    write(root / "Snipd" / "Data" / "JRE" / "ep.md", snipd)

    weread = (
        "---\n"
        "title: 金刚经（白话版）\n"
        "---\n"
        "> 📌 [应无所住而生其心。](weread://x)\n"
        "> ⏱ 2026-09-14 16:58:24\n"
        "> 📌 [凡所有相皆是虚妄。](weread://y)\n"
        "> ⏱ 2026-09-14 15:48:11\n"
    )
    write(root / "📥 Inbox" / "WeRead" / "金刚经（白话版）.md", weread)

    youtube = (
        "---\n"
        "title: Who Is Actually Running the World?\n"
        "channel: Trevor Noah\n"
        "generator: journal-youtube-likes\n"
        "---\n"
        "# Who Is Actually Running the World?\n\n"
        "## 摘句\n\n"
        "- You're gonna be programmed by this thing.\n"
        "- of the apartheid government who said,\n"
        "- Access to that kind of stuff disappears instantly.\n"
    )
    write(root / "📥 Inbox" / "YouTube-Likes" / "2026-09-14-CqtvQ9uDBho.md", youtube)
    return root


class WeeklyIntakeTests(unittest.TestCase):
    def test_new_sources_write_intake_with_thread(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = make_vault(Path(raw))
            rc = daily_digest.main(["--vault", str(vault), "--date", DAY.isoformat()])
            self.assertEqual(rc, 0)
            dest = weekly_intake.intake_path(vault, WEEK)
            self.assertTrue(dest.is_file())
            text = dest.read_text(encoding="utf-8")
            self.assertIn("generator: journal-weekly-intake", text)
            self.assertIn("Agents can leave the box.", text)
            self.assertIn("应无所住而生其心。", text)
            self.assertIn("You're gonna be programmed by this thing.", text)
            self.assertNotIn("of the apartheid government who said,", text)
            self.assertIn("[[Snipd/Data/JRE/ep]]", text)
            self.assertNotIn(f"{EMPTY_DAY.isoformat()}-Digest.md", [p.name for p in dest.parent.iterdir()])

    def test_empty_day_does_not_create_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            vault.mkdir(exist_ok=True)
            rc = daily_digest.main(["--vault", str(vault), "--date", EMPTY_DAY.isoformat()])
            self.assertEqual(rc, 0)
            self.assertFalse(weekly_intake.intake_path(vault, WEEK).exists())
            digests = vault / "📋 Digests"
            self.assertFalse(digests.exists())

    def test_wikilink_not_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = make_vault(Path(raw))
            daily_digest.main(["--vault", str(vault), "--date", DAY.isoformat()])
            daily_digest.main(["--vault", str(vault), "--date", DAY.isoformat()])
            text = weekly_intake.intake_path(vault, WEEK).read_text(encoding="utf-8")
            self.assertEqual(text.count("[[Snipd/Data/JRE/ep]]"), 1)
            self.assertIn("item_count: 3", text)

    def test_briefing_excludes_checked_and_sinks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = make_vault(Path(raw))
            daily_digest.main(["--vault", str(vault), "--date", DAY.isoformat()])
            dest = weekly_intake.intake_path(vault, WEEK)
            text = dest.read_text(encoding="utf-8")
            text = text.replace("- [ ] Snipd ·", "- [x] Snipd ·", 1)
            dest.write_text(text, encoding="utf-8")
            rc = weekly_rollup.main(["--vault", str(vault), "--date", DAY.isoformat()])
            self.assertEqual(rc, 0)
            out = dest.read_text(encoding="utf-8")
            briefing, _, items = out.partition("## 条目")
            self.assertNotIn("The Joe Rogan Experience", briefing)
            self.assertIn("Trevor Noah", briefing)
            self.assertIn("金刚经", briefing)
            snipd_at = items.find("- [x] Snipd")
            last_open = max(items.rfind("- [ ] YouTube"), items.rfind("- [ ] WeRead"))
            self.assertGreater(snipd_at, last_open)

    def test_refuses_non_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = make_vault(Path(raw))
            dest = weekly_intake.intake_path(vault, WEEK)
            write(dest, "# handmade\n")
            with self.assertRaises(SystemExit):
                daily_digest.main(["--vault", str(vault), "--date", DAY.isoformat()])

    def test_resolve_intake_prefers_current_week(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📋 Digests" / "2026-W37" / "intake.md", "w37\n")
            write(vault / "📋 Digests" / "2026-W38" / "intake.md", "w38\n")
            dest = weekly_intake.resolve_intake(vault, dt.date(2026, 9, 19))
            self.assertEqual(dest, weekly_intake.intake_path(vault, "2026-W38"))
            self.assertEqual(
                weekly_intake.main(["--vault", str(vault), "--date", "2026-09-19"]),
                0,
            )

    def test_resolve_intake_falls_back_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📋 Digests" / "2026-W37" / "intake.md", "w37\n")
            dest = weekly_intake.resolve_intake(vault, dt.date(2026, 9, 19))
            self.assertEqual(dest, weekly_intake.intake_path(vault, "2026-W37"))

    def test_resolve_intake_none_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            vault.mkdir(exist_ok=True)
            self.assertIsNone(weekly_intake.resolve_intake(vault, dt.date(2026, 9, 19)))
            self.assertEqual(
                weekly_intake.main(["--vault", str(vault), "--date", "2026-09-19"]),
                1,
            )


if __name__ == "__main__":
    raise SystemExit(unittest.main())
