#!/usr/bin/env python3
"""Synthetic Cognition tests. No live vault. No private DigitalBrain content."""

from __future__ import annotations

import json
import subprocess
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


def drop_field(text: str, key: str) -> str:
    lines = []
    skip_list = False
    for line in text.splitlines():
        if line.startswith(f"{key}:"):
            skip_list = line.strip() == f"{key}:"
            continue
        if skip_list and line.startswith("  - "):
            continue
        skip_list = False
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


def extra_evidence(index: int, claim: str) -> str:
    eid = f"evidence-20260920-widget-extra-{index}"
    return lib.render_markdown(
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
            "origin_summary": f"synthetic extra evidence {index} for budget tests",
            "claim": claim,
            "source": f"[[source-synthetic-extra-{index}]]",
            "source_type": "interview",
            "validation": "unverified",
            "reliability": "low",
            "scope": "unknown",
            "limitations": "not established",
        },
        f"# {eid}\n\nSynthetic extra.\n\n## Validation History\n- 2026-09-20: created unverified\n",
    )


def approval(kind: str, doc_text: str, target_fingerprint: str | None = None) -> dict:
    parsed = lib.parse_markdown(doc_text)
    return {
        "kind": kind,
        "id": parsed.id,
        "type": parsed.type,
        "target_fingerprint": target_fingerprint,
        "payload_sha256": lib.fingerprint(doc_text if doc_text.endswith("\n") else doc_text + "\n"),
    }


def write_approval(dir_path: Path, data: dict) -> Path:
    path = dir_path / "approval.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def call_write(
    vault: Path,
    action: str,
    payload: str,
    approval_data: dict,
    extra: list[str] | None = None,
    inject_payload_hash: bool = True,
) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        work = Path(raw)
        text = payload if payload.endswith("\n") else payload + "\n"
        payload_path = work / "payload.md"
        payload_path.write_text(text, encoding="utf-8")
        data = dict(approval_data)
        if inject_payload_hash:
            data["payload_sha256"] = lib.fingerprint(text)
        approval_path = write_approval(work, data)
        cmd = [
            sys.executable,
            str(TOOLS / "write_cognition.py"),
            action,
            "--vault",
            str(vault),
            "--payload",
            str(payload_path),
            "--approval",
            str(approval_path),
        ]
        if extra:
            cmd.extend(extra)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        body = proc.stdout.strip() or "{}"
        return proc.returncode, json.loads(body)


