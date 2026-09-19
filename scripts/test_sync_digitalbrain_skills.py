#!/usr/bin/env python3
"""Temp-vault tests for DigitalBrain skill sync. No live vault."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sync_digitalbrain_skills as sync


LEGACY_AGENTS = """# 🧠 AGENTS.md — DigitalBrain 全局指令

## 身份
- Jake

## 今天 Digest（硬路由）

用户说「今天 Digest」：立刻问 Briefing 第一条未勾选。

详见仓库内 `.cursor/skills/intake/SKILL.md`。

## Vault 结构

```
DigitalBrain/
```
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class SyncDigitalBrainSkillsTests(unittest.TestCase):
    def test_copies_skills_and_replaces_legacy_route(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "AGENTS.md", LEGACY_AGENTS)
            write(vault / "📝 Journal" / "keep.md", "old line\n")
            write(vault / "📋 Digests" / "2026-W38" / "intake.md", "do not touch\n")

            rc = sync.main(["--vault", str(vault)])
            self.assertEqual(rc, 0)

            intake = (vault / ".cursor" / "skills" / "intake" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            journal = (vault / ".cursor" / "skills" / "journal" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            agents = (vault / "AGENTS.md").read_text(encoding="utf-8")

            self.assertEqual(
                intake, (sync.SKILLS_DIR / "intake" / "SKILL.md").read_text(encoding="utf-8")
            )
            self.assertEqual(
                journal,
                (sync.SKILLS_DIR / "journal" / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "journal" / "references" / "setup.md").is_file()
            )
            self.assertIn("Jake", agents)
            self.assertIn("## Vault 结构", agents)
            self.assertIn(sync.MARK_START, agents)
            self.assertIn("客户说「可以写 / 写吧 / OK 写」之前", agents)
            self.assertNotIn("立刻问 Briefing 第一条未勾选", agents)
            self.assertEqual((vault / "📋 Digests" / "2026-W38" / "intake.md").read_text(), "do not touch\n")
            self.assertEqual((vault / "📝 Journal" / "keep.md").read_text(), "old line\n")

    def test_marked_section_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "AGENTS.md", LEGACY_AGENTS)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            sync.main(["--vault", str(vault)])
            first = (vault / "AGENTS.md").read_text(encoding="utf-8")
            sync.main(["--vault", str(vault)])
            second = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertEqual(first.count(sync.MARK_START), 1)
            self.assertEqual(first.count(sync.MARK_END), 1)

    def test_print_paths_are_exact(self) -> None:
        self.assertEqual(
            sync.commit_paths(Path("/tmp/unused")),
            [
                ".cursor/skills/intake/SKILL.md",
                ".cursor/skills/journal/SKILL.md",
                ".cursor/skills/journal/references/setup.md",
                ".cursor/skills/journal/references/weekly-brief.md",
                "AGENTS.md",
            ],
        )

    def test_missing_vault_fails(self) -> None:
        rc = sync.main(["--vault", "/tmp/information-flow-missing-vault"])
        self.assertEqual(rc, 1)

    def test_real_agents_keeps_identity_and_vault(self) -> None:
        agents = (
            "# 🧠 AGENTS.md — DigitalBrain 全局指令\n\n"
            "## 身份\n\n- **姓名：** Jake Guo / 郭劼\n\n"
            "## 今天 Digest（硬路由）\n\n"
            "立刻问 Briefing 第一条未勾选。\n\n"
            "## Vault 结构\n\n```\nDigitalBrain/\n```\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "AGENTS.md", agents)
            write(vault / "📝 Journal" / "keep.md", "old\n")
            sync.main(["--vault", str(vault)])
            out = (vault / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Jake Guo / 郭劼", out)
            self.assertIn("## Vault 结构", out)
            self.assertIn(sync.MARK_START, out)
            self.assertNotIn("立刻问 Briefing 第一条未勾选", out)


class SkillFlowContractTests(unittest.TestCase):
    def test_intake_does_not_dump_week(self) -> None:
        text = (sync.SKILLS_DIR / "intake" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("先读最近 2–3 篇", text)
        self.assertIn("呼应", text)
        self.assertIn("禁止整周附录", text)
        self.assertIn("自己认周", text)
        self.assertIn("Asia/Shanghai", text)
        self.assertNotIn("W38 有什么", text)
        self.assertNotIn("week 38", text)
        self.assertNotIn("立刻用 **Briefing** 里第一条未勾选问一句", text)
        self.assertIn("不要写 `📝 Journal/`", text)
        route = (sync.SKILLS_DIR / "digitalbrain-agents-route.md").read_text(encoding="utf-8")
        self.assertIn("自己认周", route)
        self.assertNotIn("W38 有什么", route)
        self.assertNotIn("week 38", route)

    def test_journal_waits_for_ok(self) -> None:
        text = (sync.SKILLS_DIR / "journal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("旧周记", text)
        self.assertIn("呼应", text)
        self.assertIn("可以写 / 写吧 / OK 写", text)
        self.assertIn("客户说「可以写 / 写吧 / OK 写」之前，不落盘", text)
        self.assertIn("自己认周", text)
        self.assertNotIn("W38 有什么", text)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
