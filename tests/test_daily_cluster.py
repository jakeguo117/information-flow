#!/usr/bin/env python3
"""Gates for weekday cluster writes. Temp vaults only."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "skills" / "daily-cluster" / "tools"
sys.path.insert(0, str(TOOLS))

import cluster_lib  # noqa: E402

A_SHA = "34c66732b7d4004b1e4e116ce3ca7749cf027a7e1ff20f7cc87c2cb1cc2142e7"
SOCRATIC_SHA = "e1e4f68aaead7d4d2a5b3cea414c44bdd5ececc81e8386bd695772d316c0fda2"
NEW_RULE = (
    "（与 21:00 例程同句）当天新增＝香港时间当日 00:00 到运行时刻内，提交进 `📥 Inbox/` 各来源子夹"
    "（X-Bookmarks、WeRead、Snipd、YouTube-Likes、Instagram-Saves）的新文件，或当天提交里被改动文件中当天新增的部分"
    "（划线 ⏱ 时间落在香港当日为准，读提交 diff 即可）；Snipd 同理；以及当天新写的随手记 thought；"
    "以 GitHub 提交时间为准（按路径列当天提交），不以 `📥 Inbox/_index/` 为准（该索引最后一条停在 2026-10-22，已不跟新料）。"
)
BOT_RULE = (
    "（与 21:00 例程同句）@bot 聊过与否只看此前 7 天加当天 `📋 Digests/cluster/` 正本（不看 `-gpt`）里的一行 "
    "`> 已聊 @bot：<划线原文开头或微信读书链接>；…`，白天聊过的也写入该行；"
    "该行有这条划线原文开头或微信读书链接即算聊过，不靠正文里是否出现过标题或链接；未聊过的 @bot 不限当天。"
)
PART3_QUOTES = (
    "> 取料口径：HKT 2026-10-28 00:00 至 21:12；按 GitHub 提交时间列 `📥 Inbox/` 各来源子夹当天提交。"
    "读到 3／共 3 个 Inbox 提交（`b71bfb99` 08:32 X 书签、`7b598b28` 10:27 YouTube 点赞、"
    "`8fce3629` 10:48 WeRead／Snipd 同步），涉及 3 个文件；Snipd、Instagram-Saves 当天无新文件；"
    "随手记 thought（`📝 Journal`）当天无提交。此前 7 天 cluster（仅本文件 part 1／2）未出现以下标题或链接。\n"
    "> 微信读书 @bot：当天新增 2 条均为纯划线，无 @bot／atbot 留言；此前 @bot（10-26 23:27「商品牛市根基被侵蚀」、"
    "10-27「共生模式」）已在白天开聊，不重复。\n"
    "> plan 标签：本批无「有执行步骤的未来打算」，无 plan 条。\n"
)


def run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout.strip() or "{}")


def body_for(date: str, line: str = "一条合成子料。") -> str:
    return (
        f"# Digests cluster · {date}\n"
        "\n"
        "> 取料口径：HKT 当日 00:00 到运行时刻。读到 1／共 1 个提交（`a1b2c3d` 09:00），涉及 1 个文件。\n"
        "\n"
        "## 宏观\n"
        "\n"
        f"{line}\n"
    )


def approval(date: str = "2026-10-28", line: str = "一条合成子料。", **extra: object) -> dict:
    body = body_for(date, line)
    data: dict = {
        "confirmed": True,
        "phrase": "可以写",
        "date": date,
        "body": body,
        "payload_sha256": cluster_lib.fingerprint(body),
    }
    data.update(extra)
    return data


def save(vault: Path, payload: dict, *extra: str) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "approval.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return run_json(
            [
                sys.executable,
                str(TOOLS / "write_cluster.py"),
                "save",
                "--vault",
                str(vault),
                "--approval",
                str(path),
                *extra,
            ]
        )


class SkillTextTests(unittest.TestCase):
    def test_routine_sentences_are_verbatim(self) -> None:
        text = (ROOT / "skills" / "daily-cluster" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("<!-- A-BEGIN -->\n") + len("<!-- A-BEGIN -->\n")
        chunk = text[start : text.index("<!-- A-END -->")]
        self.assertEqual(hashlib.sha256(chunk.encode()).hexdigest(), A_SHA)
        self.assertIn(
            "宏观｜交易｜内容与个人品牌｜用 AI 做事｜做事业／变现｜团队与工作法｜人生方向／个人想法",
            text,
        )
        self.assertIn(
            "浓缩成文一律 **full detail**（保留数字、日期、人名、原话、推理步骤；禁止为好读删减）。",
            text,
        )
        self.assertIn("3a. **plan 标签：**", text)
        self.assertIn("不要问「哪几条进 idea 池」", text)
        self.assertIn("（新定口径，与 21:00 例程同句）", text)
        self.assertIn(NEW_RULE, text)
        self.assertIn(BOT_RULE, text)
        self.assertIn("列提交必须翻页直到空页（GitHub 默认每页 30）", text)
        self.assertIn("漏掉的文件名：", text)
        self.assertIn("## （ChatGPT 适配）落盘", text)
        self.assertIn("## （ChatGPT 适配）plan 条", text)
        self.assertIn("## （ChatGPT 适配）深挖", text)
        self.assertIn("## （ChatGPT 适配·定时）", text)
        self.assertIn("先给全文→点头→落盘→再问深挖", text)
        self.assertIn("归堆之后讨论", text)
        self.assertIn("skills/socratic-discuss/SKILL.md", text)
        self.assertIn("不另写一套讨论说法", text)
        self.assertIn("append-discuss", text)
        self.assertIn("周六提炼和提炼想法只读同夹里没有 `-gpt` 的正本", text)
        self.assertIn("不另开文件夹", text)
        self.assertIn(
            "双跑期间 ChatGPT 只写 -gpt，正本由想法梳理 21:00 写，两份由 Workflow 每天对比，周六提炼只读正本；切换之后的做法另行更新。",
            text,
        )
        self.assertNotIn("今天已归过", text)
        self.assertNotIn("看见当天主文件已经在", text)
        self.assertNotIn("交互模式写主文件", text)

    def test_socratic_skill_matches_source_hash(self) -> None:
        raw = (ROOT / "skills" / "socratic-discuss" / "SKILL.md").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOCRATIC_SHA)

    def test_saturday_extract_skips_gpt_cluster_files(self) -> None:
        text = (ROOT / "skills" / "discuss-to-resources-ideas" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不读 `*-gpt.md`", text)
        self.assertIn("只读这些主 cluster 文件", text)
        self.assertIn("📋 Digests/cluster/YYYY-MM-DD.md", text)


class QuoteAndIntakeTests(unittest.TestCase):
    def test_part3_leading_quotes_and_body_quote_write(self) -> None:
        body = (
            "# Digests cluster · 2026-10-28\n"
            "\n"
            f"{PART3_QUOTES}"
            "\n"
            "## 宏观\n"
            "\n"
            "合成子料，确认 Part 3 这种文首三行引语可以落盘。\n"
            "\n"
            "> 正文里的引用块，不算文首引语。\n"
        )
        payload = approval()
        payload["body"] = body
        payload["payload_sha256"] = cluster_lib.fingerprint(body)
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, payload)
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["files_written"], 1)
            path = Path(data["path"])
            self.assertEqual(path.name, "2026-10-28-gpt.md")
            self.assertEqual(path.read_text(encoding="utf-8"), body)
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28.md").exists())

    def test_later_quote_block_does_not_fail_validation(self) -> None:
        body = (
            "# Digests cluster · 2026-10-28\n"
            "\n"
            "> 取料口径：读到 1／共 1 个提交（`b71bfb99` 08:32）。\n"
            "\n"
            "## 宏观\n"
            "\n"
            "先有一节。\n"
            "\n"
            f"{PART3_QUOTES}"
        )
        cluster_lib._validate_body("2026-10-28", body)

    def test_missing_intake_count_is_refused(self) -> None:
        body = (
            "# Digests cluster · 2026-10-28\n"
            "\n"
            "> 想法梳理 · 平日归堆 · HKT\n"
            "\n"
            "## 宏观\n"
            "\n"
            "一条。\n"
        )
        payload = approval()
        payload["body"] = body
        payload["payload_sha256"] = cluster_lib.fingerprint(body)
        with tempfile.TemporaryDirectory() as raw:
            rc, data = save(Path(raw), payload)
        self.assertEqual(rc, 2, data)
        self.assertEqual(data["status"], "validation_error")
        self.assertIn("读到 N／共 M", data["message"])
        self.assertEqual(data["files_written"], 0)

    def test_partial_read_without_missed_names_is_refused(self) -> None:
        body = body_for("2026-10-28").replace("读到 1／共 1", "读到 1／共 3")
        payload = approval()
        payload["body"] = body
        payload["payload_sha256"] = cluster_lib.fingerprint(body)
        with tempfile.TemporaryDirectory() as raw:
            rc, data = save(Path(raw), payload)
        self.assertEqual(rc, 2, data)
        self.assertEqual(data["status"], "validation_error")
        self.assertIn("漏掉的文件名", data["message"])
        self.assertEqual(data["files_written"], 0)

    def test_partial_read_with_missed_names_writes(self) -> None:
        body = body_for("2026-10-28").replace(
            "读到 1／共 1 个提交（`a1b2c3d` 09:00），涉及 1 个文件。",
            "读到 1／共 3 个提交（`a1b2c3d` 09:00）。漏掉的文件名：甲.md、乙.md",
        )
        payload = approval()
        payload["body"] = body
        payload["payload_sha256"] = cluster_lib.fingerprint(body)
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, payload)
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["files_written"], 1)
            self.assertEqual(Path(data["path"]).name, "2026-10-28-gpt.md")

    def test_discussed_bots_come_only_from_the_record_line(self) -> None:
        text = (
            "> 已聊 @bot：商品牛市根基被侵蚀；https://weread.qq.com/web/reader/example\n"
            "\n"
            "正文里也写了 https://weread.qq.com/web/reader/other ，这不算聊过。\n"
        )
        self.assertEqual(
            cluster_lib.discussed_bot_items(text),
            ["商品牛市根基被侵蚀", "https://weread.qq.com/web/reader/example"],
        )
        self.assertEqual(cluster_lib.discussed_bot_items("正文出现 @bot 链接也不算。\n"), [])


class NormalModeTests(unittest.TestCase):
    def test_confirmation_gate_writes_zero_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            for phrase, confirmed in (("", False), ("写周记", True), ("可以写", False)):
                rc, data = save(vault, approval(confirmed=confirmed, phrase=phrase))
                self.assertEqual(rc, 2, data)
                self.assertEqual(data["status"], "refused", data)
                self.assertEqual(data["files_written"], 0)
                self.assertFalse((vault / "📋 Digests").exists())

    def test_confirm_writes_gpt_file_without_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = approval()
            rc, data = save(vault, payload)
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["files_written"], 1)
            path = Path(data["path"])
            self.assertEqual(path.name, "2026-10-28-gpt.md")
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, payload["body"])
            self.assertTrue(text.startswith("# Digests cluster · 2026-10-28\n"))
            self.assertFalse(text.startswith("---"))
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28.md").exists())
            self.assertFalse((vault / "📋 Digests" / "daily").exists())

    def test_confirm_accepts_matching_gpt_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = approval(path="📋 Digests/cluster/2026-10-28-gpt.md")
            rc, data = save(vault, payload)
            self.assertEqual(rc, 0, data)
            self.assertEqual(Path(data["path"]).name, "2026-10-28-gpt.md")
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28.md").exists())

    def test_existing_gpt_file_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            path = Path(data["path"])
            before = path.read_bytes()
            for line in ("一条合成子料。", "另一份，不应覆盖。"):
                rc, again = save(vault, approval(line=line))
                self.assertEqual(rc, 2, again)
                self.assertEqual(again["status"], "refused")
                self.assertIn("已存在", again["message"])
                self.assertEqual(again["files_written"], 0)
                self.assertEqual(path.read_bytes(), before)
            files = list((vault / "📋 Digests" / "cluster").glob("*.md"))
            self.assertEqual([item.name for item in files], ["2026-10-28-gpt.md"])

    def test_daily_path_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval(path="📋 Digests/daily/2026-10-28.md"))
            self.assertEqual(rc, 2, data)
            self.assertIn("📋 Digests/daily", data["message"])
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📋 Digests" / "daily").exists())
            self.assertFalse((vault / "📋 Digests" / "cluster").exists())

    def test_normal_mode_refuses_main_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval(path="📋 Digests/cluster/2026-10-28.md"))
            self.assertEqual(rc, 2, data)
            self.assertEqual(data["status"], "refused")
            self.assertIn("main file", data["message"])
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📋 Digests" / "cluster").exists())

    def test_multiday_filename(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = approval("2026-10-26", span_end="27")
            rc, data = save(vault, payload)
            self.assertEqual(rc, 0, data)
            path = Path(data["path"])
            self.assertEqual(path.name, "2026-10-26_27-gpt.md")
            self.assertTrue(path.read_text(encoding="utf-8").startswith("# Digests cluster · 2026-10-26\n"))
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-26_27.md").exists())


class ScheduledModeTests(unittest.TestCase):
    def test_creates_gpt_file_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            payload = approval(confirmed=False, phrase="")
            rc, data = save(vault, payload, "--scheduled")
            self.assertEqual(rc, 0, data)
            self.assertEqual(data["files_written"], 1)
            path = Path(data["path"])
            self.assertEqual(path.name, "2026-10-28-gpt.md")
            self.assertEqual(path.read_text(encoding="utf-8"), payload["body"])
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28.md").exists())

    def test_refuses_main_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval(path="📋 Digests/cluster/2026-10-28.md"), "--scheduled")
            self.assertEqual(rc, 2, data)
            self.assertIn("main file", data["message"])
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📋 Digests" / "cluster").exists())

    def test_refuses_daily(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval(path="📋 Digests/daily/2026-10-28-gpt.md"), "--scheduled")
            self.assertEqual(rc, 2, data)
            self.assertIn("📋 Digests/daily", data["message"])
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📋 Digests").exists())

    def test_skip_when_gpt_file_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval(), "--scheduled")
            self.assertEqual(rc, 0, data)
            path = Path(data["path"])
            before = path.read_bytes()
            rc, again = save(vault, approval(line="定时第二次，不应覆盖。"), "--scheduled")
            self.assertEqual(rc, 0, again)
            self.assertEqual(again["message"], "skipped: already exists")
            self.assertEqual(again["files_written"], 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(list((vault / "📋 Digests" / "cluster").glob("*.md"))), 1)

    def test_multiday_gpt_filename(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval("2026-10-26", span_end="27"), "--scheduled")
            self.assertEqual(rc, 0, data)
            self.assertEqual(Path(data["path"]).name, "2026-10-26_27-gpt.md")

    def test_scheduled_missing_vault_does_not_write(self) -> None:
        vault = Path(tempfile.mkdtemp()) / "missing-vault"
        rc, data = save(vault, approval(confirmed=False, phrase=""), "--scheduled")
        self.assertEqual(rc, 2, data)
        self.assertEqual(data["status"], "unavailable")
        self.assertEqual(data["files_written"], 0)
        self.assertEqual(data["message"], "vault missing; scheduled run did not write")
        self.assertNotIn("Jake", data["message"])
        self.assertFalse(vault.exists())


def discuss_approval(date: str = "2026-10-28", note: str = "这一堆先看住房置换，数字先留着。", **extra: object) -> dict:
    data: dict = {
        "confirmed": True,
        "phrase": "可以写",
        "date": date,
        "note": note,
        "payload_sha256": cluster_lib.fingerprint(note),
    }
    data.update(extra)
    return data


def append_discuss(vault: Path, payload: dict, *extra: str) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "approval.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return run_json(
            [
                sys.executable,
                str(TOOLS / "write_cluster.py"),
                "append-discuss",
                "--vault",
                str(vault),
                "--approval",
                str(path),
                *extra,
            ]
        )


class DiscussAppendTests(unittest.TestCase):
    def test_appends_only_to_gpt_file(self) -> None:
        note = "这一堆先看住房置换，数字先留着。"
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            canonical = vault / "📋 Digests" / "cluster" / "2026-10-28.md"
            canonical.write_text("正本不能动\n", encoding="utf-8")
            before = canonical.read_bytes()
            rc, appended = append_discuss(vault, discuss_approval(note=note))
            self.assertEqual(rc, 0, appended)
            self.assertEqual(appended["files_written"], 1)
            text = Path(appended["path"]).read_text(encoding="utf-8")
            self.assertIn("## 深挖", text)
            self.assertIn(note, text)
            self.assertTrue(text.startswith("# Digests cluster · 2026-10-28\n"))
            self.assertEqual(canonical.read_bytes(), before)
            self.assertFalse(any(path.name == "2026-10-28.md" and path.read_bytes() != before for path in canonical.parent.glob("*.md")))

    def test_refuses_main_file_and_daily_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            gpt = Path(data["path"]).read_bytes()
            rc, main = append_discuss(vault, discuss_approval(path="📋 Digests/cluster/2026-10-28.md"))
            self.assertEqual(rc, 2, main)
            self.assertIn("main file", main["message"])
            self.assertEqual(main["files_written"], 0)
            self.assertEqual(Path(data["path"]).read_bytes(), gpt)
            rc, daily = append_discuss(vault, discuss_approval(path="📋 Digests/daily/2026-10-28-gpt.md"))
            self.assertEqual(rc, 2, daily)
            self.assertIn("📋 Digests/daily", daily["message"])
            self.assertEqual(daily["files_written"], 0)
            self.assertFalse((vault / "📋 Digests" / "daily").exists())

        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, missing = append_discuss(vault, discuss_approval())
            self.assertEqual(rc, 2, missing)
            self.assertEqual(missing["message"], "还没有这份 -gpt，先归堆")
            self.assertEqual(missing["files_written"], 0)
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28.md").exists())
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-28-gpt.md").exists())

    def test_refuses_without_phrase_scheduled_or_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            before = Path(data["path"]).read_bytes()
            rc, quiet = append_discuss(vault, discuss_approval(confirmed=False, phrase=""))
            self.assertEqual(rc, 2, quiet)
            self.assertEqual(quiet["files_written"], 0)
            rc, scheduled = append_discuss(vault, discuss_approval(), "--scheduled")
            self.assertEqual(rc, 2, scheduled)
            self.assertIn("not a scheduled write", scheduled["message"])
            self.assertEqual(Path(data["path"]).read_bytes(), before)
            rc, once = append_discuss(vault, discuss_approval())
            self.assertEqual(rc, 0, once)
            after = Path(data["path"]).read_bytes()
            rc, again = append_discuss(vault, discuss_approval())
            self.assertEqual(rc, 2, again)
            self.assertEqual(again["message"], "已存在，不覆盖")
            self.assertEqual(again["files_written"], 0)
            self.assertEqual(Path(data["path"]).read_bytes(), after)

    def test_multiday_and_existing_heading(self) -> None:
        note = "## 讨论 log\n\n跨了 26 和 27 两天，原话先留着。"
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            rc, data = save(vault, approval("2026-10-26", span_end="27"))
            self.assertEqual(rc, 0, data)
            rc, appended = append_discuss(vault, discuss_approval("2026-10-26", note=note, span_end="27"))
            self.assertEqual(rc, 0, appended)
            text = Path(appended["path"]).read_text(encoding="utf-8")
            self.assertEqual(Path(appended["path"]).name, "2026-10-26_27-gpt.md")
            self.assertEqual(text.count("## 讨论 log"), 1)
            self.assertNotIn("## 深挖\n\n## 讨论 log", text)
            self.assertFalse((vault / "📋 Digests" / "cluster" / "2026-10-26_27.md").exists())


class PublishTests(unittest.TestCase):
    def test_contents_create_body_has_no_sha_and_rejects_daily(self) -> None:
        body = cluster_lib.github_contents_create_body(
            "📋 Digests/cluster/2026-10-28-gpt.md",
            "合成".encode(),
            "cluster: 2026-10-28-gpt",
        )
        self.assertEqual(set(body), {"message", "content", "branch"})
        self.assertNotIn("sha", body)
        with self.assertRaises(ValueError):
            cluster_lib.github_contents_create_body(
                "📋 Digests/daily/2026-10-28.md",
                b"synthetic\n",
                "cluster: 2026-10-28",
            )
        with self.assertRaises(ValueError) as raised:
            cluster_lib.github_contents_create_body(
                "📋 Digests/cluster/2026-10-28.md",
                b"synthetic\n",
                "cluster: 2026-10-28",
            )
        self.assertIn("-gpt", str(raised.exception))

    def test_publish_pushes_one_new_file_and_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            remote = root / "remote.git"
            vault.mkdir()
            subprocess.check_call(["git", "init", "--bare", "-b", "main", str(remote)])
            subprocess.check_call(["git", "init", "-b", "main", str(vault)])
            for args in (
                ["config", "user.email", "synthetic@example.com"],
                ["config", "user.name", "Synthetic"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", *args], cwd=vault)
            (vault / "README.md").write_text("synthetic\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "README.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "init"], cwd=vault)
            subprocess.check_call(["git", "remote", "add", "origin", str(remote)], cwd=vault)
            subprocess.check_call(["git", "push", "-u", "origin", "main"], cwd=vault)
            before = int(
                subprocess.check_output(["git", "--git-dir", str(remote), "rev-list", "--count", "main"], text=True)
            )
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            rc, published = run_json(
                [
                    sys.executable,
                    str(TOOLS / "write_cluster.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    "📋 Digests/cluster/2026-10-28-gpt.md",
                ]
            )
            self.assertEqual(rc, 0, published)
            self.assertTrue(published["pushed"])
            message = subprocess.check_output(["git", "log", "-1", "--format=%s"], cwd=vault, text=True).strip()
            self.assertEqual(message, "cluster: 2026-10-28-gpt")
            rc, contents = run_json(
                [
                    sys.executable,
                    str(TOOLS / "write_cluster.py"),
                    "contents-body",
                    "--vault",
                    str(vault),
                    "--path",
                    "📋 Digests/cluster/2026-10-28-gpt.md",
                ]
            )
            self.assertEqual(rc, 2, contents)
            self.assertFalse(contents["sent"])
            self.assertNotIn("sha", contents["body"])
            rc, second = run_json(
                [
                    sys.executable,
                    str(TOOLS / "write_cluster.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    "📋 Digests/cluster/2026-10-28-gpt.md",
                ]
            )
            self.assertEqual(rc, 2, second)
            self.assertFalse(second["pushed"])
            after = int(
                subprocess.check_output(["git", "--git-dir", str(remote), "rev-list", "--count", "main"], text=True)
            )
            self.assertEqual(after, before + 1)

    def test_publish_includes_discussion_and_not_the_main_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            remote = root / "remote.git"
            vault.mkdir()
            subprocess.check_call(["git", "init", "--bare", "-b", "main", str(remote)])
            subprocess.check_call(["git", "init", "-b", "main", str(vault)])
            for args in (
                ["config", "user.email", "synthetic@example.com"],
                ["config", "user.name", "Synthetic"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", *args], cwd=vault)
            (vault / "README.md").write_text("synthetic\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "README.md"], cwd=vault)
            subprocess.check_call(["git", "commit", "-m", "init"], cwd=vault)
            subprocess.check_call(["git", "remote", "add", "origin", str(remote)], cwd=vault)
            subprocess.check_call(["git", "push", "-u", "origin", "main"], cwd=vault)
            rc, data = save(vault, approval())
            self.assertEqual(rc, 0, data)
            note = "深挖住房置换：原话和数字都留着。"
            rc, appended = append_discuss(vault, discuss_approval(note=note))
            self.assertEqual(rc, 0, appended)
            rc, published = run_json(
                [
                    sys.executable,
                    str(TOOLS / "write_cluster.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    "📋 Digests/cluster/2026-10-28-gpt.md",
                ]
            )
            self.assertEqual(rc, 0, published)
            self.assertTrue(published["pushed"])
            shown = subprocess.check_output(
                ["git", "show", "HEAD:📋 Digests/cluster/2026-10-28-gpt.md"],
                cwd=vault,
                text=True,
            )
            self.assertIn("## 深挖", shown)
            self.assertIn(note, shown)
            missing = subprocess.run(
                ["git", "cat-file", "-e", "HEAD:📋 Digests/cluster/2026-10-28.md"],
                cwd=vault,
                capture_output=True,
            )
            self.assertNotEqual(missing.returncode, 0)
            rc, second = run_json(
                [
                    sys.executable,
                    str(TOOLS / "write_cluster.py"),
                    "publish",
                    "--vault",
                    str(vault),
                    "--path",
                    "📋 Digests/cluster/2026-10-28-gpt.md",
                ]
            )
            self.assertEqual(rc, 2, second)
            self.assertFalse(second["pushed"])


if __name__ == "__main__":
    unittest.main()