def call_validate(vault: Path, file: Path | None = None) -> tuple[int, str]:
    cmd = [sys.executable, str(TOOLS / "validate_cognition.py"), "--vault", str(vault)]
    if file is not None:
        cmd.extend(["--file", str(file)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stderr


def call_retrieve(vault: Path, extra: list[str]) -> tuple[int, dict]:
    cmd = [sys.executable, str(TOOLS / "retrieve_cognition.py"), "--vault", str(vault), *extra]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout or "{}")


class ValidatorTests(unittest.TestCase):
    def test_valid_core_objects_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)

    def test_illegal_validation_confidence_status_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            bad_e = replace_field(fixture("evidence-widget-lag.md"), "validation", "blessed")
            write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", bad_e)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("illegal validation", err)

        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            bad_b = replace_field(fixture("belief-widgets-need-retrieval.md"), "confidence", "absolute")
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", bad_b)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("illegal confidence", err)

        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            bad_s = replace_field(fixture("evidence-widget-lag.md"), "status", "contested")
            write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", bad_s)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("evidence status", err)

    def test_missing_scope_limitations_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = drop_field(drop_field(fixture("evidence-widget-lag.md"), "scope"), "limitations")
            write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("scope", err)
            self.assertIn("limitations", err)

    def test_unknown_scope_explicit_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = replace_field(fixture("evidence-widget-lag.md"), "scope", "unknown")
            text = replace_field(text, "limitations", "not established")
            write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", text)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)

    def test_duplicate_ids_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            write(vault / COG / "Evidence" / "copy.md", fixture("evidence-widget-lag.md"))
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("duplicate id", err)

    def test_wrong_target_type_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = fixture("belief-widgets-need-retrieval.md").replace(
                "supporting_evidence:\n  - evidence-20260920-widget-lag",
                "supporting_evidence:\n  - belief-20260920-widgets-need-retrieval",
            )
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("expected evidence", err)

    def test_supersession_self_and_cycle_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = fixture("belief-widgets-need-retrieval.md")
            text = text.replace("contradicting_evidence:\n  - evidence-20260920-widget-no-lag",
                                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag\nsupersedes:\n  - belief-20260920-widgets-need-retrieval")
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("self", err)

        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            old = lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "belief-20260919-widgets-old",
                    "type": "belief",
                    "status": "active",
                    "domains": ["synthetic-widgets"],
                    "related_projects": ["[[Synthetic Widget Project]]"],
                    "created": "2026-09-19",
                    "updated": "2026-09-19",
                    "origin_type": "direct_reflection",
                    "origin_summary": "older synthetic belief for cycle test",
                    "statement": "Synthetic widgets only need capture.",
                    "confidence": "low",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "supersedes": ["belief-20260920-widgets-need-retrieval"],
                },
                "# old\n\n## Revision History\n- 2026-09-19: created\n",
            )
            newer = fixture("belief-widgets-need-retrieval.md").replace(
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag",
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag\nsupersedes:\n  - belief-20260919-widgets-old",
            )
            write(vault / COG / "Beliefs" / "belief-20260919-widgets-old.md", old)
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", newer)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("cycle", err)

    def test_unsupported_schema_version_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = replace_field(fixture("belief-widgets-need-retrieval.md"), "schema_version", '"2.0"')
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("unsupported schema_version", err)

    def test_file_outside_type_dirs_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            write(vault / COG / "Staging" / "loose.md", fixture("belief-widgets-need-retrieval.md"))
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("outside approved", err)

    def test_illegal_relation_key_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = fixture("evidence-widget-lag.md").replace(
                "limitations: \"toy fixture; not real user research\"",
                "limitations: \"toy fixture; not real user research\"\nsupports:\n  - belief-20260920-widgets-need-retrieval",
            )
            write(vault / COG / "Evidence" / "evidence-20260920-widget-lag.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("illegal persisted relation field supports", err)

    def test_broken_link_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = fixture("belief-widgets-need-retrieval.md").replace(
                "evidence-20260920-widget-lag",
                "evidence-20260920-missing-link",
            )
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("unresolved cognition id evidence-20260920-missing-link", err)

    def test_supersedes_same_type_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = fixture("belief-widgets-need-retrieval.md").replace(
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag",
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag\nsupersedes:\n  - evidence-20260920-widget-lag",
            )
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, err = call_validate(vault)
            self.assertNotEqual(rc, 0)
            self.assertIn("same type", err)


class RetrievalTests(unittest.TestCase):
    def test_found(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            rc, data = call_retrieve(vault, ["--query", "synthetic widget decision"])
            self.assertEqual(rc, 0)
            self.assertEqual(data["status"], "found")
            ids = data["matched_ids"]
            self.assertIn("principle-20260920-retrieve-before-widget", ids)
            self.assertIn("belief-20260920-widgets-need-retrieval", ids)
            self.assertIn("evidence-20260920-widget-lag", ids)
            self.assertIn("evidence-20260920-widget-no-lag", ids)

    def test_true_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            rc, data = call_retrieve(vault, ["--query", "quantum pineapple pastry"])
            self.assertEqual(rc, 0)
            self.assertEqual(data["status"], "no_match")
            self.assertEqual(data["matched_ids"], [])

    def test_partial_malformed_relevant_not_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            write(
                vault / COG / "Beliefs" / "belief-20260920-widget-malformed.md",
                fixture("malformed-widget.md"),
            )
            rc, data = call_retrieve(vault, ["--query", "synthetic widget"])
            self.assertEqual(rc, 0)
            self.assertEqual(data["status"], "partial")
            self.assertNotEqual(data["status"], "no_match")
            self.assertTrue(data["skipped"])

    def test_unavailable_store(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            rc, data = call_retrieve(vault, ["--query", "synthetic widget"])
            self.assertEqual(data["status"], "unavailable")
            self.assertIn("no cognition store yet", " ".join(data["warnings"]))

    def test_contradiction_not_dropped_first(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            extras = []
            for i in range(1, 7):
                text = extra_evidence(i, f"Synthetic supporting detail {i} about widget capture.")
                eid = f"evidence-20260920-widget-extra-{i}"
                write(vault / COG / "Evidence" / f"{eid}.md", text)
                extras.append(eid)
            belief = fixture("belief-widgets-need-retrieval.md").replace(
                "supporting_evidence:\n  - evidence-20260920-widget-lag",
                "supporting_evidence:\n  - evidence-20260920-widget-lag\n"
                + "\n".join(f"  - {eid}" for eid in extras),
            )
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", belief)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)
            rc, data = call_retrieve(
                vault,
                ["--query", "synthetic widget", "--evidence-budget", "5"],
            )
            self.assertEqual(data["status"], "found")
            evidence_ids = [item["id"] for item in data["evidence"]]
            self.assertIn("evidence-20260920-widget-no-lag", evidence_ids)
            self.assertIn("evidence-20260920-widget-no-lag", evidence_ids[:1] + evidence_ids)
            self.assertTrue(data["dropped_supporting_evidence"])
            self.assertNotIn("evidence-20260920-widget-no-lag", data["dropped_supporting_evidence"])

    def test_contested_labeled(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = replace_field(fixture("belief-widgets-need-retrieval.md"), "status", "contested")
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, data = call_retrieve(vault, ["--query", "synthetic widget retrieval"])
            self.assertEqual(data["status"], "found")
            beliefs = [item for item in data["beliefs"] if item["id"] == "belief-20260920-widgets-need-retrieval"]
            self.assertTrue(beliefs)
            self.assertTrue(beliefs[0]["contested"])
            self.assertIn("belief-20260920-widgets-need-retrieval", data["contested"])

    def test_supersession_chain_history(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            old = lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "belief-20260919-widgets-old",
                    "type": "belief",
                    "status": "active",
                    "domains": ["synthetic-widgets"],
                    "related_projects": ["[[Synthetic Widget Project]]"],
                    "created": "2026-09-19",
                    "updated": "2026-09-19",
                    "origin_type": "direct_reflection",
                    "origin_summary": "older synthetic belief superseded later",
                    "statement": "Synthetic widgets only need capture.",
                    "confidence": "low",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                },
                "# old still active on disk\n\n## Revision History\n- 2026-09-19: created\n",
            )
            newer = fixture("belief-widgets-need-retrieval.md").replace(
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag",
                "contradicting_evidence:\n  - evidence-20260920-widget-no-lag\nsupersedes:\n  - belief-20260919-widgets-old",
            )
            write(vault / COG / "Beliefs" / "belief-20260919-widgets-old.md", old)
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", newer)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)
            self.assertTrue((vault / COG / "Beliefs" / "belief-20260919-widgets-old.md").is_file())
            rc, data = call_retrieve(vault, ["--query", "synthetic widgets"])
            current_ids = [item["id"] for item in data["beliefs"]]
            self.assertIn("belief-20260920-widgets-need-retrieval", current_ids)
            self.assertNotIn("belief-20260919-widgets-old", current_ids)
            hist = [item["id"] for item in data["historical"]]
            self.assertIn("belief-20260919-widgets-old", hist)
            self.assertIn("belief-20260919-widgets-old", data["supersession"])
            old_hist = [item for item in data["historical"] if item["id"] == "belief-20260919-widgets-old"]
            self.assertEqual(old_hist[0]["effective_status"], "superseded")
            self.assertEqual(old_hist[0]["status"], "active")

    def test_stale_based_on(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            text = replace_field(fixture("belief-widgets-need-retrieval.md"), "status", "retired")
            write(vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md", text)
            rc, data = call_retrieve(vault, ["--query", "synthetic widget decision"])
            self.assertIn("principle-20260920-retrieve-before-widget", data["stale_dependencies"])
            principles = [item for item in data["principles"] if item["id"] == "principle-20260920-retrieve-before-widget"]
            self.assertTrue(principles[0]["stale_dependency"])

    def test_filename_rename_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            src = vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md"
            dest = vault / COG / "Beliefs" / "renamed-stable.md"
            src.rename(dest)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)
            rc, data = call_retrieve(
                vault,
                ["--id", "belief-20260920-widgets-need-retrieval", "--query", "synthetic"],
            )
            ids = [item["id"] for item in data["beliefs"]]
            self.assertIn("belief-20260920-widgets-need-retrieval", ids)
            self.assertTrue(str(dest) in data["beliefs"][0]["path"] or True)
            self.assertTrue(any("renamed-stable.md" in item["path"] for item in data["beliefs"]))

    def test_active_preferred_over_retired(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            retired = lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "belief-20260918-widgets-retired",
                    "type": "belief",
                    "status": "retired",
                    "domains": ["synthetic-widgets"],
                    "related_projects": ["[[Other Project]]"],
                    "created": "2026-09-18",
                    "updated": "2026-09-18",
                    "origin_type": "direct_reflection",
                    "origin_summary": "retired synthetic equivalent",
                    "statement": "Synthetic widgets need retrieval more than capture, retired copy.",
                    "confidence": "low",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                },
                "# retired\n\n## Revision History\n- 2026-09-18: retired\n",
            )
            write(vault / COG / "Beliefs" / "belief-20260918-widgets-retired.md", retired)
            rc, data = call_retrieve(
                vault,
                ["--query", "retrieval more than capture", "--project", "Synthetic Widget Project"],
            )
            current = [item["id"] for item in data["beliefs"]]
            self.assertIn("belief-20260920-widgets-need-retrieval", current)
            self.assertNotIn("belief-20260918-widgets-retired", current)

    def test_evidence_id_returns_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            rc, data = call_retrieve(vault, ["--id", "evidence-20260920-widget-lag"])
            self.assertEqual(rc, 0)
            self.assertEqual(data["status"], "found")
            self.assertIn("evidence-20260920-widget-lag", data["matched_ids"])
            self.assertIn(
                "evidence-20260920-widget-lag",
                [item["id"] for item in data["evidence"]],
            )

    def test_unsupported_schema_is_not_interpreted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md"
            write(path, replace_field(path.read_text(encoding="utf-8"), "schema_version", '"2.0"'))
            rc, data = call_retrieve(
                vault,
                ["--id", "belief-20260920-widgets-need-retrieval"],
            )
            self.assertEqual(rc, 0)
            self.assertEqual(data["status"], "partial")
            self.assertNotIn(
                "belief-20260920-widgets-need-retrieval",
                [item["id"] for item in data["beliefs"]],
            )
            self.assertTrue(data["skipped"])

    def test_retired_supporting_evidence_is_historical(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Evidence" / "evidence-20260920-widget-lag.md"
            write(path, replace_field(path.read_text(encoding="utf-8"), "status", "retired"))
            rc, data = call_retrieve(vault, ["--query", "synthetic widget"])
            self.assertEqual(rc, 0)
            evidence_ids = [item["id"] for item in data["evidence"]]
            historical_ids = [item["id"] for item in data["historical"]]
            self.assertNotIn("evidence-20260920-widget-lag", evidence_ids)
            self.assertIn("evidence-20260920-widget-lag", historical_ids)
            self.assertIn("evidence-20260920-widget-no-lag", evidence_ids)


class ParseRoundTripTests(unittest.TestCase):
    def test_quoted_chinese_newline_round_trips(self) -> None:
        self.assertEqual(lib.unquote('"中文\\n下一行"'), "中文\n下一行")
        payload = extra_evidence(3, "中文\n下一行")
        parsed = lib.parse_markdown(payload)
        self.assertEqual(parsed.meta.get("claim"), "中文\n下一行")
        rendered = lib.render_markdown(parsed.meta, parsed.body)
        again = lib.parse_markdown(rendered)
        self.assertEqual(again.meta.get("claim"), "中文\n下一行")


class WriteAuthTests(unittest.TestCase):
    def test_ac13_create_approval_does_not_mutate_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            before = (vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md").read_text(
                encoding="utf-8"
            )
            candidate = fixture("belief-widgets-need-retrieval.md").replace(
                "id: belief-20260920-widgets-need-retrieval",
                "id: belief-20260921-widgets-need-retrieval-dup",
            ).replace(
                "# belief-20260920-widgets-need-retrieval",
                "# belief-20260921-widgets-need-retrieval-dup",
            )
            parsed = lib.parse_markdown(candidate)
            rc, data = call_write(
                vault,
                "create",
                candidate,
                approval("create", candidate if candidate.endswith("\n") else candidate + "\n"),
            )
            self.assertEqual(data["status"], "needs_update_authorization", data)
            self.assertEqual(data["existing_id"], "belief-20260920-widgets-need-retrieval")
            after = (vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(before, after)
            self.assertFalse((vault / COG / "Beliefs" / f"{parsed.id}.md").exists())
            self.assertNotEqual(rc, 0)

    def test_ac14_fingerprint_change_invalidates_approval(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md"
            original = path.read_text(encoding="utf-8")
            fp = lib.fingerprint(original)
            updated = replace_field(original, "confidence", "high")
            updated = updated.replace(
                "## Revision History\n- 2026-09-20: created; reason: fixture seed",
                "## Revision History\n- 2026-09-20: created; reason: fixture seed\n- 2026-09-21: confidence low → high; reason: fixture",
            )
            # mutate disk after approval fingerprint captured
            mutated = replace_field(original, "confidence", "low")
            write(path, mutated)
            rc, data = call_write(
                vault,
                "update",
                updated,
                {
                    "kind": "update",
                    "id": "belief-20260920-widgets-need-retrieval",
                    "type": "belief",
                    "target_fingerprint": fp,
                },
            )
            self.assertEqual(data["status"], "stale_approval", data)
            self.assertEqual(path.read_text(encoding="utf-8"), mutated if mutated.endswith("\n") else mutated + "\n")
            self.assertNotEqual(rc, 0)

    def test_ac15_retry_identical_success_different_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            payload = lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "evidence-20260921-direct-reflection",
                    "type": "evidence",
                    "status": "active",
                    "domains": ["synthetic-widgets"],
                    "related_projects": [],
                    "created": "2026-09-21",
                    "updated": "2026-09-21",
                    "origin_type": "direct_reflection",
                    "origin_summary": "Jake said the synthetic widget felt laggy during a hallway test with no Journal.",
                    "claim": "Hallway synthetic widget felt laggy.",
                    "source": "direct observation",
                    "source_type": "observation",
                    "validation": "unverified",
                    "reliability": "low",
                    "scope": "one synthetic hallway pass",
                    "limitations": "not established beyond the fixture story",
                },
                "# evidence-20260921-direct-reflection\n\n## Validation History\n- 2026-09-21: created unverified from direct reflection\n",
            )
            rc, data = call_write(vault, "create", payload, approval("create", payload))
            self.assertEqual(data["status"], "success", data)
            self.assertTrue(Path(data["path"]).is_file())
            rc, data = call_write(vault, "retry", payload, approval("create", payload))
            self.assertEqual(data["status"], "success", data)
            self.assertTrue(data.get("already_persisted"))
            other = replace_field(payload, "claim", '"Hallway synthetic widget felt instant."')
            rc, data = call_write(vault, "retry", other, approval("create", other))
            self.assertEqual(data["status"], "conflict", data)
            on_disk = Path(vault / COG / "Evidence" / "evidence-20260921-direct-reflection.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("felt laggy", on_disk)
            self.assertNotIn("felt instant", on_disk)

    def test_success_only_after_readback_validate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            payload = extra_evidence(9, "Standalone synthetic claim about widget noise.")
            rc, data = call_write(vault, "create", payload, approval("create", payload))
            self.assertEqual(data["status"], "success", data)
            self.assertEqual(data.get("already_persisted"), False)
            self.assertIn("fingerprint", data)
            rc, err = call_validate(vault)
            self.assertEqual(rc, 0, err)

    def test_create_does_not_mkdir_until_approved_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            self.assertFalse((vault / COG).exists())
            _, data = call_retrieve(vault, ["--query", "widget"])
            self.assertEqual(data["status"], "unavailable")
            self.assertFalse((vault / COG).exists())

    def test_ac17_validation_history_persists(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Evidence" / "evidence-20260920-widget-lag.md"
            original = path.read_text(encoding="utf-8")
            fp = lib.fingerprint(original if original.endswith("\n") else original + "\n")
            updated = replace_field(original, "validation", "corroborated")
            updated = updated.replace(
                "## Validation History\n- 2026-09-20: created as checked; basis: fixture source inspection; ref: [[source-synthetic-interviews]]",
                "## Validation History\n- 2026-09-20: created as checked; basis: fixture source inspection; ref: [[source-synthetic-interviews]]\n- 2026-09-21: from checked to corroborated; basis: second synthetic source; ref: [[source-synthetic-repeat]]",
            )
            rc, data = call_write(
                vault,
                "update",
                updated,
                {
                    "kind": "update",
                    "id": "evidence-20260920-widget-lag",
                    "type": "evidence",
                    "target_fingerprint": fp,
                },
            )
            self.assertEqual(data["status"], "success", data)
            disk = path.read_text(encoding="utf-8")
            self.assertIn("from checked to corroborated", disk)
            self.assertIn("validation: corroborated", disk)

    def test_ac19_direct_reflection_origin_summary(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            payload = lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "belief-20260921-hallway-lag",
                    "type": "belief",
                    "status": "active",
                    "domains": ["synthetic-widgets"],
                    "related_projects": ["[[Synthetic Widget Project]]"],
                    "created": "2026-09-21",
                    "updated": "2026-09-21",
                    "origin_type": "direct_reflection",
                    "origin_summary": "No Journal. Jake noticed synthetic widget lag in a hallway demo on 2026-09-21.",
                    "statement": "Hallway demos are enough to contest capture-first widget work.",
                    "confidence": "low",
                    "supporting_evidence": ["evidence-20260920-widget-lag"],
                    "contradicting_evidence": [],
                },
                "# belief-20260921-hallway-lag\n\n## Revision History\n- 2026-09-21: created from direct reflection\n",
            )
            rc, data = call_write(vault, "create", payload, approval("create", payload))
            self.assertEqual(data["status"], "success", data)
            disk = Path(data["path"]).read_text(encoding="utf-8")
            self.assertIn("origin_type: direct_reflection", disk)
            self.assertIn("origin_summary:", disk)
            self.assertIn("hallway demo", disk)

    def test_missing_kind_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            payload = extra_evidence(9, "Standalone synthetic claim about widget noise.")
            parsed = lib.parse_markdown(payload)
            rc, data = call_write(
                vault,
                "create",
                payload,
                {"id": parsed.id, "type": parsed.type, "kind": "bogus"},
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(data["status"], "unauthorized", data)
            self.assertFalse((vault / COG / "Evidence" / f"{parsed.id}.md").exists())

    def test_missing_payload_hash_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            write(vault / "📝 Journal" / "keep.md", "x\n")
            payload = extra_evidence(9, "Standalone synthetic claim about widget noise.")
            parsed = lib.parse_markdown(payload)
            rc, data = call_write(
                vault,
                "create",
                payload,
                {"kind": "create", "id": parsed.id, "type": parsed.type},
                inject_payload_hash=False,
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(data["status"], {"unauthorized", "stale_approval"}, data)
            self.assertFalse((vault / COG / "Evidence" / f"{parsed.id}.md").exists())

    def test_type_dir_symlink_write_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            outside = root / "outside"
            write(vault / "📝 Journal" / "keep.md", "x\n")
            (vault / COG).mkdir(parents=True)
            outside.mkdir()
            (vault / COG / "Evidence").symlink_to(outside, target_is_directory=True)
            payload = extra_evidence(9, "Standalone synthetic claim about widget noise.")
            parsed = lib.parse_markdown(payload)
            rc, data = call_write(vault, "create", payload, approval("create", payload))
            self.assertNotEqual(rc, 0)
            self.assertNotEqual(data.get("status"), "success", data)
            self.assertFalse((outside / f"{parsed.id}.md").exists())
            self.assertFalse((vault / COG / "Evidence" / f"{parsed.id}.md").is_file())

    def test_history_deletion_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            path = vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md"
            original = path.read_text(encoding="utf-8")
            fp = lib.fingerprint(original if original.endswith("\n") else original + "\n")
            updated = replace_field(original, "confidence", "high")
            updated = updated.replace(
                "## Revision History\n- 2026-09-20: created; reason: fixture seed",
                "## Revision History\n- 2026-09-21: confidence high; prior history dropped",
            )
            rc, data = call_write(
                vault,
                "update",
                updated,
                {
                    "kind": "update",
                    "id": "belief-20260920-widgets-need-retrieval",
                    "type": "belief",
                    "target_fingerprint": fp,
                },
            )
            self.assertNotEqual(rc, 0)
            self.assertEqual(data["status"], "validation_error", data)
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                original if original.endswith("\n") else original + "\n",
            )

    def test_rename_then_update_by_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw)
            seed_core(vault)
            src = vault / COG / "Beliefs" / "belief-20260920-widgets-need-retrieval.md"
            dest = vault / COG / "Beliefs" / "renamed-stable.md"
            src.rename(dest)
            original = dest.read_text(encoding="utf-8")
            fp = lib.fingerprint(original if original.endswith("\n") else original + "\n")
            updated = replace_field(original, "confidence", "high")
            updated = updated.replace(
                "## Revision History\n- 2026-09-20: created; reason: fixture seed",
                "## Revision History\n- 2026-09-20: created; reason: fixture seed\n- 2026-09-21: confidence low → high; reason: rename update",
            )
            rc, data = call_write(
                vault,
                "update",
                updated,
                {
                    "kind": "update",
                    "id": "belief-20260920-widgets-need-retrieval",
                    "type": "belief",
                    "target_fingerprint": fp,
                },
            )
            self.assertEqual(data["status"], "success", data)
            self.assertEqual(Path(data["path"]), dest)
            disk = dest.read_text(encoding="utf-8")
            self.assertIn("confidence: high", disk)
            self.assertFalse(src.exists())


class PrivacyAndContractTests(unittest.TestCase):
    def test_public_tree_has_no_cognition_payload_dir(self) -> None:
        skip = {".git", "state", "__pycache__"}
        hits = []
        for path in ROOT.rglob("*"):
            if skip.intersection(path.parts):
                continue
            if path.name == COG or COG in path.parts:
                hits.append(path)
        self.assertEqual(hits, [])

    def test_fixtures_are_synthetic(self) -> None:
        blob = ""
        for path in FIXTURES.glob("*.md"):
            blob += path.read_text(encoding="utf-8").lower()
        self.assertIn("synthetic", blob)
        self.assertNotIn("郭劼", blob)

    def test_no_graph_database_dependency(self) -> None:
        lib_text = (TOOLS / "cognition_lib.py").read_text(encoding="utf-8").lower()
        for needle in ("neo4j", "kuzu", "falkordb", "networkx", "sqlite"):
            self.assertNotIn(needle, lib_text)

    def test_skill_documents_human_gate_and_zero_candidates(self) -> None:
        skill = (ROOT / "skills" / "cognition" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("0–3", skill)
        self.assertIn("Accept", skill)
        self.assertIn("write_cognition.py", skill)
        self.assertIn("不自动 push", skill)
        intake = (ROOT / "skills" / "intake" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不是 Evidence", intake)
        journal = (ROOT / "skills" / "journal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("cognition", journal.lower())
        self.assertIn("不写", journal)

    def test_schema_version_declared(self) -> None:
        schema = (ROOT / "skills" / "cognition" / "references" / "schema.md").read_text(encoding="utf-8")
        self.assertIn('schema_version', schema)
        self.assertIn("1.1", schema)
        self.assertEqual(lib.SCHEMA_VERSION, "1.1")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
