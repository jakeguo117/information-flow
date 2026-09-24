#!/usr/bin/env python3
"""Temp-vault tests for DigitalBrain skill sync. No live vault."""

from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout
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
            self.assertEqual(
                (vault / ".cursor" / "skills" / "cognition" / "SKILL.md").read_text(encoding="utf-8"),
                (sync.SKILLS_DIR / "cognition" / "SKILL.md").read_text(encoding="utf-8"),
            )
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
                ".cursor/skills/journal/SKILL.md",
                ".cursor/skills/journal/references/setup.md",
                ".cursor/skills/journal/references/weekly-brief.md",
                ".cursor/skills/cognition/SKILL.md",
                ".cursor/skills/cognition/references/schema.md",
                ".cursor/skills/cognition/references/retrieval.md",
                ".cursor/skills/cognition/references/layout.md",
                ".cursor/skills/cognition/tools/cognition_lib.py",
                ".cursor/skills/cognition/tools/validate_cognition.py",
                ".cursor/skills/cognition/tools/retrieve_cognition.py",
                ".cursor/skills/cognition/tools/write_cognition.py",
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
        self.assertIn("不是 Evidence", text)
        route = (sync.SKILLS_DIR / "digitalbrain-agents-route.md").read_text(encoding="utf-8")
        self.assertIn("自己认周", route)
        self.assertNotIn("W38 有什么", route)
        self.assertNotIn("week 38", route)
        self.assertIn("相关认知", route)
        self.assertIn(".cursor/skills/cognition/", route)
        self.assertIn("partial / unavailable 不许说成", route)

    def test_journal_waits_for_ok(self) -> None:
        text = (sync.SKILLS_DIR / "journal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("旧周记", text)
        self.assertIn("呼应", text)
        self.assertIn("可以写 / 写吧 / OK 写", text)
        self.assertIn("客户说「可以写 / 写吧 / OK 写」之前，不落盘", text)
        self.assertIn("自己认周", text)
        self.assertIn("不写 `📖 Cognition/`", text)
        self.assertNotIn("W38 有什么", text)


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
    for relative in sync.SKILL_RELATIVE_PATHS:
        src = sync.SKILLS_DIR / relative
        dest = vault / ".cursor" / "skills" / relative
        write(dest, src.read_text(encoding="utf-8"))


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
                self.assertIn(f".cursor/skills/{relative} match", out)

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
            self.assertNotIn("STALE ROUTE PLACEHOLDER", out)
            self.assertNotIn("OUTSIDE BLOCK", out)

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


if __name__ == "__main__":
    raise SystemExit(unittest.main())
