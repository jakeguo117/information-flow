#!/usr/bin/env python3
"""AC12: synthetic content trace. No vault and no network."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_content  # noqa: E402

TOOL = Path(__file__).resolve().parent / "trace_content.py"
SPEC_FINGERPRINT = "fdb72bfb9f4bd951a2680766aa646d7c1b30c18cec519efda4347804171d996c"
AUDIENCE = "合成受众问题，离开原笔记也能懂。"
V2_BODY = "合成 X 正文，第二版。"
V3_BODY = "合成 X 正文，第三版，还没再批。"


def sha1_12(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def source_id(platform: str, url: str) -> str:
    """inbox-0.1 source id when there is no platform content id."""
    return f"src-{platform}-u{sha1_12(url)}"


def input_id(platform: str, source: str, event_key: str) -> str:
    """inbox-0.1 input id: in-{platform}-{sha1(source_id + '|' + event_key)[:12]}."""
    return f"in-{platform}-{sha1_12(source + '|' + event_key)}"


def idea_id(source_ref: str, expression: str) -> str:
    return f"idea-{sha1_12(source_ref + '|' + expression)}"


def fact_id(source_ref: str, statement: str) -> str:
    return f"fact-{sha1_12(source_ref + '|' + statement)}"


def content_id(first_ref: str, audience: str) -> str:
    return f"content-{sha1_12(first_ref + '|' + audience)}"


def _material(platform: str, url: str, event_key: str) -> tuple[str, str, str]:
    source = source_id(platform, url)
    item = input_id(platform, source, event_key)
    return source, item, f"input:{item}"


SOURCE_1, INPUT_1, IDEA1_REF = _material(
    "manual", "https://example.com/synthetic-source-1", "synthetic-event-1"
)
SOURCE_2, INPUT_2, IDEA2_REF = _material(
    "weread", "https://example.com/synthetic-source-2", "synthetic-highlight-2"
)
SOURCE_3, INPUT_3, FACT_REF = _material(
    "x", "https://example.com/synthetic-source-3", "synthetic-post-3"
)
IDEA1_EXPR = "合成想法一，离开原笔记也能懂。"
IDEA2_EXPR = "合成想法二，离开原笔记也能懂。"
FACT_STATEMENT = "合成事实，关键词是南瓜。"
IDEA_1 = idea_id(IDEA1_REF, IDEA1_EXPR)
IDEA_2 = idea_id(IDEA2_REF, IDEA2_EXPR)
FACT_1 = fact_id(FACT_REF, FACT_STATEMENT)
CONTENT_REFS = [f"idea:{IDEA_1}", f"idea:{IDEA_2}", f"fact:{FACT_1}"]
CONTENT_1 = content_id(CONTENT_REFS[0], AUDIENCE)


def channels(x_body: str, cards: list[str] | None = None) -> dict:
    return {
        "x": {"body": x_body},
        "xiaohongshu": {
            "caption": "合成短文案。",
            "cards": ["1/1 合成卡片。"] if cards is None else cards,
        },
        "wechat_mp": {
            "title": "合成标题",
            "summary": "合成摘要",
            "cover_note": "封面：合成说明，无真人。",
            "body": "合成公众号正文。",
            "sources_note": "出处：https://example.com/synthetic 2026-10-20",
        },
    }


def example_content() -> dict:
    """The fingerprint example in content-record.md. Synthetic, not a note."""
    return {
        "schema_version": "content-0.1",
        "content_id": "content-1729bdab9586",
        "revision": 1,
        "channels": channels("合成 X 正文。"),
    }


def graph() -> dict:
    """Two Ideas and one Fact. Their refs are Inputs; each Input names a Source."""
    return {
        "ideas": [
            {
                "schema_version": "ideas-0.1",
                "idea_id": IDEA_1,
                "type": "idea",
                "expression": IDEA1_EXPR,
                "source_refs": [IDEA1_REF],
            },
            {
                "schema_version": "ideas-0.1",
                "idea_id": IDEA_2,
                "type": "idea",
                "expression": IDEA2_EXPR,
                "source_refs": [IDEA2_REF],
            },
        ],
        "facts": [
            {
                "schema_version": "facts-0.1",
                "fact_id": FACT_1,
                "statement": FACT_STATEMENT,
                "source_refs": [FACT_REF],
            }
        ],
        "inputs": [
            {"schema_version": "inbox-0.1", "input_id": INPUT_1, "source_id": SOURCE_1},
            {"schema_version": "inbox-0.1", "input_id": INPUT_2, "source_id": SOURCE_2},
            {"schema_version": "inbox-0.1", "input_id": INPUT_3, "source_id": SOURCE_3},
        ],
    }


def approval_for(content: dict, *, at: str = "2026-10-21T10:00:00+08:00") -> dict:
    return {
        "by": "jake",
        "phrase": "批",
        "revision": content["revision"],
        "body_sha256": content["body_sha256"],
        "channels": ["x", "xiaohongshu", "wechat_mp"],
        "at": at,
    }


def draft(revision: int, x_body: str) -> dict:
    content = {
        "schema_version": "content-0.1",
        "content_id": CONTENT_1,
        "type": "content",
        "revision": revision,
        "origin": "jake",
        "stage": "draft",
        "source_refs": list(CONTENT_REFS),
        "audience_problem": AUDIENCE,
        "channels": channels(x_body),
    }
    content["body_sha256"] = trace_content.body_sha256(content)
    return content


class ContentTraceTests(unittest.TestCase):
    def test_spec_fingerprint_matches_content_record_example(self) -> None:
        self.assertEqual(trace_content.body_sha256(example_content()), SPEC_FINGERPRINT)

    def test_card_pages_are_joined_with_newline(self) -> None:
        content = example_content()
        content["channels"]["xiaohongshu"]["cards"] = ["1/2 合成卡片。", "2/2 合成卡片。"]
        payload = {
            "schema_version": "content-0.1",
            "content_id": "content-1729bdab9586",
            "revision": 1,
            "x_body": "合成 X 正文。",
            "xhs_caption": "合成短文案。",
            "xhs_cards": "1/2 合成卡片。\n2/2 合成卡片。",
            "wechat_title": "合成标题",
            "wechat_summary": "合成摘要",
            "wechat_cover_note": "封面：合成说明，无真人。",
            "wechat_body": "合成公众号正文。",
            "wechat_sources": "出处：https://example.com/synthetic 2026-10-20",
        }
        expected = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        self.assertEqual(trace_content.body_sha256(content), expected)

    def test_ac12_approved_v2_draft_v3_refuses_and_still_traces(self) -> None:
        approved = draft(2, V2_BODY)
        approved["approval"] = approval_for(approved)
        current = draft(3, V3_BODY)
        current["approval"] = approval_for(approved)
        current["stage"] = "published"
        current["publish_result"] = {
            "state": "published",
            "by": "jake",
            "notes": "合成确认，不是真的发出。",
        }

        traced = trace_content.trace_content(current, graph())
        self.assertTrue(traced["ok"])
        self.assertEqual(traced["content_id"], CONTENT_1)
        self.assertEqual(traced["revision"], 3)
        self.assertEqual(traced["idea_ids"], [IDEA_1, IDEA_2])
        self.assertEqual(traced["fact_ids"], [FACT_1])
        self.assertEqual(traced["input_ids"], [INPUT_1, INPUT_2, INPUT_3])
        self.assertEqual(traced["source_ids"], [SOURCE_1, SOURCE_2, SOURCE_3])
        self.assertEqual(traced["unresolved"], [])
        for cited in CONTENT_REFS:
            self.assertNotIn(INPUT_1, cited)
            self.assertNotIn(SOURCE_1, cited)
        self.assertNotEqual(
            traced["approval"]["current_body_sha256"],
            traced["approval"]["approved_body_sha256"],
        )

        approval = traced["approval"]
        self.assertFalse(approval["covers_current"])
        self.assertFalse(approval["publishable"])
        self.assertTrue(approval["new_approval_required"])
        self.assertEqual(approval["approved_revision"], 2)
        self.assertEqual(approval["current_revision"], 3)
        self.assertIn("approved revision 2 does not cover draft revision 3", approval["reason"])
        self.assertIn("body_sha256 does not match the approved fingerprint", approval["reason"])
        self.assertIn("a new approval is required", approval["reason"])

        covered = trace_content.trace_content(approved, graph())
        self.assertTrue(covered["approval"]["publishable"])
        self.assertEqual(covered["input_ids"], traced["input_ids"])
        self.assertEqual(covered["source_ids"], traced["source_ids"])

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            content_path = root / "content.json"
            graph_path = root / "graph.json"
            content_path.write_text(json.dumps(current), encoding="utf-8")
            graph_path.write_text(json.dumps(graph()), encoding="utf-8")
            refused = self.invoke(content_path, graph_path, require_approval=True)
            self.assertEqual(refused.returncode, 1, refused.stderr)
            payload = json.loads(refused.stdout)
            self.assertEqual(payload["input_ids"], [INPUT_1, INPUT_2, INPUT_3])
            self.assertEqual(payload["source_ids"], [SOURCE_1, SOURCE_2, SOURCE_3])
            self.assertFalse(payload["approval"]["publishable"])
            self.assertIn("a new approval is required", payload["approval"]["reason"])

            still_traces = self.invoke(content_path, graph_path, require_approval=False)
            self.assertEqual(still_traces.returncode, 0, still_traces.stderr)
            self.assertFalse(json.loads(still_traces.stdout)["approval"]["publishable"])

            approved_path = root / "approved.json"
            approved_path.write_text(json.dumps(approved), encoding="utf-8")
            accepted = self.invoke(approved_path, graph_path, require_approval=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertTrue(json.loads(accepted.stdout)["approval"]["publishable"])

    def test_same_revision_different_body_requires_new_approval(self) -> None:
        approved = draft(2, V2_BODY)
        approved["approval"] = approval_for(approved)
        edited = draft(2, V3_BODY)
        edited["approval"] = approval_for(approved)
        result = trace_content.assess_approval(edited)
        self.assertEqual(result["approved_revision"], 2)
        self.assertEqual(result["current_revision"], 2)
        self.assertFalse(result["publishable"])
        self.assertTrue(result["new_approval_required"])
        self.assertIn("body_sha256 does not match the approved fingerprint", result["reason"])
        self.assertIn("a new approval is required", result["reason"])
        self.assertNotIn("does not cover draft revision", result["reason"])

    def test_wrong_phrase_is_not_approval(self) -> None:
        approved = draft(2, V2_BODY)
        approved["approval"] = approval_for(approved)
        approved["approval"]["phrase"] = "批准"
        result = trace_content.assess_approval(approved)
        self.assertFalse(result["publishable"])
        self.assertIn("approval is not Jake's 批", result["reason"])
        self.assertIn("a new approval is required", result["reason"])

    def invoke(self, content_path: Path, graph_path: Path, *, require_approval: bool) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(TOOL),
            "--content",
            str(content_path),
            "--graph",
            str(graph_path),
        ]
        if require_approval:
            command.append("--require-approval")
        return subprocess.run(command, check=False, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
