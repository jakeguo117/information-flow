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
            self.assertLess(text.index("## 可以借用的"), text.index("## 待分组"))
            self.assertIn(
                "- **F-2026W42-1**｜Snipd · Synthetic Show — 合成讨论一句｜[[📥 Inbox/Snipd/Data/Synthetic/ep]]",
                text,
            )
            self.assertIn("  - 合成摘句应保留", text)
            self.assertNotIn("无字幕", text)
            self.assertIn("- **F-2026W42-2**｜合成引用一句｜[原文](https://example.com/quote)", text)
            self.assertIn(
                "- **C-2026W42-1**｜合成可借用的方法｜[[📖 Resources/Synthetic/method]]",
                text,
            )
            self.assertIn("- **T-2026W42-1**｜合成论点一句｜[[📥 Inbox/Synthetic/thesis]]", text)
            self.assertIn("  - 我的看法：", text)
            self.assertEqual(text.count("我的看法"), 1)
            self.assertEqual(text.count("Synthetic/ep"), 1)
            self.assertNotIn("没有新到的条目", text)
            again = weekly.main(["--vault", str(vault), "--date", "2026-10-15"])
            self.assertEqual(again, 0)
            self.assertEqual(dest.read_text(encoding="utf-8"), text)
            self.assertIn("sha256=", text)

    def test_intake_fallback_when_the_week_has_no_daily_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "intake-2026-W42.md", "📋 Digests", "2026-W42", "intake.md")
            before = (vault / "📋 Digests" / "2026-W42" / "intake.md").read_bytes()
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            text = weekly.digest_path(vault, "2026-W42").read_text(encoding="utf-8")
            self.assertIn(
                "**P-2026W42-1**｜Synthetic · Example — 合成摄入一条｜[[📥 Inbox/Synthetic/item]]",
                text,
            )
            self.assertIn("## 可以引用的\n\n本周无", text)
            self.assertNotIn("只有标题没有链接", text)
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
            self.assertEqual(rc, weekly.EXISTS_EXIT)
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
            self.assertIn("## 待分组", text)

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


