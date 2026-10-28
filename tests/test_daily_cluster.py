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
    "当天＝香港时间当日 00:00 到运行时刻。新增＝这段时间内提交进 `📥 Inbox/` 各来源子夹"
    "（X-Bookmarks、WeRead、Snipd、YouTube-Likes、Instagram-Saves）的新文件，以及当天新写的随手记 thought；"
    "以 GitHub 提交时间为准（按路径列当天提交）。不以 `📥 Inbox/_index/` 为准（该索引最后一条停在 2026-10-22，已不跟新料）。"
    "未聊过＝此前 7 天只看 `📋 Digests/cluster/` 主文件（不看 `-gpt`），主文件里没出现过该条标题或链接；未聊过的 @bot 不限当天。"
    "读不全时写明读到 N／共 M 条和漏掉的文件名，不编。"
)


def run_json(cmd: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout.strip() or "{}")


def body_for(date: str, line: str = "一条合成子料。") -> str:
    return (
        f"# Digests cluster · {date}\n"
        "\n"
        "> 想法梳理 · 平日归堆 · HKT\n"
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
        self.assertIn("## （ChatGPT 适配）落盘", text)
        self.assertIn("## （ChatGPT 适配）plan 条", text)
        self.assertIn("## （ChatGPT 适配）深挖", text)
        self.assertIn("## （ChatGPT 适配·定时）", text)
        self.assertIn("先给全文→点头→落盘→再问深挖", text)
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


class PublishTests(unittest.TestCase):
    def test_contents_create_body_has_no_sha_and_rejects_daily(self) -> None:
        body = cluster_lib.github_contents_create_body(
            "📋 Digests/cluster/2026-10-28.md",
            "合成".encode(),
            "cluster: 2026-10-28",
        )
        self.assertEqual(set(body), {"message", "content", "branch"})
        self.assertNotIn("sha", body)
        with self.assertRaises(ValueError):
            cluster_lib.github_contents_create_body(
                "📋 Digests/daily/2026-10-28.md",
                b"synthetic\n",
                "cluster: 2026-10-28",
            )

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


if __name__ == "__main__":
    unittest.main()
