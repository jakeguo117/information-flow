#!/usr/bin/env python3
"""Temp-vault tests for DigitalBrain skill sync. No live vault."""

from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_digitalbrain_skills as sync  # noqa: E402


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
            write(vault / "📖 Cognition" / "Beliefs" / "keep.md", "private cognition\n")
            write(vault / "📖 Resources" / "concepts" / "keep.md", "resource stays\n")

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
            thought_tool = vault / ".cursor" / "skills" / "journal" / "tools" / "capture_thought.py"
            thought_ref = vault / ".cursor" / "skills" / "journal" / "references" / "thoughts.md"
            self.assertEqual(
                thought_tool.read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "journal" / "tools" / "capture_thought.py").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                thought_ref.read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "journal" / "references" / "thoughts.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (vault / ".cursor" / "skills" / "cognition" / "SKILL.md").read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "cognition" / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (vault / ".cursor" / "skills" / "ideas" / "SKILL.md").read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "ideas" / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((vault / ".cursor" / "skills" / "facts" / "SKILL.md").exists())
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "references" / "schema.md").is_file()
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "references" / "retrieval.md").is_file()
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "references" / "layout.md").is_file()
            )
            self.assertTrue(
                (
                    vault / ".cursor" / "skills" / "cognition" / "tools" / "validate_cognition.py"
                ).is_file()
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "tools" / "cognition_lib.py").is_file()
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "tools" / "retrieve_cognition.py").is_file()
            )
            self.assertTrue(
                (vault / ".cursor" / "skills" / "cognition" / "tools" / "write_cognition.py").is_file()
            )
            content_skill = vault / ".cursor" / "skills" / "content" / "SKILL.md"
            content_record = (
                vault / ".cursor" / "skills" / "content" / "references" / "content-record.md"
            )
            self.assertEqual(
                content_skill.read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "content" / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                content_record.read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "content" / "references" / "content-record.md").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertIn("Jake", agents)
            self.assertIn("## Vault 结构", agents)
            self.assertIn(sync.MARK_START, agents)
            self.assertIn("客户说「可以写 / 写吧 / OK 写」之前", agents)
            self.assertNotIn("立刻问 Briefing 第一条未勾选", agents)
            self.assertEqual((vault / "📋 Digests" / "2026-W38" / "intake.md").read_text(), "do not touch\n")
            self.assertEqual((vault / "📝 Journal" / "keep.md").read_text(), "old line\n")
            self.assertEqual((vault / "📖 Cognition" / "Beliefs" / "keep.md").read_text(), "private cognition\n")
            self.assertEqual((vault / "📖 Resources" / "concepts" / "keep.md").read_text(), "resource stays\n")

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
                ".cursor/skills/digest/SKILL.md",
                ".cursor/skills/journal/SKILL.md",
                ".cursor/skills/journal/references/setup.md",
                ".cursor/skills/journal/references/weekly-brief.md",
                ".cursor/skills/journal/references/thoughts.md",
                ".cursor/skills/journal/tools/journal_lib.py",
                ".cursor/skills/journal/tools/write_journal.py",
                ".cursor/skills/journal/tools/thought_lib.py",
                ".cursor/skills/journal/tools/capture_thought.py",
                ".cursor/skills/cognition/SKILL.md",
                ".cursor/skills/cognition/references/schema.md",
                ".cursor/skills/cognition/references/retrieval.md",
                ".cursor/skills/cognition/references/layout.md",
                ".cursor/skills/cognition/tools/cognition_lib.py",
                ".cursor/skills/cognition/tools/validate_cognition.py",
                ".cursor/skills/cognition/tools/retrieve_cognition.py",
                ".cursor/skills/cognition/tools/write_cognition.py",
                ".cursor/skills/ideas/SKILL.md",
                ".cursor/skills/content/SKILL.md",
                ".cursor/skills/content/references/content-record.md",
                ".cursor/skills/content/tools/trace_content.py",
                ".cursor/skills/content-core/SKILL.md",
                ".cursor/skills/content-core/references/exemplars.md",
                ".cursor/skills/content-x/SKILL.md",
                ".cursor/skills/content-x-ops/SKILL.md",
                ".cursor/skills/content-x-article-packaging/SKILL.md",
                ".cursor/skills/content-x-process-topic/SKILL.md",
                ".cursor/skills/content-x-cta-loop/SKILL.md",
                ".cursor/skills/content-xhs/SKILL.md",
                ".cursor/skills/content-wechat/SKILL.md",
                ".cursor/skills/content-visual/SKILL.md",
                ".cursor/skills/canvas-design/SKILL.md",
                ".cursor/skills/canvas-design/LICENSE.txt",
                ".cursor/skills/canvas-design/SOURCE.md",
                ".cursor/skills/humanizer-zh/SKILL.md",
                ".cursor/skills/humanizer-zh/LICENSE",
                ".cursor/skills/humanizer-zh/LICENSE-jiji262",
                ".cursor/skills/humanizer-zh/LICENSE-qu-ai-wei",
                ".cursor/skills/humanizer-zh/NOTICE",
                ".cursor/skills/humanizer-zh/SOURCE.md",
                ".cursor/skills/interview/SKILL.md",
                ".cursor/skills/editor/SKILL.md",
                ".cursor/skills/editor/references/x-longform-11.md",
                "AGENTS.md",
            ],
        )
        self.assertIn("ideas/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("facts/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content/references/content-record.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-core/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-core/references/exemplars.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-x/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-x-ops/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-x-article-packaging/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-x-process-topic/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-x-cta-loop/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-visual/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-xhs/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("content-wechat/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("canvas-design/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("canvas-design/LICENSE.txt", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("canvas-design/SOURCE.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("humanizer-zh/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("humanizer-zh/LICENSE", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("humanizer-zh/SOURCE.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("interview/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("editor/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertIn("editor/references/x-longform-11.md", sync.SKILL_RELATIVE_PATHS)
        self.assertNotIn("qu-ai-wei/SKILL.md", sync.SKILL_RELATIVE_PATHS)
        self.assertNotIn(
            ".cursor/skills/facts/SKILL.md",
            sync.commit_paths(Path("/tmp/unused")),
        )

    def test_every_journal_tool_and_reference_is_allowlisted(self) -> None:
        """New files under skills/journal/tools and references must be copied.

        The sync script does not glob the tree. A file that exists in this
        repo but is missing from SKILL_RELATIVE_PATHS never reaches DigitalBrain.
        """
        tools = {
            path.name
            for path in (sync.SKILLS_DIR / "journal" / "tools").glob("*.py")
            if path.is_file()
        }
        references = {
            path.name
            for path in (sync.SKILLS_DIR / "journal" / "references").glob("*.md")
            if path.is_file()
        }
        listed_tools = {
            Path(relative).name
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("journal/tools/")
        }
        listed_references = {
            Path(relative).name
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("journal/references/")
        }
        self.assertEqual(tools, listed_tools)
        self.assertEqual(references, listed_references)
        self.assertIn("capture_thought.py", listed_tools)
        self.assertIn("thought_lib.py", listed_tools)
        self.assertIn("thoughts.md", listed_references)

    def test_every_content_file_is_allowlisted(self) -> None:
        """Files under skills/content must be copied. Sync does not glob."""
        files = {
            str(path.relative_to(sync.SKILLS_DIR))
            for path in (sync.SKILLS_DIR / "content").rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and not path.name.startswith("test_")
        }
        listed = {
            relative
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("content/")
        }
        self.assertEqual(
            files,
            {
                "content/SKILL.md",
                "content/references/content-record.md",
                "content/tools/trace_content.py",
            },
        )
        self.assertEqual(files, listed)

    def test_every_content_core_file_is_allowlisted(self) -> None:
        """Files under skills/content-core must be copied. Sync does not glob."""
        files = {
            str(path.relative_to(sync.SKILLS_DIR))
            for path in (sync.SKILLS_DIR / "content-core").rglob("*")
            if path.is_file()
        }
        listed = {
            relative
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("content-core/")
        }
        self.assertEqual(
            files,
            {
                "content-core/SKILL.md",
                "content-core/references/exemplars.md",
            },
        )
        self.assertEqual(files, listed)

    def test_every_canvas_design_file_is_allowlisted(self) -> None:
        """Files under skills/canvas-design must be copied. Sync does not glob.

        Fonts are not vendored. The three shipped files are the whole tree.
        """
        files = {
            str(path.relative_to(sync.SKILLS_DIR))
            for path in (sync.SKILLS_DIR / "canvas-design").rglob("*")
            if path.is_file()
        }
        listed = {
            relative
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("canvas-design/")
        }
        self.assertEqual(
            files,
            {
                "canvas-design/SKILL.md",
                "canvas-design/LICENSE.txt",
                "canvas-design/SOURCE.md",
            },
        )
        self.assertEqual(files, listed)

    def test_qu_ai_wei_removed_and_replacement_skills_allowlisted(self) -> None:
        """qu-ai-wei is gone. humanizer-zh, interview, and editor are copied whole.

        Sync does not glob. A file under these trees that is missing from
        SKILL_RELATIVE_PATHS never reaches DigitalBrain.
        """
        self.assertFalse((sync.SKILLS_DIR / "qu-ai-wei").exists())
        expected = {
            "humanizer-zh": {
                "humanizer-zh/SKILL.md",
                "humanizer-zh/LICENSE",
                "humanizer-zh/LICENSE-jiji262",
                "humanizer-zh/LICENSE-qu-ai-wei",
                "humanizer-zh/NOTICE",
                "humanizer-zh/SOURCE.md",
            },
            "interview": {"interview/SKILL.md"},
            "editor": {"editor/SKILL.md", "editor/references/x-longform-11.md"},
        }
        for prefix, want in expected.items():
            files = {
                str(path.relative_to(sync.SKILLS_DIR))
                for path in (sync.SKILLS_DIR / prefix).rglob("*")
                if path.is_file()
            }
            listed = {
                relative
                for relative in sync.SKILL_RELATIVE_PATHS
                if relative.startswith(prefix + "/")
            }
            self.assertEqual(files, want)
            self.assertEqual(files, listed)

    def test_allowlist_adds_ideas_and_facts_without_deleting_vault_copies(self) -> None:
        """ideas/SKILL.md is copied; facts/SKILL.md stays allowlisted until its source exists.

        An allowlisted path with no source file is skipped. Copies already in
        the vault, including facts and unlisted sibling files, are not deleted.
        """
        ideas_only = {
            relative
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("ideas/")
        }
        facts_only = {
            relative
            for relative in sync.SKILL_RELATIVE_PATHS
            if relative.startswith("facts/")
        }
        self.assertEqual(ideas_only, {"ideas/SKILL.md"})
        self.assertEqual(facts_only, {"facts/SKILL.md"})
        self.assertTrue((sync.SKILLS_DIR / "ideas" / "SKILL.md").is_file())
        self.assertFalse((sync.SKILLS_DIR / "facts" / "SKILL.md").is_file())
        self.assertIn("ideas/SKILL.md", sync.present_skill_relative_paths())
        self.assertNotIn("facts/SKILL.md", sync.present_skill_relative_paths())

        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "AGENTS.md", LEGACY_AGENTS)
            write(vault / "📝 Journal" / "keep.md", "old line\n")
            facts = vault / ".cursor" / "skills" / "facts" / "SKILL.md"
            facts_extra = vault / ".cursor" / "skills" / "facts" / "references" / "schema.md"
            ideas_extra = vault / ".cursor" / "skills" / "ideas" / "references" / "schema.md"
            sentinel = b"VAULT FACTS SENTINEL\n"
            write(facts, sentinel.decode("utf-8"))
            write(facts_extra, "VAULT FACTS EXTRA\n")
            write(ideas_extra, "VAULT IDEAS EXTRA\n")
            before_facts = _file_snapshot(vault / ".cursor" / "skills" / "facts")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--vault", str(vault), "--print-paths"])
            listed = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn(".cursor/skills/ideas/SKILL.md", listed)
            self.assertNotIn(".cursor/skills/facts/", listed)
            self.assertEqual(facts.read_bytes(), sentinel)
            self.assertEqual(facts_extra.read_text(encoding="utf-8"), "VAULT FACTS EXTRA\n")
            self.assertEqual(ideas_extra.read_text(encoding="utf-8"), "VAULT IDEAS EXTRA\n")
            self.assertEqual(before_facts, _file_snapshot(vault / ".cursor" / "skills" / "facts"))
            ideas = vault / ".cursor" / "skills" / "ideas" / "SKILL.md"
            self.assertEqual(
                ideas.read_bytes(),
                (sync.SKILLS_DIR / "ideas" / "SKILL.md").read_bytes(),
            )

            before = _tree_fingerprint(vault)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("drift clean", out)
            self.assertIn(".cursor/skills/ideas/SKILL.md match", out)
            self.assertNotIn("facts", out)
            self.assertEqual(before, _tree_fingerprint(vault))
            self.assertEqual(facts.read_bytes(), sentinel)

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
    def test_digest_reads_thursday_cycle_snapshot(self) -> None:
        text = (sync.SKILLS_DIR / "digest" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: digest", text)
        self.assertIn("📋 Digests/cycles/", text)
        self.assertIn("cy-", text)
        self.assertIn("周四快照", text)
        self.assertIn("📋 Digests/daily/", text)
        self.assertIn("Jake 接受之前", text)
        self.assertIn("不是 Evidence", text)
        self.assertNotIn("intake.md", text)
        self.assertNotIn("最多两个概念", text)
        self.assertNotIn("Asia/Shanghai", text)
        route = (sync.SKILLS_DIR / "digitalbrain-agents-route.md").read_text(encoding="utf-8")
        self.assertIn("/digest", route)
        self.assertIn("📋 Digests/daily/", route)
        self.assertNotIn("W38 有什么", route)
        self.assertNotIn("week 38", route)
        self.assertIn("相关认知", route)
        self.assertIn(".cursor/skills/cognition/", route)
        self.assertIn("partial / unavailable 不许说成", route)

    def test_managed_route_does_not_authorize_protected_main(self) -> None:
        route = (sync.SKILLS_DIR / "digitalbrain-agents-route.md").read_text(encoding="utf-8")
        lowered = route.lower()
        self.assertNotIn("push origin main", lowered)
        self.assertNotIn("git push origin main", lowered)
        self.assertNotIn("可以直接写 protected main", route)
        self.assertNotIn("可以直接 push protected main", route)
        self.assertNotIn("直接修改 / push protected main", route)
        self.assertNotIn("禁止为 Digest 开 PR", route)
        self.assertIn("当前 Global Governance / project policy", route)
        self.assertIn("会修改已有文件的变更走 task branch 和 PR", route)
        self.assertNotIn("使用 task branch，精确路径暂存", route)
        self.assertIn("精确路径暂存", route)
        self.assertIn("禁止 `git add -A`", route)
        self.assertIn(
            "只新增文件的提交（想法文件、消化清单）可以直接推 main；任何修改或删除都不直推 main，不强推",
            route,
        )
        self.assertNotIn("不直接 push protected `main`", route)
        self.assertIn("PR 与 merge 服从当前授权和治理 gate", route)
        self.assertIn("Journal 仍不自动 push", route)
        self.assertIn("客户说「可以写 / 写吧 / OK 写」之前，不要写 `📝 Journal/`", route)
        self.assertIn("「记一下：」「想法：」或 `/thought`", route)
        self.assertIn("看过未展开", route)
        self.assertIn("capture_thought.py", route)
        self.assertIn("没存上", route)
        self.assertIn("把他的原话原样念回去", route)
        self.assertIn("只新增且路径还不在 origin 上的提交会重放后再推，不强推", route)
        self.assertIn("退出码 5 是工具自己的异常，不是 git 不可用", route)

    def test_journal_waits_for_ok(self) -> None:
        text = (sync.SKILLS_DIR / "journal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("旧周记", text)
        self.assertIn("呼应", text)
        self.assertIn("可以写 / 写吧 / OK 写", text)
        self.assertIn("客户说「可以写 / 写吧 / OK 写」之前，不落盘", text)
        self.assertIn("自己认周", text)
        self.assertIn("不写 `📖 Cognition/`", text)
        self.assertNotIn("W38 有什么", text)

    def test_content_skill_contract(self) -> None:
        stub = (sync.SKILLS_DIR / "content" / "SKILL.md").read_text(encoding="utf-8")
        core = (sync.SKILLS_DIR / "content-core" / "SKILL.md").read_text(encoding="utf-8")
        x_skill = (sync.SKILLS_DIR / "content-x" / "SKILL.md").read_text(encoding="utf-8")
        xhs_skill = (sync.SKILLS_DIR / "content-xhs" / "SKILL.md").read_text(encoding="utf-8")
        wechat_skill = (sync.SKILLS_DIR / "content-wechat" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        record = (sync.SKILLS_DIR / "content" / "references" / "content-record.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: content", stub)
        self.assertIn("已停用", stub)
        self.assertIn("skills/content-core/SKILL.md", stub)
        self.assertIn("skills/content-x/SKILL.md", stub)
        self.assertIn("skills/content-xhs/SKILL.md", stub)
        self.assertIn("skills/content-wechat/SKILL.md", stub)
        self.assertNotIn("1. 发现选题", stub)
        self.assertNotIn("一条帖子出三版", stub)
        self.assertNotIn("周记里已经写清的句子直接引用", stub)
        for step in (
            "1. 发现选题",
            "2. 确定选题",
            "3. 内容策划",
            "4. 内容生产",
            "5. 审核发布",
            "6. 反馈复盘",
        ):
            self.assertIn(step, core)
        self.assertIn("三层过滤", core)
        self.assertIn("自检清单", core)
        self.assertIn("发布授权绑定版本", core)
        self.assertIn("body_sha256", core)
        self.assertIn("不代发", core)
        self.assertIn("private-jake", core)
        self.assertIn("public-ok", core)
        self.assertIn("约 3000", core)
        self.assertIn("周日 20:00", core)
        self.assertIn("周一 10:00", core)
        self.assertIn("小红书", core)
        self.assertIn("公众号", core)
        self.assertIn("批 / 改 / 不要", core)
        self.assertIn("家人、钱和持仓、健康、工作客户、具体人名", core)
        self.assertIn("内容/草稿/{年-W周}/", core)
        self.assertIn("连续 20 个字符", core)
        self.assertIn("Grok Bot", core)
        self.assertIn("配图/示意", core)
        self.assertIn("「周记里已经写清的句子直接引用」已废止", core)
        sensitive = "家人、钱和持仓、健康、工作客户、具体人名"
        for platform, body in (
            ("content-x", x_skill),
            ("content-xhs", xhs_skill),
            ("content-wechat", wechat_skill),
        ):
            self.assertIn("必须先加载", body, platform)
            self.assertIn("skills/content-core/SKILL.md", body, platform)
            self.assertNotIn(sensitive, body, platform)
            self.assertNotIn("一条帖子出三版", body, platform)
        self.assertIn("约 3000", x_skill)
        self.assertIn("1–3", x_skill)
        self.assertIn("短帖可以没有配图", x_skill)
        self.assertIn("不要求小红书式多图卡片", x_skill)
        self.assertIn("X Article", x_skill)
        self.assertIn("X 长文", x_skill)
        self.assertIn("X 短帖", x_skill)
        self.assertIn(
            "禁止在这一轮、这一写作上下文里 Skill load `content-xhs` 或 `content-wechat`",
            x_skill,
        )
        self.assertNotIn("Creator Academy 写法稍后追加", x_skill)
        self.assertIn("标题：具体 + 勾好奇 + 承诺价值", x_skill)
        self.assertIn("首句钩住读者", x_skill)
        self.assertIn("一段最多 2–4 行", x_skill)
        self.assertIn("每 3–5 段一个小标题", x_skill)
        self.assertIn("叙事用「我」", x_skill)
        self.assertIn("每个论点后面马上跟证据", x_skill)
        self.assertIn("可嵌本人已发帖当证据", x_skill)
        self.assertIn("用可核验文件/数据做分析", x_skill)
        self.assertIn("论证靠段落推进", x_skill)
        self.assertIn("加粗只加证据句", x_skill)
        self.assertIn("结尾给 takeaway + 一两句收束", x_skill)
        self.assertIn("去填充、大声读", x_skill)
        self.assertIn("不定死砍 20–30%", x_skill)
        self.assertIn("结尾提问求回复", x_skill)
        self.assertIn("结尾求转发/分享", x_skill)
        self.assertIn("标题百分比式钩子", x_skill)
        self.assertIn("本轮只要 X：只交 X", x_skill)
        self.assertIn("读者会问的问题、话题或真实自白", x_skill)
        self.assertIn("论证和收尾可以直接对读者说「你」", x_skill)
        self.assertIn("优先用列表或编号", x_skill)
        self.assertIn("你现在就可以试", x_skill)
        self.assertIn("BREAKDOWN", x_skill)
        self.assertIn("01-articles-guide", x_skill)
        self.assertNotIn("全文最多一处", x_skill)
        self.assertNotIn("小标题是判断句", x_skill)
        self.assertIn("论证骨架三栏", core)
        self.assertIn("证据或读者疑问空着，这张卡不能交", core)
        self.assertIn("论证图", core)
        self.assertIn("小标题朗读测", core)
        self.assertIn("模型写的方向卡分论点、小标题和其他卡面句，他回过「行」也不豁免", core)
        self.assertIn("skills/content-core/references/exemplars.md", core)
        self.assertIn("同一终稿 sha", core)
        self.assertIn("你现在就可以试", core)
        self.assertNotIn("小标题是判断句", core)
        ops = (sync.SKILLS_DIR / "content-x-ops" / "SKILL.md").read_text(encoding="utf-8")
        visual = (sync.SKILLS_DIR / "content-visual" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("发前预告", ops)
        self.assertIn("新文置顶 24–72 小时", ops)
        self.assertIn("回链全文", ops)
        self.assertIn("早回复首波读者", ops)
        self.assertIn("Exclusive Threads", ops)
        self.assertIn("## OCR 资格与禁止求互动", ops)
        self.assertIn("待 Jake 定", ops)
        self.assertIn("## X 长文引用再分发", ops)
        self.assertIn("## 沉睡账号 Article 复活（约 7–30 天）", ops)
        self.assertIn("账号非沉睡时，暂不作首期例行复活计划", ops)
        self.assertIn("不代发小红书", ops)
        self.assertIn("不实现自动发帖", ops)
        packaging = (sync.SKILLS_DIR / "content-x-article-packaging" / "SKILL.md").read_text(encoding="utf-8")
        topic = (sync.SKILLS_DIR / "content-x-process-topic" / "SKILL.md").read_text(encoding="utf-8")
        cta = (sync.SKILLS_DIR / "content-x-cta-loop" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("外人一眼能说清三者各解决什么", packaging)
        self.assertIn("封面只有 brief、无本岗出图", packaging)
        self.assertIn("能复述「你怎么想／怎么做」", topic)
        self.assertIn("不另起与 Ideas 组合流平行的第二套选题台账", topic)
        self.assertIn("读完有明确动作", cta)
        self.assertIn("无去向且无「待对齐」标注 → 不合格", cta)
        for body in (packaging, topic, cta):
            self.assertNotIn("/workspace", body)
        self.assertIn("五层 prompt", visual)
        self.assertIn("## 10. X Article 包装三件套 · 封面", visual)
        self.assertIn("卖梦想", visual)
        self.assertIn("拆异议", visual)
        self.assertIn("Think Harder", visual)
        self.assertIn("先重跑，再一次只改一处", visual)
        self.assertIn("参考图锁风格", visual)
        self.assertIn("只写动作", visual)
        self.assertIn("16:9，再裁成 5:2", visual)
        self.assertIn("预留标题叠字安全区", visual)
        self.assertIn("短视频可以进 X 长文", visual)
        self.assertIn("默认无人像", visual)
        self.assertIn("不用现成风格模板", visual)
        self.assertIn(
            "禁止在这一轮、这一写作上下文里 Skill load `content-xhs` 或 `content-wechat`",
            core,
        )
        self.assertIn("一次交齐三版只在两种任务里适用", core)
        self.assertIn("只要写 X、X Article、X 长文或 X 短帖", core)
        self.assertNotIn("然后加载三个平台技能，一次交齐三版。", core)
        self.assertIn(
            "禁止同一写作上下文 Skill load content-xhs 或 content-wechat",
            stub,
        )
        x_only_note = "只写 X、X Article、X 长文或 X 短帖的那一轮不加载本技能。"
        self.assertIn(x_only_note, xhs_skill)
        self.assertIn(x_only_note, wechat_skill)
        self.assertIn("不要为了填这两栏去 Skill load", record)
        self.assertIn("纸纹底", xhs_skill)
        self.assertIn("同一条逻辑链", xhs_skill)
        self.assertIn("title", wechat_skill)
        self.assertIn("sources_note", wechat_skill)
        self.assertIn("不另加他没确认的观点", wechat_skill)
        for doc in (stub, core, x_skill, xhs_skill, wechat_skill):
            self.assertNotIn("每日 digest", doc)
            self.assertNotIn("我的看法", doc)
            self.assertNotIn("thesis", doc.lower())
            self.assertNotIn("digest.md", doc)
        self.assertIn("content-0.1", record)
        self.assertIn("content_id", record)
        self.assertIn("body_sha256", record)
        self.assertIn("audience_problem", record)
        self.assertIn("source_refs", record)
        self.assertIn("wechat_mp", record)
        self.assertIn("发布包", record)
        self.assertIn("fdb72bfb9f4bd951a2680766aa646d7c1b30c18cec519efda4347804171d996c", record)
        self.assertIn("skills/content-core/SKILL.md", record)
        drive_home = "Google Drive「内容/草稿/{周}/」"
        local_disk = "不把发布包写到这台机器的本地磁盘"
        images = "实际的卡片图和封面图"
        image_rebind = "换图也要把 revision 加一"
        self.assertIn("内容/草稿/{年-W周}/", core)
        self.assertIn(local_disk, core)
        self.assertIn(images, core)
        self.assertIn(image_rebind, core)
        self.assertIn(drive_home, record)
        self.assertIn(local_disk, record)
        self.assertIn(images, record)
        self.assertIn(image_rebind, record)
        for doc in (core, record):
            self.assertNotIn("发布包停在对话里", doc)
            self.assertNotIn("发布包留在对话里", doc)
            self.assertNotIn("还停在对话里", doc)
            self.assertNotIn("本包只写文案和配图说明", doc)
        self.assertNotIn("每日 digest", record)
        self.assertNotIn("我的看法", record)
        self.assertNotIn("thesis", record.lower())
        self.assertNotIn("年-W周", record)


def _tree_fingerprint(root: Path) -> dict[str, str]:
    """Map relative path -> sha256 of file bytes for the whole tree."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(root))
            out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _seed_synced_vault(vault: Path) -> None:
    prefix = "# OUTSIDE BLOCK PREFIX\n\n"
    suffix = "\n\n## OUTSIDE BLOCK SUFFIX\nOUTSIDE BLOCK\n"
    write(vault / "AGENTS.md", prefix + sync.load_route_snippet() + suffix)
    write(vault / "📝 Journal" / "keep.md", "OUTSIDE BLOCK journal placeholder\n")
    for relative in sync.present_skill_relative_paths():
        src = sync.SKILLS_DIR / relative
        dest = vault / ".cursor" / "skills" / relative
        write(dest, src.read_text(encoding="utf-8"))


def _skills_tree_without_intake(dest: Path) -> None:
    """Copy this repo's skills tree except ``intake/``, as the Journal pack does."""
    for path in sync.SKILLS_DIR.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(sync.SKILLS_DIR)
        if relative.parts[0] == "intake":
            continue
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())


def _file_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = path.read_bytes()
    return out


class DriftCheckTests(unittest.TestCase):
    def test_clean_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("drift clean", out)
            self.assertIn("agents_block match", out)
            for relative in sync.SKILL_RELATIVE_PATHS:
                reported = f".cursor/skills/{relative}"
                if (sync.SKILLS_DIR / relative).is_file():
                    self.assertIn(f"{reported} match", out)
                else:
                    self.assertNotIn(reported, out)
            self.assertIn(".cursor/skills/ideas/SKILL.md match", out)
            self.assertNotIn(".cursor/skills/facts/SKILL.md", out)

    def test_stale_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            stale = vault / ".cursor" / "skills" / "intake" / "SKILL.md"
            stale.write_text("STALE PLACEHOLDER BYTES\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--drift", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            out = buf.getvalue()
            self.assertIn(".cursor/skills/intake/SKILL.md mismatch", out)
            self.assertIn("drift found", out)
            self.assertNotIn("STALE PLACEHOLDER", out)

    def test_missing_copy(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            (vault / ".cursor" / "skills" / "journal" / "SKILL.md").unlink()
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            out = buf.getvalue()
            self.assertIn(".cursor/skills/journal/SKILL.md missing", out)
            self.assertIn("drift found", out)

    def test_agents_block_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            agents = vault / "AGENTS.md"
            text = agents.read_text(encoding="utf-8")
            start = text.index(sync.MARK_START)
            end = text.index(sync.MARK_END) + len(sync.MARK_END)
            mutated = (
                text[:start]
                + sync.MARK_START
                + "\n## STALE ROUTE PLACEHOLDER\n"
                + sync.MARK_END
                + text[end:]
            )
            agents.write_text(mutated, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            out = buf.getvalue()
            self.assertIn("agents_block mismatch", out)
            self.assertNotIn("agents_block missing", out)
            self.assertNotIn("STALE ROUTE PLACEHOLDER", out)
            self.assertNotIn("OUTSIDE BLOCK", out)

    def test_absent_agents_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            (vault / "AGENTS.md").unlink()
            before = _tree_fingerprint(vault)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            out = buf.getvalue()
            self.assertIn("agents_block missing", out)
            self.assertNotIn("agents_block mismatch", out)
            self.assertIn("dst=-", out)
            self.assertEqual(before, _tree_fingerprint(vault))
            self.assertFalse((vault / "AGENTS.md").exists())

    def test_agents_without_marked_block_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            agents = vault / "AGENTS.md"
            agents.write_text(
                "# OUTSIDE BLOCK PREFIX\n\nNo managed route block here.\n",
                encoding="utf-8",
            )
            before = _tree_fingerprint(vault)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            out = buf.getvalue()
            self.assertIn("agents_block missing", out)
            self.assertNotIn("agents_block mismatch", out)
            self.assertNotIn("OUTSIDE BLOCK", out)
            self.assertEqual(before, _tree_fingerprint(vault))
            self.assertNotIn(sync.MARK_START, agents.read_text(encoding="utf-8"))

    def test_outside_agents_content_preserved_by_drift_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            agents = vault / "AGENTS.md"
            before = agents.read_text(encoding="utf-8")
            start = before.index(sync.MARK_START)
            end = before.index(sync.MARK_END) + len(sync.MARK_END)
            prefix_before = before[:start]
            suffix_before = before[end:]
            buf = io.StringIO()
            with redirect_stdout(buf):
                sync.main(["--check", "--vault", str(vault)])
            after = agents.read_text(encoding="utf-8")
            self.assertEqual(after[: after.index(sync.MARK_START)], prefix_before)
            self.assertEqual(
                after[after.index(sync.MARK_END) + len(sync.MARK_END) :],
                suffix_before,
            )
            self.assertEqual(before, after)

    def test_patch_agents_preserves_outside_markers(self) -> None:
        prefix = "# OUTSIDE BLOCK PREFIX\n\n"
        suffix = "\n\n## OUTSIDE BLOCK SUFFIX\nOUTSIDE BLOCK\n"
        current = prefix + sync.load_route_snippet() + suffix
        patched = sync.patch_agents(current, sync.load_route_snippet())
        start = patched.index(sync.MARK_START)
        end = patched.index(sync.MARK_END) + len(sync.MARK_END)
        self.assertEqual(patched[:start], prefix)
        self.assertIn("## OUTSIDE BLOCK SUFFIX", patched[end:])
        self.assertIn("OUTSIDE BLOCK", patched[end:])
        self.assertEqual(patched.count(sync.MARK_START), 1)
        self.assertEqual(patched.count(sync.MARK_END), 1)

    def test_drift_mode_zero_writes_on_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            _seed_synced_vault(vault)
            (vault / ".cursor" / "skills" / "intake" / "SKILL.md").write_text(
                "STALE PLACEHOLDER BYTES\n", encoding="utf-8"
            )
            agents = vault / "AGENTS.md"
            text = agents.read_text(encoding="utf-8")
            start = text.index(sync.MARK_START)
            end = text.index(sync.MARK_END) + len(sync.MARK_END)
            agents.write_text(
                text[:start]
                + sync.MARK_START
                + "\n## STALE ROUTE PLACEHOLDER\n"
                + sync.MARK_END
                + text[end:],
                encoding="utf-8",
            )
            before = _tree_fingerprint(vault)
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = sync.main(["--check", "--vault", str(vault)])
            self.assertEqual(rc, 1)
            after = _tree_fingerprint(vault)
            self.assertEqual(before, after)


class PackWithoutIntakeTests(unittest.TestCase):
    """Journal pack source has journal + cognition and no intake skill."""

    def _vault_with_existing_intake(self, root: Path) -> tuple[Path, Path, bytes]:
        vault = root / "vault"
        write(vault / "AGENTS.md", LEGACY_AGENTS)
        write(vault / "📝 Journal" / "keep.md", "old line\n")
        intake = vault / ".cursor" / "skills" / "intake" / "SKILL.md"
        extra = vault / ".cursor" / "skills" / "intake" / "references" / "note.md"
        sentinel = b"VAULT INTAKE SENTINEL\n"
        write(intake, sentinel.decode("utf-8"))
        write(extra, "VAULT INTAKE EXTRA\n")
        return vault, intake, sentinel

    def test_sync_succeeds_and_keeps_existing_vault_intake(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills = root / "skills"
            _skills_tree_without_intake(skills)
            self.assertFalse((skills / "intake").exists())
            vault, intake, sentinel = self._vault_with_existing_intake(root)
            extra = vault / ".cursor" / "skills" / "intake" / "references" / "note.md"
            before_intake = _file_snapshot(vault / ".cursor" / "skills" / "intake")
            with patch.object(sync, "SKILLS_DIR", skills):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = sync.main(["--vault", str(vault), "--print-paths"])
                listed = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertNotIn(".cursor/skills/intake/", listed)
            self.assertIn(".cursor/skills/journal/SKILL.md", listed)
            self.assertIn(".cursor/skills/journal/tools/write_journal.py", listed)
            self.assertIn(".cursor/skills/cognition/SKILL.md", listed)
            self.assertEqual(intake.read_bytes(), sentinel)
            self.assertEqual(extra.read_text(encoding="utf-8"), "VAULT INTAKE EXTRA\n")
            self.assertEqual(before_intake, _file_snapshot(vault / ".cursor" / "skills" / "intake"))
            journal = vault / ".cursor" / "skills" / "journal" / "SKILL.md"
            self.assertEqual(journal.read_bytes(), (skills / "journal" / "SKILL.md").read_bytes())
            self.assertTrue((vault / ".cursor" / "skills" / "cognition" / "tools" / "write_cognition.py").is_file())
            self.assertEqual((vault / "📝 Journal" / "keep.md").read_text(encoding="utf-8"), "old line\n")

    def test_check_ignores_vault_intake_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            skills = root / "skills"
            _skills_tree_without_intake(skills)
            vault = root / "vault"
            write(vault / "📝 Journal" / "keep.md", "old line\n")
            with patch.object(sync, "SKILLS_DIR", skills):
                prefix = "# OUTSIDE BLOCK PREFIX\n\n"
                suffix = "\n\n## OUTSIDE BLOCK SUFFIX\nOUTSIDE BLOCK\n"
                write(vault / "AGENTS.md", prefix + sync.load_route_snippet() + suffix)
                for relative in sync.present_skill_relative_paths():
                    src = skills / relative
                    write(
                        vault / ".cursor" / "skills" / relative,
                        src.read_text(encoding="utf-8"),
                    )
                intake = vault / ".cursor" / "skills" / "intake" / "SKILL.md"
                write(intake, "VAULT INTAKE SENTINEL\n")
                present = sync.present_skill_relative_paths()
                self.assertTrue(present)
                self.assertFalse(any(relative.startswith("intake/") for relative in present))
                before = _tree_fingerprint(vault)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = sync.main(["--check", "--vault", str(vault)])
                out = buf.getvalue()
                self.assertEqual(rc, 0)
                self.assertIn("drift clean", out)
                self.assertIn(".cursor/skills/journal/SKILL.md match", out)
                self.assertIn(".cursor/skills/cognition/SKILL.md match", out)
                self.assertNotIn("intake", out)
                self.assertEqual(before, _tree_fingerprint(vault))
                self.assertEqual(intake.read_text(encoding="utf-8"), "VAULT INTAKE SENTINEL\n")

                journal = vault / ".cursor" / "skills" / "journal" / "SKILL.md"
                journal.unlink()
                intake_before = intake.read_bytes()
                tree_without_journal = _tree_fingerprint(vault)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = sync.main(["--drift", "--vault", str(vault)])
                out = buf.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn(".cursor/skills/journal/SKILL.md missing", out)
            self.assertIn("drift found", out)
            self.assertNotIn("intake", out)
            self.assertEqual(intake.read_bytes(), intake_before)
            self.assertEqual(tree_without_journal, _tree_fingerprint(vault))
            self.assertFalse(journal.exists())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