class RealWeekTests(unittest.TestCase):
    def test_w42_source_sections_land_in_the_three_groups(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            for day in ("2026-10-12", "2026-10-13", "2026-10-14"):
                place(vault, f"real/{day}.md", "📋 Digests", "daily", f"{day}.md")
            note = vault / "📥 Inbox" / "YouTube-Likes" / "2026-10-13-aw-zxPHhh8U.md"
            note.parent.mkdir(parents=True)
            note.write_text(
                "---\nsource_url: https://example.com/watch\n---\n\n# synthetic note\n",
                encoding="utf-8",
            )
            snipd = vault / "📥 Inbox" / "Snipd" / "Data" / "Behind the Craft" / "We Built Grok Bot. Here Are Our 14 Best Bots _ Peng Zheng & Lauren Tan.md"
            snipd.parent.mkdir(parents=True)
            snipd.write_text(
                "Episode page https://share.snipd.com/episode/example\n",
                encoding="utf-8",
            )
            xnote = vault / "📥 Inbox" / "X-Bookmarks" / "2026-10-14-0x_kaize-2110055685048209702.md"
            xnote.parent.mkdir(parents=True)
            xnote.write_text(
                "---\ntweet_url: https://x.com/example/status/1\n---\n\n# tip\n",
                encoding="utf-8",
            )
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            text = weekly.digest_path(vault, "2026-W42").read_text(encoding="utf-8")
            thesis = text.split("## 值得讨论的（thesis）", 1)[1].split("## ", 1)[0]
            quoted = text.split("## 可以引用的", 1)[1].split("## ", 1)[0]
            borrowed = text.split("## 可以借用的", 1)[1].split("## ", 1)[0]
            pending = text.split("## 待分组", 1)[1]
            self.assertIn("本周无", pending)
            self.assertNotIn("- **P-", pending)
            self.assertEqual(thesis.count("- **T-2026W42-"), 2)
            self.assertIn("Yan Talk", thesis)
            self.assertIn("[原文](https://example.com/watch)", thesis)
            self.assertIn("我的看法：", thesis)
            self.assertIn("禪心悟道", thesis)
            self.assertEqual(quoted.count("- **F-2026W42-"), 1)
            self.assertIn("Behind the Craft", quoted)
            self.assertIn("[原文](https://share.snipd.com/episode/example)", quoted)
            self.assertIn("Lauren Tan, a Grok Bot engineer", quoted)
            self.assertEqual(borrowed.count("- **C-2026W42-"), 1)
            self.assertIn("@0x_kaize", borrowed)
            self.assertIn("[原文](https://x.com/example/status/1)", borrowed)
            self.assertNotIn("#佛法智慧", text)
            self.assertNotIn("无字幕", text)

    def test_explicit_group_tag_is_not_a_source_guess(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            daily = vault / "📋 Digests" / "daily" / "2026-10-14.md"
            daily.parent.mkdir(parents=True)
            daily.write_text(
                "\n".join(
                    [
                        "## YouTube",
                        "",
                        "- [[📥 Inbox/Synthetic/tagged]] — YouTube · Channel — 已标明的一条",
                        "  - group: F",
                        "  - 这句引用留下",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, 0)
            text = weekly.digest_path(vault, "2026-W42").read_text(encoding="utf-8")
            quoted = text.split("## 可以引用的", 1)[1].split("## ", 1)[0]
            self.assertIn("**F-2026W42-1**｜YouTube · Channel — 已标明的一条｜[[📥 Inbox/Synthetic/tagged]]", quoted)
            self.assertIn("这句引用留下", quoted)
            self.assertNotIn("group:", quoted)
            pending = text.split("## 待分组", 1)[1]
            self.assertIn("本周无", pending)
            self.assertNotIn("已标明", pending)


class RefreshTests(unittest.TestCase):
    def test_later_day_refreshes_an_unedited_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "real/2026-10-12.md", "📋 Digests", "daily", "2026-10-12.md")
            place(vault, "real/2026-10-13.md", "📋 Digests", "daily", "2026-10-13.md")
            first = weekly.main(["--vault", str(vault), "--date", "2026-10-14"])
            self.assertEqual(first, 0)
            dest = weekly.digest_path(vault, "2026-W42")
            early = dest.read_text(encoding="utf-8")
            self.assertEqual(early.count("- **T-2026W42-"), 1)
            self.assertIn("Yan Talk", early)
            place(vault, "real/2026-10-14.md", "📋 Digests", "daily", "2026-10-14.md")
            second = weekly.main(["--vault", str(vault), "--date", "2026-10-15"])
            self.assertEqual(second, 0)
            later = dest.read_text(encoding="utf-8")
            self.assertEqual(later.count("- **T-2026W42-"), 2)
            self.assertEqual(later.count("- **F-2026W42-"), 1)
            self.assertEqual(later.count("- **C-2026W42-"), 1)
            self.assertIn("Behind the Craft", later)
            self.assertIn("@0x_kaize", later)

    def test_hand_edit_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "real/2026-10-13.md", "📋 Digests", "daily", "2026-10-13.md")
            self.assertEqual(weekly.main(["--vault", str(vault), "--week", "2026-W42"]), 0)
            dest = weekly.digest_path(vault, "2026-W42")
            edited = dest.read_text(encoding="utf-8").replace("Yan Talk", "手改过的频道", 1)
            dest.write_text(edited, encoding="utf-8")
            place(vault, "real/2026-10-14.md", "📋 Digests", "daily", "2026-10-14.md")
            rc = weekly.main(["--vault", str(vault), "--date", "2026-10-15"])
            self.assertEqual(rc, weekly.EXISTS_EXIT)
            kept = dest.read_text(encoding="utf-8")
            self.assertEqual(kept, edited)
            self.assertNotIn("Behind the Craft", kept)

    def test_filled_opinion_is_not_replaced_even_if_hash_matches(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "daily-2026-10-12.md", "📋 Digests", "daily", "2026-10-12.md")
            place(vault, "root-2026-10-13-Digest.md", "📋 Digests", "2026-10-13-Digest.md")
            self.assertEqual(weekly.main(["--vault", str(vault), "--week", "2026-W42"]), 0)
            dest = weekly.digest_path(vault, "2026-W42")
            filled_body = dest.read_text(encoding="utf-8")
            body, _recorded = weekly.split_generated(filled_body)
            self.assertFalse(weekly.opinion_filled(body))
            body = body.replace("  - 我的看法：", "  - 我的看法：已经写了", 1)
            self.assertTrue(weekly.opinion_filled(body))
            dest.write_text(weekly.stamp(body), encoding="utf-8")
            before = dest.read_text(encoding="utf-8")
            rc = weekly.main(["--vault", str(vault), "--week", "2026-W42"])
            self.assertEqual(rc, weekly.EXISTS_EXIT)
            self.assertEqual(dest.read_text(encoding="utf-8"), before)

    def test_monday_refreshes_the_previous_week(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            place(vault, "real/2026-10-13.md", "📋 Digests", "daily", "2026-10-13.md")
            self.assertEqual(weekly.week_from_date(dt.date(2026, 10, 19)), "2026-W43")
            self.assertEqual(weekly.previous_week("2026-W43"), "2026-W42")
            self.assertEqual(weekly.main(["--vault", str(vault), "--date", "2026-10-14"]), 0)
            dest = weekly.digest_path(vault, "2026-W42")
            self.assertEqual(dest.read_text(encoding="utf-8").count("- **T-2026W42-"), 1)
            sunday = vault / "📋 Digests" / "daily" / "2026-10-18.md"
            sunday.write_text(
                "- [[📥 Inbox/X-Bookmarks/sunday-item]] — X · @synthetic：周日才到的一条\n",
                encoding="utf-8",
            )
            rc = weekly.main(["--vault", str(vault), "--date", "2026-10-19", "--also-previous"])
            self.assertEqual(rc, 0)
            text = dest.read_text(encoding="utf-8")
            self.assertIn("周日才到的一条", text)
            self.assertIn("Yan Talk", text)
            self.assertFalse(weekly.digest_path(vault, "2026-W43").exists())

    def test_marker_pattern_is_shared_and_strips_crlf(self) -> None:
        journal = ROOT / "skills" / "journal" / "tools" / "journal_lib.py"
        builder = ROOT / "scripts" / "build_weekly_digest.py"

        def pattern_line(path: Path) -> str:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("DIGEST_MARKER_PATTERN = "):
                    return line
            raise AssertionError(path)

        self.assertEqual(pattern_line(journal), pattern_line(builder))
        sys.path.insert(0, str(ROOT / "skills" / "journal" / "tools"))
        import journal_lib  # noqa: E402

        body = "---\nweek: 2026-W42\n---\n\n# 本周 digest（2026-W42）\n\n合成正文。\n"
        stamped = weekly.stamp(body).replace("\n", "\r\n")
        self.assertIn("\r\n<!-- information-flow-weekly-digest", stamped)
        stripped = journal_lib.strip_generator_marker(stamped)
        self.assertNotIn("information-flow-weekly-digest", stripped)
        self.assertIn("合成正文。", stripped)
        parsed, recorded = weekly.split_generated(weekly.stamp(body))
        self.assertEqual(parsed, body if body.endswith("\n") else body + "\n")
        self.assertEqual(len(recorded or ""), 64)


class SourceUrlTests(unittest.TestCase):
    def test_image_url_key_does_not_beat_episode_url(self) -> None:
        text = (
            "---\n"
            "image_url: https://wsrv.nl/cover.png\n"
            "episode_url: https://share.snipd.com/episode/example\n"
            "---\n"
        )
        self.assertEqual(weekly.note_source_url(text), "https://share.snipd.com/episode/example")

    def test_body_image_does_not_hide_the_source_link(self) -> None:
        text = (
            "---\n"
            "title: note\n"
            "---\n"
            "\n"
            "![](https://cdn.example/photo.jpg)\n"
            "https://wsrv.nl/?url=thumb.webp\n"
            "[原文](https://example.com/post)\n"
        )
        self.assertEqual(weekly.note_source_url(text), "https://example.com/post")

    def test_body_rule_does_not_hide_the_first_link(self) -> None:
        text = (
            "---\n"
            "title: note\n"
            "---\n"
            "\n"
            "https://example.com/first\n"
            "\n"
            "---\n"
            "\n"
            "https://cdn.example/later.png\n"
        )
        self.assertEqual(weekly.note_source_url(text), "https://example.com/first")

    def test_unclosed_frontmatter_does_not_yield_a_thumb_url(self) -> None:
        text = "---\nthumb: https://example.com/not-a-source\ntitle: unfinished\n"
        self.assertIsNone(weekly.split_frontmatter(text))
        self.assertEqual(weekly.note_source_url(text), "")

    def test_one_source_group_table(self) -> None:
        import daily_takeaway
        import source_groups

        self.assertIs(daily_takeaway.SOURCE_GROUP, source_groups.SOURCE_GROUP)
        self.assertIs(daily_takeaway.SECTION_GROUP, source_groups.SECTION_GROUP)
        self.assertEqual(weekly.group_for_heading("YouTube"), source_groups.SECTION_GROUP["YouTube"])
        self.assertEqual(weekly.GENERATOR_VERSION, "2")


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
            self.assertIn("待分组", text)
            self.assertIn("本周无", text)
            self.assertIn("P-2026W42-1", text)
            self.assertNotIn("T-2026W42-a", text)
        reading = skill.split("### 1. 读输入", 1)[1].split("### 2.", 1)[0]
        step = skill.split("0. **先拿当周 digest", 1)[1].split("\n1. ", 1)[0]
        order = brief.split("## 读取顺序", 1)[1]
        self.assertLess(reading.index("先读当周 digest"), reading.index("先旧周记"))
        self.assertLess(order.index("digest.md"), order.index("📝 Journal/"))
        self.assertIn(phrase, reading)
        self.assertIn(phrase, step)
        self.assertIn("T-2026W42-1", step)
        description = skill.split("description:", 1)[1].split("\n", 1)[0]
        self.assertIn("写周记", description)
        self.assertTrue(description.strip().strip('"').startswith("写周记"))
        self.assertIn("一行一条", description)
        body = skill.split("---", 2)[-1]
        self.assertLess(body.index("## 写周记的第一段输出"), body.index("## 随手记"))
        self.assertIn("一行一条", body.split("## 随手记", 1)[0])
        self.assertIn("写周记的第一段输出", brief.split("## 读取顺序", 1)[0])
        self.assertIn("一行一条", brief.split("## 读取顺序", 1)[0])
        cognition = (ROOT / "skills" / "cognition" / "SKILL.md").read_text(encoding="utf-8")
        cognition_description = cognition.split("description:", 1)[1].split("\n", 1)[0]
        self.assertNotIn("写周记", cognition_description)
        workflow = (ROOT / ".github" / "workflows" / "daily-intake.yml").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/build_weekly_digest.py --vault digitalbrain --also-previous", workflow)
        self.assertIn('"$status" -eq 2', workflow)
        digest_skill = (ROOT / "skills" / "digest" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/build_weekly_digest.py", digest_skill)
        self.assertIn("📋 Digests/{YYYY-Wnn}/digest.md", digest_skill)
        manual = (ROOT / ".github" / "workflows" / "weekly-digest.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", manual)
        self.assertIn("push:", manual)
        self.assertIn("branches: [main]", manual)
        self.assertIn(".github/weekly-digest-request", manual)
        self.assertIn('EVENT_NAME" = "workflow_dispatch"', manual)
        self.assertIn("INPUT_WEEK", manual)
        self.assertIn("YYYY-Www", manual)
        self.assertIn("^[0-9]{4}-W(0[1-9]|[1-4][0-9]|5[0-3])$", manual)
        self.assertIn("permissions:", manual)
        self.assertIn("contents: read", manual)
        self.assertIn("contents: read", workflow)
        self.assertIn("${{ secrets.DIGITALBRAIN_TOKEN }}", workflow)
        self.assertIn("group: digitalbrain-digests", manual)
        self.assertIn("group: digitalbrain-digests", workflow)
        self.assertNotIn("schedule:", manual)
        self.assertNotIn("pull_request:", manual)
        self.assertNotIn("--force", manual)
        self.assertIn('"$status" -eq 3', manual)
        self.assertIn('"$status" -eq 3', workflow)
        self.assertIn("${{ secrets.DIGITALBRAIN_TOKEN }}", manual)
        request = (ROOT / ".github" / "weekly-digest-request").read_text(encoding="utf-8")
        self.assertEqual(request, "2026-W42\n")


if __name__ == "__main__":
    unittest.main()
