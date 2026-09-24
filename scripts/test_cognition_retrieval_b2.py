#!/usr/bin/env python3
"""Batch 3B-B2 Cognition retrieval contract tests. Synthetic vaults only."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "skills" / "cognition" / "tools"
FIXTURES = ROOT / "tests" / "fixtures" / "cognition" / "objects"
sys.path.insert(0, str(TOOLS))

import cognition_lib as lib  # noqa: E402

COG = "📖 Cognition"

# Synthetic journal-looking prose — must never appear in retrieval output.
PRIVATE_JOURNAL_MARKER = (
    "PRIVATE_JOURNAL_DIARY: today I argued with myself about lunch and felt lonely."
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def replace_field(text: str, key: str, value: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            lines.append(f"{key}: {value}")
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def seed_core(vault: Path) -> None:
    write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", fixture("evidence-widget-lag.md"))
    write(
        vault / COG / "Evidence" / "evidence-20260920-widget-no-lag.md",
        fixture("evidence-widget-no-lag.md"),
    )
    write(
        vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md",
        fixture("belief-widgets-need-retrieval.md"),
    )
    write(
        vault / COG / "Principles" / "principle-20260920-retrieve-before-widget.md",
        fixture("principle-retrieve-before-widget.md"),
    )


def dump_blob(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


class RetrievalContractB2Tests(unittest.TestCase):
    def test_found(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            data = lib.retrieve(vault, query="synthetic widget decision")
            self.assertEqual(data["status"], "found")
            self.assertIn("principle-20260920-retrieve-before-widget", data["matched_ids"])
            self.assertTrue(data["principles"] or data["beliefs"] or data["evidence"])

    def test_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            data = lib.retrieve(vault, query="quantum pineapple pastry")
            self.assertEqual(data["status"], "no_match")
            self.assertEqual(data["matched_ids"], [])
            self.assertEqual(data["principles"], [])
            self.assertEqual(data["beliefs"], [])
            self.assertEqual(data["evidence"], [])

    def test_partial_malformed_relevant(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            write(
                vault / COG / "Beliefs" / "belief-20260920-widget-malformed.md",
                fixture("malformed-widget.md"),
            )
            data = lib.retrieve(vault, query="synthetic widget")
            self.assertEqual(data["status"], "partial")
            self.assertNotEqual(data["status"], "no_match")
            self.assertTrue(data["skipped"])

    def test_unavailable_missing_store(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            data = lib.retrieve(vault, query="synthetic widget")
            self.assertEqual(data["status"], "unavailable")
            self.assertNotEqual(data["status"], "no_match")

    def test_unavailable_missing_vault_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "does-not-exist"
            data = lib.retrieve(vault, query="synthetic widget")
            self.assertEqual(data["status"], "unavailable")
            self.assertNotEqual(data["status"], "no_match")

    def test_contradiction_visible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            data = lib.retrieve(vault, query="synthetic widget", evidence_budget=5)
            evidence_ids = [item["id"] for item in data["evidence"]]
            self.assertIn("evidence-20260920-widget-no-lag", evidence_ids)
            belief = next(
                item
                for item in data["beliefs"]
                if item["id"] == "belief-20260920-widgets-need-retrieval"
            )
            self.assertIn(
                "evidence-20260920-widget-no-lag",
                belief["contradicting_evidence"],
            )

    def test_stale_dependency_visible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = replace_field(
                fixture("belief-widgets-need-retrieval.md"), "status", "retired"
            )
            write(
                vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md",
                text,
            )
            data = lib.retrieve(vault, query="synthetic widget decision")
            self.assertIn(
                "principle-20260920-retrieve-before-widget",
                data["stale_dependencies"],
            )
            principles = [
                item
                for item in data["principles"]
                if item["id"] == "principle-20260920-retrieve-before-widget"
            ]
            self.assertTrue(principles)
            self.assertTrue(principles[0]["stale_dependency"])
            self.assertIn(data["status"], {"found", "partial"})

    def test_provenance_fields_present(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            data = lib.retrieve(vault, query="synthetic widget lag")
            self.assertEqual(data["status"], "found")
            evidence = [
                item
                for item in data["evidence"]
                if item["id"] == "evidence-20260920-widget-lag"
            ]
            self.assertTrue(evidence)
            hit = evidence[0]
            for key in ("id", "path", "status", "source"):
                self.assertIn(key, hit)
            self.assertEqual(hit["id"], "evidence-20260920-widget-lag")
            self.assertEqual(hit["status"], "active")
            self.assertEqual(hit["source"], "[[source-synthetic-interviews]]")
            self.assertTrue(hit["path"])
            # Belief/Principle payloads still expose the provenance keys
            belief = data["beliefs"][0]
            for key in ("id", "path", "status", "source"):
                self.assertIn(key, belief)

    def test_failure_not_absence_unreadable_file(self) -> None:
        """Read error must be partial/unavailable — never no_match."""
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            # Unreadable file whose name/tokens will NOT match the query
            locked = vault / COG / "Evidence" / "evidence-20260920-zzz-locked.md"
            write(locked, "not even valid frontmatter\n")
            os.chmod(locked, 0)
            try:
                data = lib.retrieve(vault, query="quantum pineapple pastry")
                self.assertNotEqual(
                    data["status"],
                    "no_match",
                    "read failure must not collapse into no_match",
                )
                self.assertIn(data["status"], {"partial", "unavailable"})
                self.assertTrue(
                    data["skipped"] or data["status"] == "unavailable",
                    data,
                )
            finally:
                os.chmod(locked, stat.S_IRUSR | stat.S_IWUSR)

    def test_budget_truncation_never_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            extras = []
            for i in range(1, 7):
                eid = f"evidence-20260920-widget-extra-{i}"
                text = lib.render_markdown(
                    {
                        "schema_version": "1.1",
                        "id": eid,
                        "type": "evidence",
                        "status": "active",
                        "domains": ["synthetic-widgets"],
                        "related_projects": ["[[Synthetic Widget Project]]"],
                        "created": "2026-09-20",
                        "updated": "2026-09-20",
                        "origin_type": "external_source",
                        "origin_summary": f"synthetic extra {i}",
                        "claim": f"Synthetic supporting detail {i} about widget capture.",
                        "source": f"[[source-synthetic-extra-{i}]]",
                        "source_type": "interview",
                        "validation": "unverified",
                        "reliability": "low",
                        "scope": "unknown",
                        "limitations": "not established",
                    },
                    f"# {eid}\n\nSynthetic.\n\n## Validation History\n- 2026-09-20: created\n",
                )
                write(vault / COG / "Evidence" / f"{eid}.md", text)
                extras.append(eid)
            belief = fixture("belief-widgets-need-retrieval.md").replace(
                "supporting_evidence:\n  - evidence-20260920-widget-lag",
                "supporting_evidence:\n  - evidence-20260920-widget-lag\n"
                + "\n".join(f"  - {eid}" for eid in extras),
            )
            write(
                vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md",
                belief,
            )
            data = lib.retrieve(vault, query="synthetic widget", evidence_budget=5)
            self.assertNotEqual(data["status"], "no_match")
            self.assertIn(data["status"], {"found", "partial"})
            self.assertTrue(data["dropped_supporting_evidence"])

    def test_privacy_safe_output_no_journal_body(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Evidence" / "evidence-20260920-widget-lag.md"
            original = path.read_text(encoding="utf-8")
            # Inject journal-looking prose into the note body only
            body_injected = original.replace(
                "Synthetic observation for tests. Not Jake's private cognition.",
                PRIVATE_JOURNAL_MARKER,
            )
            write(path, body_injected)
            data = lib.retrieve(vault, query="synthetic widget lag")
            blob = dump_blob(data)
            self.assertNotIn(PRIVATE_JOURNAL_MARKER, blob)
            # No unbounded body / raw fields on hits
            for bucket in ("principles", "beliefs", "evidence", "historical"):
                for item in data[bucket]:
                    self.assertNotIn("body", item)
                    self.assertNotIn("raw", item)
                    self.assertNotIn("source_journals", item)
            # Summaries stay bounded (claim/statement, not full notes)
            for item in data["evidence"]:
                self.assertLessEqual(len(item.get("summary") or ""), 500)


if __name__ == "__main__":
    unittest.main()
